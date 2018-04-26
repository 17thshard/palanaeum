# coding=utf-8
import json
import logging

from django.http import HttpResponse


class AjaxException(BaseException):
    """
    This exception should be raised in views decorated with json_response decorator.
    If a view raises this exception, the decorator will create a JSON response of following format:
    {'success': False, 'reason': exception_message} where exception_message is what you type in the
    exception constructor.
    """
    def __init__(self, msg):
        super(AjaxException).__init__()
        self.msg = msg


def json_response(org_fun):
    """
    This decorator converts list or dictionary returned by a function into a HttpResponse containing JSON encoded data.
    """
    def func(request, *args, **kwargs):
        try:
            ret = org_fun(request, *args, **kwargs)
        except AjaxException as ae:
            ret = {'success': False, 'reason': str(ae.msg)}
        if ret is None:
            ret = {}
        if not isinstance(ret, dict):
            if isinstance(ret, HttpResponse) and ret.status_code == 200:
                logging.getLogger('palanaeum').warning("Json response requires list or dict from decorated function. Got: {}. "
                                                       "Request for: {}".format(ret.content.decode(), request.path))
            return ret
        if 'success' not in ret:
            ret['success'] = True
        encoded = json.dumps(ret)
        return HttpResponse(encoded, content_type='application/json')
    return func
