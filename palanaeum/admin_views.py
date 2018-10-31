import itertools
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from palanaeum.configuration import get_config_dict, set_config, CONFIG_ENTRIES, set_config_file
from palanaeum.decorators import json_response, AjaxException
from palanaeum.forms import GeneralConfig, AudioConfig, CloudConfig, RelatedSiteForm, FaviconsConfig
from palanaeum.models import RelatedSite, ConfigEntry
from palanaeum.utils import page_numbers_to_show


@user_passes_test(lambda u: u.is_superuser, login_url="auth_login")
def index(request):
    usage = shutil.disk_usage(settings.MEDIA_ROOT)
    total_space_str = "{:.2f} Gb".format(usage.total / 1024**3)
    used_space_str = "{:.2f} Gb".format(usage.used / 1024**3)
    free_space_str = "{:.2f} Gb".format(usage.free / 1024**3)
    return render(request, 'palanaeum/admin/admin_index.html',
                  {'used_space': usage.used, 'available_space': usage.free,
                   'total_space': usage.total, 'total_space_str': total_space_str,
                   'free_space_str': free_space_str, 'used_space_str': used_space_str})


@user_passes_test(lambda u: u.is_superuser, login_url="auth_login")
def config(request):
    current_config = get_config_dict()

    if request.method == 'POST':
        general_form = GeneralConfig(request.POST, request.FILES)
        audio_form = AudioConfig(request.POST, request.FILES)
        cloud_form = CloudConfig(request.POST, request.FILES)
        favicon_form = FaviconsConfig(request.POST, request.FILES)
        forms = [general_form, audio_form, cloud_form, favicon_form]
        if all(form.is_valid() for form in forms):
            for key, value in itertools.chain(*(form.cleaned_data.items() for form in forms)):
                if CONFIG_ENTRIES.get(key)[0] == 'file' and key in request.FILES:
                    set_config_file(key, request.FILES[key])
                else:
                    set_config(key, value)
            messages.success(request, _('New settings successfully saved.'))
        else:
            messages.error(request, _('There is an error in provided settings.'))
    else:
        general_form = GeneralConfig(initial=current_config)
        audio_form = AudioConfig(initial=current_config)
        cloud_form = CloudConfig(initial=current_config)
        favicon_form = FaviconsConfig(initial=current_config)

    return render(request, 'palanaeum/admin/config.html', {
        'general_config': general_form, 'audio_config': audio_form, 'cloud_config': cloud_form,
        'favicon_config': favicon_form,
    })


@user_passes_test(lambda u: u.is_superuser)
def users_list(request):
    only_staff = request.GET.get('only_staff', False)
    if only_staff:
        users = User.objects.filter(is_staff=True)
    else:
        users = User.objects.all()

    users = users.order_by('username')

    paginator = Paginator(users, 50, 10)
    try:
        page = paginator.page(request.GET.get('page', 0))
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    to_show = page_numbers_to_show(paginator, page.number)

    return render(request, 'palanaeum/admin/users_list.html', {'page': page,
                                                               'page_numbers_to_show': to_show})


@require_POST
@user_passes_test(lambda u: u.is_superuser)
@json_response
def set_user_state(request):
    try:
        user_id = request.POST['user_id']
        user = User.objects.get(pk=user_id)
        is_active = request.POST.get('is_active', False) == 'true'
        is_staff = request.POST.get('is_staff', False) == 'true'
        is_superuser = request.POST.get('is_superuser', False) == 'true'
    except KeyError:
        raise AjaxException('Missing user_id parameter.')
    except User.DoesNotExist:
        raise Http404

    user.is_active = is_active
    user.is_staff = is_staff and is_active
    user.is_superuser = is_superuser and is_staff and is_active
    user.save()

    return {'is_staff': user.is_staff, 'is_active': user.is_active,
            'is_superuser': user.is_superuser, 'user_id': user_id}


@user_passes_test(lambda u: u.is_superuser)
def related_sites_list(request):
    related_sites = RelatedSite.objects.all()
    return render(request, 'palanaeum/admin/related_sites.html', {'related_sites': related_sites})


@user_passes_test(lambda u: u.is_superuser)
def related_site_edit(request, site_id: int=None):
    if site_id is not None:
        related_site = get_object_or_404(RelatedSite, pk=site_id)
    else:
        related_site = RelatedSite()

    if request.method == 'POST':
        form = RelatedSiteForm(request.POST, files=request.FILES, instance=related_site)
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, _('Related site updated successfully.'))
            return redirect('admin_related_sites')
    else:
        form = RelatedSiteForm(instance=related_site)

    return render(request, 'palanaeum/admin/related_site_edit.html', {'form': form, 'related_site': related_site})


@user_passes_test(lambda u: u.is_superuser)
def related_site_delete(request, site_id: int=None):
    related_site = get_object_or_404(RelatedSite, pk=site_id)
    if request.method == 'POST':
        related_site.delete()
        messages.success(request, _('Related site deleted successfully'))
        return redirect('admin_related_sites')

    return render(request, 'palanaeum/admin/delete_related_site_confirm.html', {'related_site': related_site})


@user_passes_test(lambda u: u.is_superuser)
def reset_favicons(request):
    sizes = [16, 32, 96, 120, 152, 167, 180]
    ConfigEntry.objects.filter(key__in=("favicon{}".format(size) for size in sizes)).delete()
    messages.success(request, _('Favicons were restored to defaults.'))

    return redirect('admin_config')
