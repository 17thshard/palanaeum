from django.http import HttpRequest


def is_contributor(request: HttpRequest) -> bool:
    """
    Defines is a user from given request should see non-approved things.
    """
    return hasattr(request, 'user') and request.user.is_authenticated
