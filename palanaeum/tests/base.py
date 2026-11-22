from contextlib import contextmanager
from io import BytesIO

from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from PIL import Image

from palanaeum import middleware


@contextmanager
def set_current_request(user=None, path="/"):
    """
    Temporarily set the thread-local request inspected by VisibleManager,
    Content, Tag.get_tag, EventForm, and model permission helpers.
    """
    request = RequestFactory().get(path)
    request.user = user if user is not None else AnonymousUser()
    prev_request = getattr(middleware._GLOBAL_REQUEST_BOX, "request", None)
    middleware._GLOBAL_REQUEST_BOX.request = request
    try:
        yield request
    finally:
        middleware._GLOBAL_REQUEST_BOX.request = prev_request


def make_test_image_bytes(size=(50, 50), color=(0, 128, 255), image_format="PNG"):
    buffer = BytesIO()
    img = Image.new("RGB", size, color)
    img.save(buffer, format=image_format)
    return buffer.getvalue()


def make_uploaded_image(
    name="test.png",
    size=(50, 50),
    color=(0, 128, 255),
    content_type="image/png",
):
    data = make_test_image_bytes(size=size, color=color, image_format="PNG")
    return SimpleUploadedFile(name, data, content_type=content_type)


def make_LocMem_caches_setting(location_prefix="palanaeum-test"):
    return {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": f"{location_prefix}-default",
        },
        "search": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": f"{location_prefix}-search",
        },
        "config": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": f"{location_prefix}-config",
        },
    }
