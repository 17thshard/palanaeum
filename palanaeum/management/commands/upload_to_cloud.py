import logging

from django.core.management.base import BaseCommand
from palanaeum.tasks import upload_new_sources_to_cloud

logger = logging.getLogger('palanaeum.admin')


class Command(BaseCommand):
    """
    Manually executes the cloud uploading Celery task.
    """
    help = __doc__

    def handle(self, *args, **options):
        upload_new_sources_to_cloud()
