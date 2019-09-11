# coding=utf-8
import json
import logging
import re
from collections import defaultdict
from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.validators import URLValidator
from django.db import transaction
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from lxml.html.diff import htmldiff

from palanaeum import tasks
from palanaeum.configuration import get_config
from palanaeum.decorators import json_response, AjaxException
from palanaeum.forms import EventForm, ImageRenameForm
from palanaeum.models import Event, AudioSource, Entry, Snippet, EntryLine, \
    EntryVersion, URLSource, ImageSource
from palanaeum.utils import is_contributor


@staff_member_required(login_url='auth_login')
def edit_event(request, event_id=None):
    """
    Display a form for Event creation or save the form.
    """
    if event_id is not None:
        event = get_object_or_404(Event, pk=event_id)
    else:
        event = None

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save()
            if event_id is None:
                messages.success(request, _('The {} event has been created '
                                            'successfully.').format(event.name))
                logging.getLogger('palanaeum.staff').info("%s has created event %s.", request.user,
                                                          event.id)
            else:
                messages.success(request, _('The event has been updated successfully.'))
                logging.getLogger('palanaeum.staff').info("%s has modified event %s.", request.user,
                                                          event.id)
            return redirect('view_event_no_title', event_id=event.id)
    else:
        form = EventForm(instance=event)

    return render(request, 'palanaeum/staff/event_edit_form.html',
                  {'form': form, 'new_event': event is None, 'event_id': event_id, 'event': event})


@staff_member_required(login_url='auth_login')
def remove_event(request, event_id):
    """
    Display a confirmation question, then remove the event.
    """
    event = get_object_or_404(Event, pk=event_id)

    if request.method == 'POST':
        event.delete()
        messages.success(request, _('Event has been deleted successfully.'))
        logging.getLogger('palanaeum.staff').info("%s has removed event %s.", request.user,
                                                  event.id)
        return redirect(reverse('index'))

    return render(request, 'palanaeum/staff/delete_event_confirm.html', {'event': event})


@staff_member_required(login_url='auth_login')
def remove_entry(request, entry_id):
    """
    Display a confirmation question, then remove the entry.
    """
    entry = get_object_or_404(Entry, pk=entry_id)

    if request.method == 'POST':
        entry.delete()
        messages.success(request, _('Entry has been successfully deleted.'))
        logging.getLogger('palanaeum.staff').info("%s has removed entry %s.", request.user,
                                                  entry.id)
        return redirect('view_event_no_title', entry.event_id)

    return render(request, 'palanaeum/staff/delete_entry_confirm.html', {'entry': entry})


@staff_member_required(login_url='auth_login')
def remove_audio_file(request, file_id):
    """
    Display a page asking for confirmation that the file is to be removed from the server.
    If it's confirmed then delete it.
    """
    audio_file = get_object_or_404(AudioSource, pk=file_id)

    if request.method == 'POST':
        audio_file.delete()
        messages.success(request, _('Audio file has been successfully deleted.'))
        logging.getLogger('palanaeum.staff').info("%s has removed audio file %s.", request.user,
                                                  audio_file.id)
        return redirect('view_event_no_title', event_id=audio_file.event_id)

    return render(request, 'palanaeum/staff/delete_audio_file_confirm.html',
                  {'file_id': file_id, 'file': audio_file,
                   'back': reverse('view_event_no_title', kwargs={'event_id': audio_file.event_id})})


@staff_member_required(login_url='auth_login')
def remove_image_source(request, source_id):
    """
    Display a page asking for confirmation that the file is to be removed from the server.
    Delete if confirmation is given
    """
    img_source = get_object_or_404(ImageSource, pk=source_id)

    if request.method == 'POST':
        img_source.delete()
        messages.success(request, _('Image source has been successfully deleted.'))
        logging.getLogger('palanaeum.staff').info("%s has removed image file %s.", request.user,
                                                  img_source.id)
        return redirect('view_event_no_title', event_id=img_source.event_id)

    return render(request, 'palanaeum/staff/delete_image_source_confirm.html',
                  {'source': img_source})



@require_POST
@staff_member_required(login_url='auth_login')
@json_response
def hide_show_resource(request):
    try:
        resource_class = request.POST['class']
        assert (resource_class in ('entry', 'audio_source', 'url_source', 'snippet', 'image_source'))
        resource_id = int(request.POST['id'])
        mode = request.POST['mode']
    except KeyError:
        raise AjaxException('Missing required POST parameter (class, mode and id are required).')
    except TypeError:
        raise AjaxException('The id parameter must contain an integer.')
    except AssertionError:
        raise AjaxException('Invalid class.')

    if mode not in ('show', 'hide'):
        raise AjaxException('Invalid mode.')

    if resource_class == 'entry':
        obj = get_object_or_404(Entry, pk=resource_id)
    elif resource_class == 'url_source':
        obj = get_object_or_404(URLSource, pk=resource_id)
    elif resource_class == 'audio_source':
        obj = get_object_or_404(AudioSource, pk=resource_id)
    elif resource_class == 'snippet':
        obj = get_object_or_404(Snippet, pk=resource_id)
    elif resource_class == 'image_source':
        obj = get_object_or_404(ImageSource, pk=resource_id)
    else:
        raise AjaxException("Unknown resource class.")

    if mode == 'show':
        obj.show()
        logging.getLogger('palanaeum.staff').info("%s showed %s  %s.", request.user,
                                                  resource_class, obj.id)
    else:
        obj.hide()
        logging.getLogger('palanaeum.staff').info("%s hid %s  %s.", request.user,
                                                  resource_class, obj.id)

    obj.save()
    return


@staff_member_required(login_url='auth_login')
def approve_source(request, source_type, pk):
    if source_type == 'audio':
        source = get_object_or_404(AudioSource, pk=pk)
    elif source_type == 'image':
        source = get_object_or_404(ImageSource, pk=pk)
    else:
        raise Http404

    source.approve()
    messages.success(request, "Source {} has been approved.".format(source.title))
    logging.getLogger('palanaeum.staff').info("Source %s has been approved by %s.",
                                              source.id, request.user)

    return redirect('view_event', source.event_id, slugify(source.event.name))


@staff_member_required(login_url='auth_login')
def reject_source(request, source_type, pk):
    if source_type == 'audio':
        source = get_object_or_404(AudioSource, pk=pk)
    elif source_type == 'image':
        source = get_object_or_404(ImageSource, pk=pk)
    else:
        raise Http404

    if source.is_approved:
        messages.error(request, "Source {} is already approved!".format(
            source.title
        ))
    else:
        source.delete()
        messages.success(request, "Source {} has been rejected.".format(source.title))
        logging.getLogger('palanaeum.staff').info("Source %s has been rejected by %s.",
                                                  source.id, request.user)

    return redirect('view_event', source.event_id, slugify(source.event.name))


@login_required(login_url='auth_login')
def unlink_snippet(request, snippet_id: int):
    snippet = get_object_or_404(Snippet, pk=snippet_id)
    entry_id = snippet.entry.id
    snippet.entry = None
    snippet.save()

    messages.success(request, _('Snippet has been unlinked.'))
    logging.getLogger('palanaeum.staff').info("%s unlinked snippet %s.",
                                              request.user, snippet.id)

    return redirect('edit_entry', entry_id=entry_id)


@login_required(login_url='auth_login')
def edit_audio_source(request, source_id):
    """
    Display a page for creation of Snippets.
    """
    source = get_object_or_404(AudioSource, pk=source_id)

    if not source.visible():
        raise PermissionDenied

    if source.length == 0:
        source.reset_length()
        source.save()

    snippets = Snippet.objects.filter(source=source)

    for snippet in snippets:
        snippet.foreign = not ((snippet.created_by == request.user) or request.user.is_staff)

    return render(request, 'palanaeum/staff/audio_source_edit.html', {'source': source, 'snippets': snippets})


@staff_member_required(login_url='auth_login')
@json_response
@require_POST
def rename_audio_source(request):
    """
    Rename an audio source, return JSON response.
    """
    source_id = request.POST.get('source_id')
    try:
        source = get_object_or_404(AudioSource, pk=int(source_id))
    except ValueError:
        raise AjaxException("Source_id has to be integer.")

    try:
        old_title = source.file_title
        source.file_title = request.POST['title']
    except KeyError:
        raise AjaxException("Title missing.")
    logging.getLogger('palanaeum.staff').info("%s renamed audio source %s from %s to %s.",
                                              request.user, source.id, old_title, source.file_title)
    source.save()
    return {}


@json_response
@staff_member_required(login_url='auth_login')
@require_POST
def get_new_snippet_id(request):
    """
    Get a new snippet's id and return it. Don't leave the new snippet in the database.
    """
    try:
        source_id = request.POST['source_id']
    except KeyError:
        raise AjaxException('Missing source_id parameter.')
    snippet = Snippet()
    snippet.created_by = request.user
    snippet.source_id = source_id
    snippet.save()
    snippet_id = snippet.id
    snippet.delete()
    return {'snippet_id': snippet_id}


def _process_snippets(source: AudioSource, request: HttpRequest):

    beginning_re = r'^snippet-(\d+)-beginning$'
    length_re = r'^snippet-(\d+)-length$'
    comment_re = r'^snippet-(\d+)-comment$'
    optional_re = r'^snippet-(\d+)-optional'

    snippets_by_id = {s.id: s for s in Snippet.objects.filter(source=source)}
    updated_snippets = set()
    updated_urls = {}

    for key in request.POST.keys():
        b_match = re.match(beginning_re, key)
        l_match = re.match(length_re, key)
        c_match = re.match(comment_re, key)
        t_match = re.match(optional_re, key)

        match = b_match or l_match or c_match or t_match

        if not match:
            continue

        snippet_id = int(match.group(1))

        try:
            snippet = snippets_by_id[snippet_id]
        except KeyError:
            if Snippet.objects.filter(pk=snippet_id).exists():
                raise AjaxException(_('"Snippet {} already exists and cannot be edited here.').format(snippet_id))
            snippet = Snippet()
            snippet.id = snippet_id
            snippet.created_by = request.user
            snippet.source = source
            snippets_by_id[snippet_id] = snippet

        if b_match and not snippet.muted:
            new_beginning = int(request.POST[key])
            snippet.beginning = new_beginning
        elif l_match and not snippet.muted:
            new_length = max(1, int(request.POST[key]))
            snippet.length = new_length
        elif c_match:
            snippet.comment = request.POST[key]
        elif t_match:
            snippet.optional = request.POST[key] == 'true'
        updated_snippets.add(snippet)
        logging.getLogger('palanaeum.staff').info("Audio snippet %s edited by %s.", snippet.id, request.user)
        updated_urls[snippet_id] = reverse('edit_snippet_entry',
                                           kwargs={'snippet_id': snippet_id})
    return updated_snippets, updated_urls


@json_response
@staff_member_required(login_url='auth_login')
@require_POST
@transaction.atomic
def update_snippets(request):
    """
    Update or create a new snippet. Return the edited snippet's id.
    """
    try:
        source_id = request.POST['source_id']
        source = get_object_or_404(AudioSource, pk=int(source_id))
    except KeyError:
        raise AjaxException('Missing source_id parameter.')

    try:
        updated_snippets, updated_urls = _process_snippets(source, request)
    except ValueError as err:
        raise AjaxException('Invalid value: {}.'.format(err))

    # Save changes
    snip_ids = []
    for s in updated_snippets:
        s.save()
        snip_ids.append(s.id)

    for snippet_id in snip_ids:
        tasks.create_snippet.delay(snippet_id)

    return {'saved_count': len(updated_snippets), 'edit_urls': updated_urls}


@login_required(login_url='auth_login')
def edit_snippet_entry(request, snippet_id):
    """
    Display a list of existing entries or allow user to create a new Entry.
    """
    snippet = get_object_or_404(Snippet, pk=snippet_id)

    if snippet.entry_id:
        return redirect('edit_entry', entry_id=snippet.entry_id)

    if not request.user.is_staff:
        # If has been decided that regular users can't connect snippets to existing entries.
        # They have to create new ones.
        return redirect('create_entry_for_snippet', snippet_id=snippet.id)

    if request.method == 'POST':
        entry = get_object_or_404(Entry, pk=request.POST['entry_id'])
        snippet.entry = entry
        snippet.save()
        messages.success(request, _('Snippet successfully assigned to entry.'))
        logging.getLogger('palanaeum.staff').info("Assigning snippet %s to entry %s by %s", snippet.id, entry.id,
                                                  request.user)
        return redirect('edit_audio_source', source_id=snippet.source_id)

    all_event_entries = Entry.objects.filter(event=snippet.source.event)

    if not all_event_entries.exists():
        return redirect('create_entry_for_snippet', snippet_id=snippet.id)  # Create a new entry for the snippet

    return render(request, 'palanaeum/staff/edit_snippet_entry.html',
                  {'snippet': snippet, 'event_entries': all_event_entries})


@login_required(login_url='auth_login')
def create_entry_for_snippet(request, snippet_id):
    """
    Create a new entry for snippet and go to edit page.
    If an entry already exists, just go to edit page.
    """
    snippet = get_object_or_404(Snippet, pk=snippet_id)

    if snippet.entry:
        messages.error(request, _("This snippet already has an entry assigned to it."))
        return redirect('edit_entry', entry_id=snippet.entry_id)

    entry = Entry()
    entry.created_by = request.user
    entry.event = snippet.source.event
    entry.is_approved = False
    entry.set_order_last()
    entry.save()

    snippet.entry = entry
    snippet.save()
    logging.getLogger('palanaeum.staff').info("Assigning snippet %s to entry %s by %s", snippet.id, entry.id,
                                              request.user)
    return redirect('edit_entry', entry_id=snippet.entry_id)


@login_required(login_url='auth_login')
def edit_entry(request, entry_id=None, event_id=None):
    """
    Display an edit page for Entry object.
    """
    if not is_contributor(request):
        messages.warning(request, _('This page is for contributors only.'))
        return redirect('index')

    if entry_id is None:
        entry = Entry()
        entry.event = get_object_or_404(Event, pk=event_id)
        version = EntryVersion(entry=entry)
        version.entry_date = entry.event.date
        entry.created_by = request.user
        entry.set_order_last()
    else:
        entry = get_object_or_404(Entry, pk=entry_id)

    if entry_id is not None:
        snippets = list(Snippet.all_visible.filter(entry=entry))
        images = list(ImageSource.all_visible.filter(entry=entry))
    else:
        snippets = []
        images = []

    return render(request, 'palanaeum/staff/entry_edit_form.html', {'entry': entry, 'event': entry.event,
                                                                    'snippets': snippets,
                                                                    'images': images})


@login_required(login_url='auth_login')
def show_entry_history(request, entry_id):
    """
    Display a page with two version of the entries, compared with each other, with highlighted changes.
    """
    if not is_contributor(request):
        messages.warning(request, _('This page is for contributors only.'))
        return redirect('index')

    entry = get_object_or_404(Entry, pk=entry_id)
    version_1 = request.GET.get('version_1', False)
    version_2 = request.GET.get('version_2', False)

    # Default newer is the newest version
    newer = entry.versions.last()
    older = None

    if version_2 and version_1:
        newer = get_object_or_404(EntryVersion, pk=version_2, entry_id=entry_id)
        older = get_object_or_404(EntryVersion, pk=version_1, entry_id=entry_id)
    elif newer is not None:
        # Default older is the last approved version
        # If there's no approved version, then it's the second to last version
        older = (entry.versions.filter(is_approved=True).exclude(pk=newer.pk).last() \
                or entry.versions.exclude(pk=newer.pk).last() or newer)

    if older is None or newer is None:
        raise Http404

    if newer.date < older.date:
        newer, older = older, newer

    def make_html(version):
        html = ['<article class="entry-article w3-display-container w3-border w3-card">']
        html += ['<header>Date: {}</header>'.format(version.entry_date)]
        for line in version.lines.all():
            html.append("<h3>{}{}</h3>".format(
                line.speaker, " ({})".format(_('paraphrased')) if version.paraphrased else ''))
            html.append(line.text)
        if version.note:
            html.append('<small class="footnote">Footnote: {}</small>'.format(version.note))
        if version.url_sources.exists():
            sources = "Sources: " + ", ".join(source.html() for source in version.url_sources.all())
            html.append("<div style='float:right'>{}</div>".format(sources))
        if version.tags.exists():
            tags = ", ".join(str(tag) for tag in version.tags.all())
            html.append('<footer>{}: {}</footer>'.format(_('Tags'), tags))
        else:
            html.append('<footer></footer>')

        html.append("</article>")
        return "".join(html)

    newer_html = make_html(newer)
    older_html = make_html(older)

    html_diff = htmldiff(older_html, newer_html)

    return render(request, "palanaeum/staff/entry_history.html", {
        'newer_version': newer,
        'newer_html': newer_html,
        'html_diff': html_diff,
        'older_version': older,
        'older_html': older_html,
        'entry': entry,
        'all_versions': EntryVersion.objects.filter(entry=entry),
        'snippets': Snippet.all_visible.filter(entry=entry),
        'images': ImageSource.all_visible.filter(entry=entry)
    })


@require_POST
@staff_member_required(login_url='auth_login')
def approve_entry(request, entry_id):
    """
    Approve changes to given entry.
    """
    entry = get_object_or_404(Entry, pk=entry_id)
    entry.versions.last().approve(request.user)
    logging.getLogger('palanaeum.staff').info("Entry %s (version: %s) approved by %s.", entry.id,
                                              entry.versions.last().id, request.user)
    messages.success(request, _("You have approved changes to this entry."))
    return redirect('edit_entry', entry_id=entry_id)


@require_POST
@staff_member_required(login_url='auth_login')
def reject_entry(request, entry_id):
    """
    Reject changes to given entry.
    """
    entry = get_object_or_404(Entry, pk=entry_id)
    last_version = entry.versions.last()
    logging.getLogger('palanaeum.staff').info("Entry %s (version: %s) rejected by %s.", entry.id,
                                              entry.versions.last().id, request.user)
    logging.getLogger('palanaeum.staff').info("Rejected version content: %s",
                                              "<br/>".join(str(line) for line in last_version.lines.all()))
    last_version.reject()

    if not entry.versions.exists():
        event_id = entry.event.id
        entry.delete()
        logging.getLogger('palanaeum.staff').info("Entry %s was removed because its last remaining version was rejected.", entry.id)
        messages.success(request, _("You have rejected changes to this entry. It was deleted because there weren't any remaining versions."))
        return redirect('view_event_no_title', event_id=event_id)
    else:
        messages.success(request, _("You have rejected changes to this entry. It is reverted to last approved version."))
        return redirect('edit_entry', entry_id=entry_id)


@json_response
@staff_member_required(login_url='auth_login')
@require_POST
@transaction.atomic
def delete_snippet(request):
    db_id = request.POST['db_id']
    snippet = get_object_or_404(Snippet, pk=db_id)

    snippet.delete()
    logging.getLogger('palanaeum.staff').info("Snippet %s deleted by %s.", snippet, request.user)

    return {'db_id': db_id}


def _entry_lines_by_ids(request, entry_version):
    """
    Return a map:
    * temporary_entry_id -> entry
    """
    lines_by_ids = {str(l.id): l for l in EntryLine.objects.filter(entry_version=entry_version)}
    lines_by_tmp_ids = {}
    id_re = r'^line-(\d+)-id$'

    for key in request.POST:
        match = re.match(id_re, key)
        if match is None:
            continue

        tmp_id = match.group(1)
        if request.POST[key]:
            lines_by_tmp_ids[tmp_id] = lines_by_ids[request.POST[key]]
        else:
            new_line = EntryLine()
            new_line.entry_version = entry_version
            lines_by_tmp_ids[tmp_id] = new_line

    return lines_by_tmp_ids


def _update_lines(request, lines_by_tmp_ids):
    line_re = r'^line-(\d+)-(speaker|text|order)$'

    for key in request.POST:
        match = re.match(line_re, key)

        if not match:
            continue

        line_id = match.group(1)
        match_type = match.group(2)
        line = lines_by_tmp_ids[line_id]

        if match_type == 'speaker':
            line.speaker = request.POST[key]
        elif match_type == 'text':
            line.text = request.POST[key]
        elif match_type == 'order':
            line.order = int(request.POST[key])
        else:
            raise ValueError("Unknown match_type.")


def _delete_lines(lines_by_tmp_ids):
    deleted_lines_ids = []

    for line in lines_by_tmp_ids.values():
        if not (line.speaker or line.text):
            if line.id:
                deleted_lines_ids.append(line.id)
                line.delete()
            else:
                deleted_lines_ids.append(line.order)
        else:
            line.save()

    return deleted_lines_ids


def _save_entry_lines(request, entry_version):
    """
    Save the lines of given entry.
    """
    lines_by_tmp_ids = _entry_lines_by_ids(request, entry_version)

    _update_lines(request, lines_by_tmp_ids)

    deleted_lines_ids = _delete_lines(lines_by_tmp_ids)

    lines_id_mapping = {tmp_id: line.id for tmp_id, line in lines_by_tmp_ids.items()}

    return lines_id_mapping, deleted_lines_ids


def _save_entry_url_sources(request, entry_version: EntryVersion):
    """
    Save updated url sources.
    """
    source_re = r'^url-source-(\d+)-(name|url)$'

    urls_data = defaultdict(dict)  # {id -> {url: "", name: ""}
    validator = URLValidator(['http', 'https'])

    for key in filter(lambda k: re.match(source_re, k), request.POST):
        match = re.match(source_re, key)
        urls_data[match.group(1)][match.group(2)] = request.POST[key]

    entry_version.url_sources.clear()

    for url_data in urls_data.values():
        name = url_data['name']
        url = url_data['url']

        try:
            validator(url)
        except ValidationError:
            continue

        if not url:
            continue

        try:
            url_obj = URLSource.objects.get(url=url)
        except URLSource.DoesNotExist:
            url_obj = URLSource.objects.create(url=url, text=name)
        else:
            url_obj.text = name
            url_obj.save()

        url_obj.entry_versions.add(entry_version)
        url_obj.save()

    URLSource.remove_unused()

    return


@json_response
@login_required(login_url='auth_login')
@require_POST
@transaction.atomic
def save_entry(request):
    """
    Save received entry data.
    """
    if not is_contributor(request):
        raise AjaxException(_('Only contributors can perform this action.'))

    if 'entry_id' not in request.POST or not request.POST['entry_id']:
        entry = Entry()
        event = get_object_or_404(Event, pk=request.POST['event_id'])
        entry.event = event
        entry.created_by = request.user
        entry.is_approved = False
        entry.set_order_last()
        entry.save()
        entry_version = EntryVersion()
        entry_version.entry = entry
        entry_version.entry_date = event.date
        entry_version.user = request.user
    else:
        entry_id = request.POST['entry_id']
        entry = get_object_or_404(Entry, pk=entry_id)
        event = entry.event
        entry_version = entry.versions.last()
        if entry_version is None:
            entry_version = EntryVersion()
            entry_version.entry = entry
            entry_version.entry_date = event.date
            entry_version.user = request.user

    entry_version.archive_version()
    entry_version.note = request.POST.get('note', '')
    entry_version.user = request.user
    entry_version.is_approved = False
    entry_version.approved_by = None
    entry_version.approved_date = None
    entry_version.paraphrased = bool(request.POST.get('paraphrased', False))
    entry_version.direct_entry = bool(request.POST.get('direct', False))
    entry_version.reported_by = request.POST.get('reported_by', '')

    date_str = request.POST.get('date', event.date.strftime("%Y-%m-%d"))
    if date_str:
        try:
            entry_version.entry_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise AjaxException(_("Unsupported date format. Expected date format is: YYYY-MM-DD."))
    else:
        entry_version.entry_date = event.date

    entry_version.save()

    lines_id_mapping, deleted_lines_ids = _save_entry_lines(request, entry_version)

    _save_entry_url_sources(request, entry_version)

    tags_str = ", ".join(request.POST.getlist('tags[]'))
    entry_version.update_tags(tags_str)

    # Save by staff member approves by default
    if request.user.is_staff:
        entry_version.approve(request.user)

    logging.getLogger('palanaeum.staff').info("Entry %s updated by %s", entry.id, request.user)

    return {'lines_id_mapping': lines_id_mapping, 'deleted_lines': deleted_lines_ids, 'entry_id': entry.id,
            'add_entry_url': reverse('event_add_entry', kwargs={'event_id': event.id})}


@json_response
@require_GET
@staff_member_required(login_url='auth_login')
def get_url_text(request):
    """
    Return name assigned to submitted url.
    """
    url = request.GET.get('url')

    try:
        url_obj = URLSource.objects.get(url=url)
    except URLSource.DoesNotExist:
        return {'text': ''}

    return {'text': url_obj.text}


@login_required(login_url='auth_login')
def choose_source_type(request, event_id):
    """
    Display a page where users select what type of sources they want to upload.
    """
    event = get_object_or_404(Event, pk=event_id)
    return render(request, 'palanaeum/staff/choose_source_type.html', {'event': event})


@login_required(login_url='auth_login')
def upload_audio_page(request, event_id):
    """
    Display a page with Fine Uploader that will upload the AudioSources.
    """
    event = get_object_or_404(Event, pk=event_id)
    if request.user.is_staff:
        limit = get_config('audio_staff_size_limit')
    else:
        limit = get_config('audio_user_size_limit')
    readable_limit = "{:4.2f} MB".format(limit)
    return render(request, 'palanaeum/staff/upload_audio_page.html',
                  {'event': event, 'file_size_limit': limit * 1024 * 1024,
                   'readable_limit': readable_limit})


@login_required(login_url='auth_login')
def upload_images_page(request, event_id):
    """
    Display a page with Fine Uploader that will upload the ImageSources.
    """
    event = get_object_or_404(Event, pk=event_id)
    limit = get_config('image_size_limit')
    readable_limit = "{:4.2f} MB".format(limit)
    return render(request, 'palanaeum/staff/upload_images_page.html',
                  {'event': event, 'file_size_limit': limit * 1024 * 1024,
                   'readable_limit': readable_limit})


@csrf_exempt
@json_response
@login_required(login_url='auth_login')
def upload_images_endpoint(request):
    """
    Save the image sent by user.
    """
    event = get_object_or_404(Event, pk=request.POST.get('eventId'))
    file_name = request.POST.get('qqfilename')

    img_source = ImageSource()
    img_source.event = event
    img_source.created_by = request.user
    img_source.is_approved = request.user.is_staff
    img_source.name = file_name
    img_source.save_uploaded_file(request.FILES['qqfile'])
    img_source.save()
    logging.getLogger('palanaeum.staff').info("Image source %s uploaded by %s.", img_source, request.user)
    return {'success': True}


@transaction.atomic
def rename_image_source(request, source_id):
    """
    Change the name of an image.
    """
    img = get_object_or_404(ImageSource, pk=source_id)

    if request.method == 'POST':
        form = ImageRenameForm(request.POST, instance=img)
        if form.is_valid():
            old_name = img.name
            new_name = form.save().name
            logging.getLogger('palanaeum.staff').info("%s renamed image source %s from '%s' to '%s'.",
                                                      request.user, img.pk, old_name, new_name)
            messages.success(request, _('Image source name changed.'))
            return redirect(img.event.get_absolute_url())
    else:
        form = ImageRenameForm(instance=img)

    return render(request, 'palanaeum/staff/edit_image_name.html', {'image': img, 'form': form})


@transaction.atomic
def edit_image_source_entry(request, source_id):
    """
    Display a list of available entries and a button to create a new entry.
    """
    img = get_object_or_404(ImageSource, pk=source_id)

    if request.method == 'POST':
        entry = get_object_or_404(Entry, pk=request.POST['entry_id'])
        img.entry = entry
        img.save()
        messages.success(request, _('Image successfully assigned to entry.'))
        logging.getLogger('palanaeum.staff').info("%s assigned image %s to entry %s.", request.user, img.id, entry.id)
        return redirect('view_event_no_title', event_id=img.event_id)

    all_event_entries = Entry.objects.filter(event=img.event)

    if not all_event_entries.exists():
        return redirect('create_entry_for_image_source', source_id=source_id)  # Create a new entry for the image

    return render(request, 'palanaeum/staff/edit_image_entry.html',
                  {'image': img, 'event_entries': all_event_entries})


@transaction.atomic
def create_entry_for_image_source(request, source_id):
    """
    Create an empty Entry for Image Source and assign it to the source.
    """
    img_source = get_object_or_404(ImageSource, pk=source_id)

    entry = Entry()
    entry.event = img_source.event
    entry.created_by = request.user
    entry.save()

    img_source.entry = entry
    img_source.save()

    messages.success(request, _('New entry for image source has been created and linked.'))
    logging.getLogger('palanaeum.staff').info("%s created new entry for image %s.", request.user, img_source.id)

    return redirect('edit_entry', entry_id=entry.id)


@staff_member_required(login_url='auth_login')
def sort_entries_page(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    entries_ids = Entry.objects.filter(event=event).values_list('id', flat=True)
    entries = Entry.prefetch_entries(entries_ids, show_unapproved=True)
    entries = sorted(entries.values(), key=lambda e: e.order)
    return render(request, 'palanaeum/staff/sort_entries.html',
                  {'event': event, 'entries': entries, 'sources': list(event.sources_iterator())})


@staff_member_required(login_url='auth_login')
@transaction.atomic
@require_POST
@json_response
def save_entries_order(request):
    try:
        event_id = request.POST.get('eventId', None)
        ordering = json.loads(request.POST.get('ordering'))
        assert isinstance(ordering, dict)
        ordering = {int(key): int(value) for key, value in ordering.items()}
    except KeyError:
        raise AjaxException("This view requires two parameters: "
                            "eventId and ordering.")
    except json.JSONDecodeError:
        raise AjaxException("Invalid JSON in ordering.")
    except AssertionError:
        raise AjaxException("JSON in ordering has to represent a dict.")
    except TypeError:
        raise AjaxException("Only integers are allowed in ordering dict.")

    event = get_object_or_404(Event, pk=event_id)
    entries_dict = Entry.objects.filter(event=event).in_bulk(ordering.keys())
    Entry.objects.filter(event=event).update(order=max(ordering.values())+1)

    for entry_id, order in ordering.items():
        entries_dict[entry_id].order = int(order)
        entries_dict[entry_id].save()

    logging.getLogger('palanaeum.staff').info("%s reordered entries in event %s", request.user, event_id)

    return {'url': reverse('view_event_no_title', kwargs={'event_id': event_id})}


@staff_member_required(login_url='auth_login')
@transaction.atomic
def reorder_entries_by_snippets(request, event_id):
    # FIXME: Make it a POST only view with CSRF protection
    event = get_object_or_404(Event, pk=event_id)
    entries = Entry.objects.filter(event_id=event_id).prefetch_related('snippets')

    with_snippets = []
    without_snippets = []

    for entry in entries:
        if entry.snippets.exists():
            with_snippets.append(entry)
        else:
            without_snippets.append(entry)

    def snippet_key(entry):
        return tuple(sorted((s.source_id, s.beginning) for s in entry.snippets.all()))

    with_snippets.sort(key=snippet_key)

    without_snippets.sort(key=lambda item: item.order)

    for i, entry in enumerate(with_snippets + without_snippets):
        entry.order = i
        entry.save()

    logging.getLogger('palanaeum.staff').info("%s reordered entries in event %s", request.user, event_id)

    return redirect('view_event_no_title', event_id=event.id)


@staff_member_required(login_url='auth_login')
@transaction.atomic
def reorder_entries_by_creation_date(request, event_id):
    # FIXME: Make it a POST only view with CSRF protection
    event = get_object_or_404(Event, pk=event_id)
    entries_dict = Entry.objects.filter(event=event).in_bulk()
    versions = EntryVersion.objects.filter(entry__event=event).only('entry_id', 'date').order_by('-date').distinct('entry_id')

    for i, ev in enumerate(reversed(versions)):
        entries_dict[ev.entry_id].order = i
        entries_dict[ev.entry_id].save()

    logging.getLogger('palanaeum.staff').info("%s reordered entries in event %s", request.user, event_id)

    return redirect('view_event_no_title', event_id=event.id)


@staff_member_required(login_url='auth_login')
@transaction.atomic
def reorder_entries_by_assigned_date(request, event_id):
    # FIXME: Make it a POST only view with CSRF protection
    event = get_object_or_404(Event, pk=event_id)
    versions = sorted(EntryVersion.newest.filter(entry__event=event).select_related('entry'),
                      key=lambda ev: ev.entry_date)

    for i, ev in enumerate(versions):
        ev.entry.order = i
        ev.entry.save()

    logging.getLogger('palanaeum.staff').info("%s reordered entries in event %s", request.user, event_id)

    return redirect('view_event_no_title', event_id=event.id)


@staff_member_required(login_url='auth_login')
def mute_snippet(request, source_id):
    """
    Display a page where staff member can select a snippet to be muted, or perform the muting.
    """
    audio_source = get_object_or_404(AudioSource, pk=source_id)
    snippets = Snippet.objects.filter(source=audio_source)

    if request.method == 'POST':
        try:
            snippet = Snippet.objects.get(pk=int(request.POST['snippet_id']))
            snippet.muted = True
            snippet.save()
            tasks.mute_snippet.delay(snippet.id)
        except (KeyError, ValueError, Snippet.DoesNotExist):
            messages.error(request, _("Couldn't process your request. Is the selected snippet correct?"))
        else:
            messages.success(request, _("Selected snippet was scheduled for muting."))
            logging.getLogger('palanaeum.staff').info("%s scheduled muting of snippet %s", request.user, snippet)
            return redirect('mute_snippet', source_id=source_id)

    return render(request, 'palanaeum/staff/mute_snippet.html', {'snippets': snippets, 'audio_source': audio_source})


@staff_member_required(login_url='auth_login')
def staff_cp_suggestions(request):
    source_suggestions = list(AudioSource.objects.filter(is_approved=False))
    source_suggestions.extend(ImageSource.objects.filter(is_approved=False))

    entry_suggestions_id = Entry.objects.filter(versions__is_approved=False).values_list('id', flat=True)
    entry_suggestions = Entry.prefetch_entries(entry_suggestions_id, show_unapproved=True).values()

    all_suggestions = defaultdict(lambda: defaultdict(list))
    for entry in entry_suggestions:
        all_suggestions[entry.event]['entries'].append(entry)

    for source in source_suggestions:
        all_suggestions[source.event]['sources'].append(source)

    return render(request, 'palanaeum/staff/staff_cp_suggestions.html',
                  {'sources': source_suggestions, 'entries': entry_suggestions,
                   'all_suggestions': dict(all_suggestions),
                   'page': 'suggestions'})


@staff_member_required(login_url='auth_login')
def staff_cp(request):
    """
    Display a page with summary of all unapproved suggestions etc.
    """

    return render(request, 'palanaeum/staff/staff_cp.html', {'page': 'index'})
