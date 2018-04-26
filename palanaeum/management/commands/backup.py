from django.core.management.base import BaseCommand, CommandError
from palanaeum.tasks import backup_palanaeum

class Command(BaseCommand):
    help = 'Creates a new backup file.'

    def handle(self, *args, **options):
        backup_palanaeum()