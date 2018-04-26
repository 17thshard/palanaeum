from django.core.management.base import BaseCommand

from palanaeum.models import EntrySearchVector, Entry


class Command(BaseCommand):
    help = 'Recreate the whole search index.'

    def handle(self, *args, **options):
        entries_count = Entry.objects.count()

        EntrySearchVector.objects.all().delete()

        for i, entry in enumerate(Entry.objects.all()):
            esv = EntrySearchVector(entry=entry)
            esv.update()
            if i % 10 == 0:
                self.stdout.write("\r{:4.2%}".format(i/entries_count), ending='')

        self.stdout.write("\rSearch index rebuilt.")
