# coding=utf-8
from django.apps import apps
from django.contrib.staticfiles.templatetags.staticfiles import static

from palanaeum import settings, search, configuration
from palanaeum.models import Entry, AudioSource, ImageSource


def favicon(size):
    return configuration.get_config('favicon{}'.format(size)) or static('palanaeum/img/favicon{}.png'.format(size))


def palanaeum_context(request):
    """
    Put all useful information into context, like page title.
    """
    if hasattr(request, 'user') and request.user.is_staff:
        suggestions = Entry.objects.filter(versions__is_approved=False).distinct().count()
        suggestions += AudioSource.objects.filter(is_approved=False).count()
        suggestions += ImageSource.objects.filter(is_approved=False).count()
        is_staff = True
    else:
        suggestions = 0
        is_staff = False

    logo_path = configuration.get_config('logo_file') or static('palanaeum/img/palanaeum_logo.svg')
    palanaeum_app = apps.get_app_config('palanaeum')

    return {
        'BASE_URL': request.build_absolute_uri("/").rstrip("/"),
        'PAGE_TITLE': configuration.get_config('page_title'),
        'TINYMCE_API_KEY': settings.TINYMCE_API_KEY,
        'GENERAL_SEARCH_PARAM_NAME': search.TextSearchFilter.GET_PARAM_NAME,
        'GOOGLE_ID': configuration.get_config('google_analytics'),
        'SUGGESTIONS_COUNT': suggestions,
        'STAFF': is_staff,
        'PALANAEUM_VERSION': settings.PALANAEUM_VERSION,
        'PALANAEUM_LOGO_URL': logo_path,
        'FAVICON16': favicon(16),
        'FAVICON32': favicon(32),
        'FAVICON96': favicon(96),
        'FAVICON120': favicon(120),
        'FAVICON152': favicon(152),
        'FAVICON167': favicon(167),
        'FAVICON180': favicon(180),
        'FAVICON200': favicon(200),
        'VERSION_TAG': palanaeum_app.version,
    }