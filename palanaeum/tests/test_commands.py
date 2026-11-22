import contextlib
import datetime
import io
import os
import pathlib
import runpy
import unittest
from unittest import mock

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from palanaeum.cloud.exceptions import DownloadError
from palanaeum.models import AudioSource, EntryLine, EntrySearchVector, EntryVersion, Event
from palanaeum.tests.factories import (
    AudioSourceFactory,
    EntryFactory,
    EntryLineFactory,
    EntryVersionFactory,
    EventFactory,
    SnippetFactory,
)


class ManagementCommandsTests(TestCase):
    def test_backup_command_invokes_backup_task(self):
        with mock.patch("palanaeum.management.commands.backup.backup_palanaeum") as m_backup:
            call_command("backup")
        m_backup.assert_called_once_with()

    def test_upload_to_cloud_command_invokes_upload_task(self):
        with mock.patch("palanaeum.management.commands.upload_to_cloud.upload_new_sources_to_cloud") as m_upload:
            call_command("upload_to_cloud")
        m_upload.assert_called_once_with()

    def test_generate_and_insert_test_events_command(self):
        call_command("generate_and_insert_test_events", "-n", "2")
        events = list(Event.objects.order_by("date"))
        self.assertEqual(len(events), 2)
        self.assertEqual([e.name for e in events], ["auto_generated_event_1", "auto_generated_event_2"])
        self.assertEqual(events[0].date, datetime.date(2017, 1, 1))
        self.assertEqual(events[1].date, datetime.date(2017, 1, 2))
        self.assertTrue(all(e.review_state in dict(Event.REVIEW_STATES) for e in events))

    def test_rebuild_search_index_empty_and_populated(self):
        out_empty = io.StringIO()
        call_command("rebuild_search_index", stdout=out_empty)
        self.assertIn("Search index rebuilt.", out_empty.getvalue())
        self.assertEqual(EntrySearchVector.objects.count(), 0)

        event = EventFactory(is_approved=True)
        e1 = EntryFactory(event=event, is_approved=True)
        v1 = EntryVersionFactory(entry=e1, is_approved=True)
        EntryLineFactory(entry_version=v1, speaker="Kelsier", text="Survive in Luthadel")
        e2 = EntryFactory(event=event, is_approved=True)
        v2 = EntryVersionFactory(entry=e2, is_approved=True)
        EntryLineFactory(entry_version=v2, speaker="Vin", text="Mistborn metals")
        stale = EntrySearchVector(entry=e1)
        stale.update()

        out_pop = io.StringIO()
        call_command("rebuild_search_index", stdout=out_pop)
        self.assertEqual(EntrySearchVector.objects.count(), 2)
        self.assertIn("0.00%", out_pop.getvalue())
        self.assertIn("Search index rebuilt.", out_pop.getvalue())

    @mock.patch("palanaeum.management.commands.transcode_all.subprocess.run")
    @mock.patch("palanaeum.management.commands.transcode_all.get_cloud_backend")
    def test_transcode_all_command_handles_local_cloud_error_and_snippets(self, mock_backend, mock_run):
        event = EventFactory(is_approved=True)

        src_local = AudioSourceFactory(
            event=event,
            status=AudioSource.READY,
            length=30,
            raw_file=SimpleUploadedFile("local.wav", b"LOCAL"),
            transcoded_file=SimpleUploadedFile("local.mp3", b"OLD"),
        )
        src_cloud_ok = AudioSourceFactory(
            event=event,
            status=AudioSource.STORED_IN_CLOUD,
            length=40,
            raw_file=SimpleUploadedFile("cloud_ok.wav", b"C1"),
            transcoded_file=SimpleUploadedFile("cloud_ok.mp3", b"OLD"),
        )
        os.unlink(src_cloud_ok.raw_file.path)

        src_cloud_err = AudioSourceFactory(
            event=event,
            status=AudioSource.STORED_IN_CLOUD,
            length=50,
            raw_file=SimpleUploadedFile("cloud_err.wav", b"C2"),
            transcoded_file=SimpleUploadedFile("cloud_err.mp3", b"OLD"),
        )
        os.unlink(src_cloud_err.raw_file.path)

        snip = SnippetFactory(
            source=src_local,
            beginning=5,
            length=10,
            file=str(pathlib.Path(settings.MEDIA_ROOT) / "snip_out.mp3"),
        )

        cloud = mock.MagicMock()

        def fake_download(source):
            if source.pk == src_cloud_err.pk:
                raise RuntimeError("cloud unavailable")
            pathlib.Path(source.raw_file.path).write_bytes(b"DOWNLOADED")

        cloud.download_source.side_effect = fake_download
        mock_backend.return_value = cloud

        out = io.StringIO()
        with self.assertLogs("palanaeum.admin", level="ERROR"):
            call_command("transcode_all", stdout=out)

        self.assertIn("Successfully transcoded 3 sources.", out.getvalue())
        self.assertIn("Successfully transcoded 1 snippets.", out.getvalue())
        self.assertFalse(os.path.exists(src_cloud_ok.raw_file.path))
        self.assertTrue(os.path.exists(src_local.raw_file.path))
        # 2 sources (local + cloud_ok; cloud_err skipped on download exception) + 1 snippet = 3 calls
        self.assertEqual(mock_run.call_count, 3)
        self.assertEqual(mock_run.call_args_list[-1].args[0][-1], snip.file)

    @unittest.expectedFailure
    def test_fix_bad_uploads_command_is_registered_with_command_class(self):
        """
        Bug in palanaeum/management/commands/fix_bad_uploads.py:1-73 — the file
        imports BaseCommand but omits a `Command(BaseCommand)` class and executes
        top-level script statements unconditionally on import, so
        `call_command('fix_bad_uploads')` fails.
        """
        call_command("fix_bad_uploads")

    def test_fix_bad_uploads_script_execution_via_runpy(self):
        event = EventFactory(is_approved=True)
        s1 = AudioSourceFactory(
            event=event,
            status=AudioSource.STORED_IN_CLOUD,
            length=30,
            raw_file="talk(1).wav",
            transcoded_file=SimpleUploadedFile("talk_1.mp3", b"MP3_1"),
        )
        s2 = AudioSourceFactory(
            event=event,
            status=AudioSource.STORED_IN_CLOUD,
            length=30,
            raw_file="talk(2).wav",
            transcoded_file=SimpleUploadedFile("talk_2.mp3", b"MP3_2"),
        )
        snip = SnippetFactory(
            source=s1,
            beginning=0,
            length=5,
            file=str(pathlib.Path(settings.MEDIA_ROOT) / "bad_snip.mp3"),
        )

        # Entry whose newest version has speaker='Footnote'
        e_foot = EntryFactory(event=event, is_approved=True)
        v_foot = EntryVersionFactory(entry=e_foot, is_approved=True)
        EntryLineFactory(entry_version=v_foot, speaker="Footnote", text="Clarifying footnote")
        EntryLineFactory(entry_version=v_foot, speaker="Hoid", text="Main answer")

        # Entry whose older version has speaker='Footnote', but newest version does not
        e_old_foot = EntryFactory(event=event, is_approved=True)
        t_old = timezone.now() - datetime.timedelta(days=5)
        v_old = EntryVersionFactory(entry=e_old_foot, date=t_old, is_approved=True)
        EntryVersion.objects.filter(pk=v_old.pk).update(date=t_old)
        EntryLineFactory(entry_version=v_old, speaker="Footnote", text="Old footnote")
        v_new = EntryVersionFactory(entry=e_old_foot, is_approved=True)
        EntryLineFactory(entry_version=v_new, speaker="Dalinar", text="No footnote in newest")

        fake_b2 = mock.MagicMock()
        fake_b2._url_encode.side_effect = lambda name: str(name).replace("(", "%28").replace(")", "%29")

        def fake_download(file_name, dest_path):
            if "%282%29" in str(file_name):
                raise DownloadError("encoded lookup failed")
            pathlib.Path(dest_path).write_bytes(b"DOWNLOADED")
            return dest_path

        fake_b2.download_file.side_effect = fake_download

        script_path = pathlib.Path(settings.BASE_DIR) / "palanaeum" / "management" / "commands" / "fix_bad_uploads.py"
        captured_out = io.StringIO()
        with mock.patch("palanaeum.cloud.get_cloud_backend", return_value=fake_b2), mock.patch(
            "subprocess.run"
        ) as mock_run, contextlib.redirect_stdout(captured_out):
            runpy.run_path(str(script_path), run_name="fix_bad_uploads_test")

        # s1 used encoded name once; s2 fell back to raw name after DownloadError
        self.assertEqual(fake_b2.download_file.call_count, 3)
        self.assertEqual(fake_b2.upload_source.call_count, 2)
        self.assertEqual(mock_run.call_count, 3)  # 2 sources + 1 snippet
        self.assertEqual(mock_run.call_args_list[-1].args[0][-1], snip.file)
        self.assertFalse(os.path.exists(s1.raw_file.path))
        self.assertFalse(os.path.exists(s2.raw_file.path))
        self.assertEqual(AudioSource.objects.filter(pk__in=[s1.pk, s2.pk], status=AudioSource.READY).count(), 2)

        # Footnote on newest version was archived & moved to version.note
        v_foot.refresh_from_db()
        self.assertEqual(v_foot.note, "Clarifying footnote")
        self.assertFalse(EntryLine.objects.filter(entry_version=v_foot, speaker="Footnote").exists())
        self.assertEqual(e_foot.versions.count(), 2)
        # Old footnote entry skipped updating v_new because its newest version had no Footnote line
        v_new.refresh_from_db()
        self.assertEqual(v_new.note, "")
