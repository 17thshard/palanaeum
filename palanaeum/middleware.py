# coding=utf-8
import threading

import pytz
from django.utils import timezone

_GLOBAL_REQUEST_BOX = threading.local()


class TimezoneMiddleware:
    """
    Sets the correct timezone for user.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, 'settings'):
                settings = request.user.settings
            else:
                from palanaeum.models import UserSettings
                settings = UserSettings.objects.create(user=request.user)
            tzname = settings.timezone
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()

        response = self.get_response(request)

        return response


class GlobalRequestKeeper:
    """
    Keep a reference to currently processed request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _GLOBAL_REQUEST_BOX
        _GLOBAL_REQUEST_BOX.request = request
        return self.get_response(request)


def get_request():
    global _GLOBAL_REQUEST_BOX
    return getattr(_GLOBAL_REQUEST_BOX, 'request', None)
