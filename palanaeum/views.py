import logging
import time
from collections import defaultdict
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from palanaeum.configuration import get_config
from palanaeum.decorators import json_response, AjaxException
from palanaeum.forms import UserCreationFormWithEmail, UserSettingsForm, \
    EmailChangeForm, SortForm, UsersEntryCollectionForm
from palanaeum.models import UserSettings, Event, \
    AudioSource, Entry, Tag, ImageSource, RelatedSite, UsersEntryCollection
from palanaeum.search import init_filters, execute_filters, get_search_results, \
    paginate_search_results
from palanaeum.utils import is_contributor


def index(request):
    """
    Draw the home page.
    """
    page_length = UserSettings.get_page_length(request)
    newest_events = Event.all_visible.exclude(entries=None).prefetch_related('entries', 'tags')[:page_length]
    events_count = Event.all_visible.filter().count()
    entries_count = Entry.all_visible.filter().count()
    audio_sources_count = AudioSource.all_visible.filter().count()

    new_sources = []
    new_sources.extend(AudioSource.all_visible.order_by('-created_date')[:5])
    new_sources.extend(ImageSource.all_visible.order_by('-created_date')[:5])
    new_sources.sort(key=lambda source: source.created_date or
                                        timezone.datetime(1900, 1, 1, tzinfo=timezone.get_current_timezone()),
                     reverse=True)
    new_sources = new_sources[:5]

    related_sites = RelatedSite.objects.all()

    welcome_text = get_config('index_hello')

    return render(request, 'palanaeum/index.html', {'newest_events': newest_events, 'events_count': events_count,
                                                    'entries_count': entries_count, 'audio_sources_count': audio_sources_count,
                                                    'new_sources': new_sources, 'related_sites': related_sites,
                                                    'welcome_text': welcome_text})


def events(request):
    """
    Display a list of events that are present in the system.
    """
    all_events = Event.all_visible.all()

    sort_form = SortForm((('name', _('name')), ('date', _('date'))), request.GET,
                         initial={'sort_by': 'date', 'sort_ord': '-'})

    if sort_form.is_valid():
        sort_by = sort_form.cleaned_data['sort_by']
        sort_ord = sort_form.cleaned_data['sort_ord']
        all_events.order_by('{}{}'.format(sort_ord, sort_by), 'name')

    page_length = UserSettings.get_page_length(request)
    paginator = Paginator(all_events, page_length, orphans=page_length // 10)

    page_num = request.GET.get('page', '1')

    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return render(request, 'palanaeum/events_list.html', {'paginator': paginator, 'page': page})


def event_no_slug(request, event_id):
    """
    Redirect to a version with slug in URL.
    """
    event = get_object_or_404(Event, pk=event_id)
    return redirect('view_event', event_id, slugify(event.name))


def view_entry(request, entry_id):
    """
    Redirect user to proper event and entry.
    """
    entry = get_object_or_404(Entry, pk=entry_id)
    return redirect(reverse('view_event', args=(entry.event_id, slugify(entry.event.name))) + '#e{}'.format(entry.id))


def view_event(request, event_id):
    """
    Display single Event page.
    """
    event = get_object_or_404(Event, pk=event_id)

    if not event.visible():
        raise PermissionDenied

    entry_ids = Entry.all_visible.filter(event=event).values_list('id', flat=True)
    entries_map = Entry.prefetch_entries(entry_ids, show_unapproved=is_contributor(request))

    entries = sorted(entries_map.values(), key=lambda e: e.order)
    sources = list(event.sources_iterator())

    approval_msg = get_config('approval_message')
    if event.review_state == Event.REVIEW_APPROVED:
        approval_explanation = get_config('review_reviewed_explanation')
    elif event.review_state == Event.REVIEW_PENDING:
        approval_explanation = get_config('review_pending_explanation')
    else:
        approval_explanation = ''

    return render(request, 'palanaeum/event.html', {'event': event, 'entries': entries, 'sources': sources,
                                                    'approval_msg': approval_msg,
                                                    'review_message': approval_explanation})


def password_reset_complete(request):
    """
    Write a message about success and redirect user to login page.
    """
    messages.success(request, _('Your password has been set. You may go ahead and log in now.'))
    logging.getLogger('palanaeum.auth').info("User %s has requested password reset.", request.user)
    return redirect('auth_login')


def password_change_complete(request):
    """
    Write a message about success and redirect user to login page.
    """
    messages.success(request, _('Your password has been changed.'))
    logging.getLogger('palanaeum.auth').info("User %s has changed their password.", request.user)
    return redirect('auth_settings')


def register_user(request):
    """
    Display a registration form. If it's a POST request, create a new user.
    """
    if request.method == 'POST':
        form = UserCreationFormWithEmail(request.POST)
        if form.is_valid():
            new_user = form.save(commit=True)
            settings = UserSettings.objects.create(user=new_user)
            settings.page_length = get_config('default_page_length')
            settings.save()
            # We're not gonna play with e-mail confirmation and activation for now.
            messages.success(request, _('Congratulations! You have created a new account. '
                                        'You can sign in using your credentials.'))
            logging.getLogger('palanaeum.auth').info("User %s has registered.", request.user)
            return redirect('auth_login')
    else:
        form = UserCreationFormWithEmail()

    return render(request, 'palanaeum/auth/register.html', {'form': form})


@login_required(login_url='auth_login')
def user_settings(request):
    """
    Display user control panel.
    """
    settings_obj = UserSettings.objects.get(user=request.user)

    if request.method == 'POST':
        email_form = EmailChangeForm(request.POST, user=request.user)
        settings_form = UserSettingsForm(request.POST, instance=settings_obj)
        if settings_form.is_valid() and email_form.is_valid():
            email_form.save()
            settings_obj = settings_form.save()
            request.session['page_length'] = settings_obj.page_length
            messages.success(request, _('Settings have been saved.'))
            return redirect('auth_settings')
    else:
        email_form = EmailChangeForm(initial={'email': request.user.email}, user=request.user)
        settings_form = UserSettingsForm(instance=settings_obj)

    return render(request, 'palanaeum/auth/settings.html', {'settings_form': settings_form, 'email_form': email_form})


@login_required(login_url='auth_login')
def show_collection_list(request):
    """
    Displays a list of user collections owned by current user.
    """
    collections = UsersEntryCollection.objects.filter(user=request.user)

    return render(request, 'palanaeum/collections/collection_list.html', {'collections': collections})


def show_collection(request, collection_id):
    """
    Check if user can view this collections and display it.
    """
    collection = get_object_or_404(UsersEntryCollection, pk=collection_id)

    if not (collection.public or collection.user == request.user or request.user.is_superuser):
        messages.error(request, _('You are not allowed to see this collection.'))
        return redirect('index')
    elif collection.user != request.user and request.user.is_superuser:
        messages.info(request, _('You are viewing a private collection as superuser.'))

    entries_ids = collection.entries.all().values_list('id', flat=True)
    entries = Entry.prefetch_entries(entries_ids)
    entries = [entries[eid] for eid in entries_ids]

    return render(request, 'palanaeum/collections/collection.html',
                  {'entries': entries, 'collection': collection,
                   'is_owner': collection.user == request.user})


@login_required(login_url='auth_login')
def edit_collection(request, collection_id=None):
    """
    Display collection edit form allowing user to edit it's name, description
    and visibility.
    """
    if collection_id:
        collection = get_object_or_404(UsersEntryCollection, pk=collection_id)

        if collection.user != request.user:
            messages.error(request, _('You are not allowed to edit this collection.'))
            return redirect('index')
    else:
        collection = UsersEntryCollection(user=request.user)

    if request.method == 'POST':
        form = UsersEntryCollectionForm(request.POST, instance=collection)
        if form.is_valid():
            form.save()
            messages.success(request, _('Collection saved successfully.'))
            return redirect('collections_list')
        messages.error(request, _('There were problems while saving your collection.'))
    else:
        form = UsersEntryCollectionForm(instance=collection)

    return render(request, 'palanaeum/collections/collection_edit.html',
                  {'form': form, 'collection': collection, 'new_collection': collection_id is None})


@login_required(login_url='auth_login')
def delete_collection(request, collection_id):
    """
    Display a page asking for confirmation that you want to delete the collection. Delete if
    it's confirmed.
    """
    collection = get_object_or_404(UsersEntryCollection, pk=collection_id)

    if collection.user != request.user and not request.user.is_superuser:
        messages.error(request, _('You are not allowed to delete this collection.'))
        return redirect('index')

    if request.method == 'POST':
        collection.delete()
        messages.success(request, _('Collection removed successfully.'))
        return redirect('collections_list')

    return render(request, 'palanaeum/collections/collection_remove_confirm.html',
                  {'collection': collection})


@json_response
@login_required(login_url='auth_login')
def get_collection_list_json(request):
    entry_id = request.GET.get('entry_id', None)

    collections = UsersEntryCollection.objects.filter(user=request.user)

    ret = []

    for collection in collections:
        ret.append({
            'id': collection.id,
            'name': collection.name if len(collection.name) < 30 else collection.name[:27] + '...',
            'size': collection.entries.count(),
            'has_entry': collection.entries.filter(pk=entry_id).exists(),
            'public': collection.public,
        })

    return {'success': True, 'list': ret}


@require_POST
@json_response
@login_required(login_url='auth_login')
def switch_entry_in_collection(request):
    try:
        entry_id = int(request.POST['entry_id'])
        entry = get_object_or_404(Entry, pk=entry_id)
        collection_id = int(request.POST['collection_id'])
        collection = get_object_or_404(UsersEntryCollection, pk=collection_id)
        action = request.POST['action']
        assert(action in ('add', 'remove'))
    except KeyError:
        raise AjaxException('Missing required POST parameter (entry_id, collection_id and action are required).')
    except (TypeError, ValueError):
        raise AjaxException('The id parameter must contain an integer.')
    except AssertionError:
        raise AjaxException('Invalid action.')

    if collection.user != request.user and not request.user.is_superuser:
        raise AjaxException('You are not allowed to do this!')

    if action == 'add':
        collection.entries.add(entry)
    else:
        collection.entries.remove(entry)

    return {'success': True, 'size': collection.entries.count(),
            'name': collection.name if len(collection.name) < 30 else collection.name[:27] + '...',
            'public': collection.public}


@require_POST
@json_response
@login_required(login_url='auth_login')
def ajax_add_collection(request):
    try:
        name = request.POST['name'][:UsersEntryCollection.MAX_NAME_LENGTH]
        entry_id = int(request.POST['entry_id'])
        entry = get_object_or_404(Entry, pk=entry_id)
    except KeyError:
        raise AjaxException('Missing required POST parameter (name and entry_id required).')
    except (TypeError, ValueError):
        raise AjaxException('The id parameter must contain an integer.')

    collection = UsersEntryCollection.objects.create(
        user=request.user, name=name, public=False
    )

    collection.entries.add(entry)

    return {'success': True, 'name': name, 'id': collection.id}


def adv_search(request):
    """
    Display an advances search form + search results.
    """
    filters = init_filters(request)

    ordering = request.GET.get('ordering', 'rank')

    search_params = [urlencode({'ordering': ordering})]
    for search_filter in filters:
        if search_filter:
            search_params.append(search_filter.as_url_param())
    search_params = "&".join(search_params)

    if any(filters):
        start_time = time.time()
        entries_scores = execute_filters(filters)

        entries, paginator, page = paginate_search_results(request, get_search_results(entries_scores, ordering))
        search_time = time.time() - start_time
    else:
        entries = []
        paginator = None
        page = None
        search_time = 0

    return render(request, 'palanaeum/search/adv_search_results.html',
                  {'paginator': paginator, 'entries': entries, 'filters': filters, 'search_done': any(filters),
                   'query': request.GET.get('query', ''), 'search_params': search_params,
                   'page': page, 'search_time': search_time, 'ordering': ordering})


@json_response
def get_tags(request):
    """
    Return a tag list suitable for select2.
    """
    query = request.GET.get('q', '')
    tags = Tag.objects.filter(
        Q(name__startswith=query) | Q(name__contains=' ' + query)
    ).annotate(entry_count=Count('entries'), event_count=Count('events'))
    return {'results': [
        {
            'id': t.name,
            'text': "{} ({})".format(t.name, t.entry_count + t.event_count)
        } for t in sorted(tags, key=lambda tag: -(tag.entry_count + tag.event_count))]}


def tags_list(request):
    """
    Show a list of tags that are used in the system.
    """
    event_tags = defaultdict(list)
    entry_tags = defaultdict(list)

    for tag in Tag.objects.exclude(entries=None).annotate(entry_count=Count('entries')):
        entry_tags[tag.entry_count].append(tag)

    for tag in Tag.objects.exclude(events=None).annotate(event_count=Count('events')):
        event_tags[tag.event_count].append(tag)

    entry_tags = sorted(entry_tags.items(), reverse=True)
    event_tags = sorted(event_tags.items(), reverse=True)

    return render(request, 'palanaeum/tags_list.html', {'entry_tags': entry_tags, 'event_tags': event_tags})


def recent_entries(request):
    """
    Show recent entries, sorted by their assigned date, modification or creation date.
    """
    date_mode = request.GET.get('mode', 'created')

    if date_mode == 'modified':
        entries = Entry.all_visible.order_by('-modified').values_list('id', flat=True)
    elif date_mode == 'recorded':
        entries = Entry.all_visible.order_by('-date', '-id').values_list('id', flat=True)
    else:  # Sort by creation date by default
        entries = Entry.all_visible.order_by('-created').values_list('id', flat=True)

    page_length = UserSettings.get_page_length(request)
    page_num = request.GET.get('page', '1')

    paginator = Paginator(entries, page_length, orphans=page_length // 10)

    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    entries_map = Entry.prefetch_entries(page, show_unapproved=is_contributor(request))
    entries = [entries_map[entry_id] for entry_id in page]

    return render(request, 'palanaeum/recent_entries.html',
                  {'paginator': paginator, 'page': page, 'entries': entries, 'mode': date_mode,
                   'page_params': 'mode={}'.format(date_mode)})

