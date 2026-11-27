import datetime
import json
import os
import pathlib
import shutil
import stat
import struct
import subprocess
import unittest
import wave
import zipfile
from unittest import mock

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from palanaeum.cloud.exceptions import PalanaeumCloudError
from palanaeum.configuration import set_config
from palanaeum.models import AudioSource
from palanaeum.tasks import (
    backup_palanaeum,
    create_snippet,
    mute_snippet,
    transcode_source,
    upload_new_sources_to_cloud,
)
from palanaeum.tests.factories import AudioSourceFactory, EventFactory, SnippetFactory


def _write_silent_wav(path: pathlib.Path, duration_seconds: float = 0.2, sample_rate: int = 8000):
    path.parent.mkdir(parents=True, exist_ok=True)
    num_frames = int(duration_seconds * sample_rate)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack("<" + "h" * num_frames, *([0] * num_frames)))


class TranscodeSourceTaskTests(TestCase):
    def setUp(self):
        self.event = EventFactory(is_approved=True)

    @mock.patch("palanaeum.tasks.time.sleep")
    def test_missing_audio_source_retries_and_aborts(self, mock_sleep):
        with self.assertLogs("palanaeum.celery", level="ERROR") as logs:
            transcode_source(999999)
        mock_sleep.assert_called_once_with(2)
        self.assertTrue(any("wasn't found in the database" in line for line in logs.output))

    @mock.patch("palanaeum.tasks.subprocess.run")
    @mock.patch("palanaeum.tasks.time.sleep")
    def test_audio_source_appearing_on_second_lookup_succeeds(self, mock_sleep, mock_run):
        src = AudioSourceFactory(
            event=self.event,
            status=AudioSource.WAITING,
            length=30,
            raw_file=SimpleUploadedFile("retry_talk.wav", b"RIFF-data"),
        )

        def fake_ffmpeg(cmd, **_kwargs):
            out_path = pathlib.Path(cmd[-1])
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(b"mp3-bytes")

        mock_run.side_effect = fake_ffmpeg

        with mock.patch.object(AudioSource.objects, "get", side_effect=[AudioSource.DoesNotExist, src]):
            transcode_source(src.pk)

        mock_sleep.assert_called_once_with(2)
        src.refresh_from_db()
        self.assertEqual(src.status, AudioSource.READY)
        self.assertTrue(str(src.transcoded_file).endswith(".mp3"))
        self.assertTrue(pathlib.Path(src.transcoded_file.path).is_file())

    @mock.patch("palanaeum.tasks.subprocess.run")
    def test_non_waiting_status_aborts_early(self, mock_run):
        src = AudioSourceFactory(
            event=self.event,
            status=AudioSource.READY,
            length=15,
            raw_file=SimpleUploadedFile("already_ready.wav", b"RIFF"),
        )
        with self.assertLogs("palanaeum.celery", level="ERROR"):
            transcode_source(src.pk)
        mock_run.assert_not_called()

    @mock.patch("palanaeum.tasks.subprocess.run")
    def test_missing_raw_file_and_ffmpeg_failure_marks_failed(self, mock_run):
        src = AudioSourceFactory(
            event=self.event,
            status=AudioSource.WAITING,
            length=15,
            raw_file=SimpleUploadedFile("missing_src.wav", b"RIFF"),
        )
        os.unlink(src.raw_file.path)
        mock_run.side_effect = subprocess.CalledProcessError(1, ["ffmpeg"])

        with self.assertLogs("palanaeum.celery", level="ERROR") as logs:
            with self.assertRaises(subprocess.CalledProcessError):
                transcode_source(src.pk)

        src.refresh_from_db()
        self.assertEqual(src.status, AudioSource.FAILED)
        self.assertTrue(any("Raw file" in line for line in logs.output))

    @mock.patch("palanaeum.tasks.subprocess.run")
    def test_collision_suffix_loop_and_happy_path(self, mock_run):
        src = AudioSourceFactory(
            event=self.event,
            status=AudioSource.WAITING,
            length=42,
            raw_file=SimpleUploadedFile("panel.wav", b"WAV"),
        )
        base, _ = os.path.splitext(src.raw_file.path)
        pathlib.Path(base + ".mp3").write_bytes(b"existing-0")
        pathlib.Path(base + "-transcoded.mp3").write_bytes(b"existing-1")

        captured_cmds = []

        def fake_ffmpeg(cmd, **kwargs):
            captured_cmds.append((cmd, kwargs))
            pathlib.Path(cmd[-1]).write_bytes(b"transcoded-final")

        mock_run.side_effect = fake_ffmpeg
        set_config("audio_quality", "192k")

        transcode_source(src.pk)

        src.refresh_from_db()
        self.assertEqual(src.status, AudioSource.READY)
        self.assertTrue(str(src.transcoded_file).endswith("-transcoded-transcoded.mp3"))
        self.assertTrue(pathlib.Path(src.transcoded_file.path).is_file())
        self.assertEqual(captured_cmds[0][0][:5], ["ffmpeg", "-y", "-i", src.raw_file.path, "-b:a"])
        self.assertEqual(captured_cmds[0][0][5], "192k")
        self.assertTrue(captured_cmds[0][1]["check"])

    @mock.patch("palanaeum.tasks.subprocess.run")
    def test_deleted_mid_transcode_aborts_before_saving_ready(self, mock_run):
        src = AudioSourceFactory(
            event=self.event,
            status=AudioSource.WAITING,
            length=25,
            raw_file=SimpleUploadedFile("deleted_mid.wav", b"WAV"),
        )

        def delete_mid_run(cmd, **_kwargs):
            pathlib.Path(cmd[-1]).write_bytes(b"mp3")
            AudioSource.objects.filter(pk=src.pk).delete()

        mock_run.side_effect = delete_mid_run
        with self.assertLogs("palanaeum.celery", level="ERROR") as logs:
            transcode_source(src.pk)

        self.assertFalse(AudioSource.objects.filter(pk=src.pk).exists())
        self.assertTrue(any("has been deleted" in line for line in logs.output))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe not installed")
    def test_transcode_source_real_ffmpeg_smoke(self):
        wav_path = pathlib.Path(settings.MEDIA_ROOT) / "smoke_tone.wav"
        _write_silent_wav(wav_path, duration_seconds=0.25)

        src = AudioSourceFactory(
            event=self.event,
            status=AudioSource.WAITING,
            length=1,
            raw_file="smoke_tone.wav",
        )
        transcode_source(src.pk)
        src.refresh_from_db()
        self.assertEqual(src.status, AudioSource.READY)
        self.assertTrue(str(src.transcoded_file).endswith(".mp3"))
        out_path = pathlib.Path(src.transcoded_file.path)
        self.assertTrue(out_path.is_file())
        self.assertGreater(out_path.stat().st_size, 0)

        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=format_name", "-of", "default=nw=1:nk=1", str(out_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertIn("mp3", probe.stdout.decode().lower())


class SnippetTasksTests(TestCase):
    def setUp(self):
        self.event = EventFactory(is_approved=True)
        self.source = AudioSourceFactory(
            event=self.event,
            status=AudioSource.READY,
            length=120,
            raw_file=SimpleUploadedFile("src.wav", b"WAV"),
            transcoded_file=SimpleUploadedFile("src.mp3", b"MP3-ORIG"),
        )

    @mock.patch("palanaeum.tasks.subprocess.run")
    @mock.patch("palanaeum.tasks.time.sleep")
    def test_missing_or_muted_snippet_returns_cleanly(self, mock_sleep, mock_run):
        with self.assertLogs("palanaeum.celery", level="ERROR"):
            create_snippet(999999)
        muted = SnippetFactory(source=self.source, beginning=0, length=10, muted=True)
        create_snippet(muted.pk)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_run.assert_not_called()

    @mock.patch("palanaeum.tasks.subprocess.run")
    @mock.patch("palanaeum.tasks.time.sleep")
    def test_create_snippet_skips_up_to_date_and_regenerates_outdated(self, mock_sleep, mock_run):
        temp_base = pathlib.Path(settings.MEDIA_ROOT).parent
        snippet_dir = pathlib.Path(settings.MEDIA_ROOT) / "snippets" / str(self.source.pk)
        snippet_dir.mkdir(parents=True, exist_ok=True)
        existing_file = snippet_dir / "10_20.mp3"
        existing_file.write_bytes(b"existing-snippet")

        rel_path = str(existing_file.relative_to(temp_base))
        snippet = SnippetFactory(source=self.source, beginning=10, length=20, file=rel_path)

        prev_cwd = os.getcwd()
        os.chdir(temp_base)
        self.addCleanup(os.chdir, prev_cwd)

        with override_settings(BASE_DIR=temp_base):
            # Up-to-date snippet file already on disk -> no ffmpeg call
            create_snippet(snippet.pk)
            mock_run.assert_not_called()

            # Change beginning/length -> old file unlinked and new snippet generated
            snippet.beginning = 15
            snippet.length = 25
            snippet.save()

            def fake_cut(cmd, **_kwargs):
                out_file = pathlib.Path(cmd[-1])
                out_file.parent.mkdir(parents=True, exist_ok=True)
                out_file.write_bytes(b"new-cut")

            mock_run.side_effect = fake_cut
            create_snippet(snippet.pk)

        mock_run.assert_called_once()
        self.assertFalse(existing_file.exists())
        snippet.refresh_from_db()
        expected_rel = str(pathlib.Path("media") / "snippets" / str(self.source.pk) / "15_25.mp3")
        self.assertEqual(snippet.file, expected_rel)
        self.assertTrue((temp_base / expected_rel).is_file())

    @mock.patch("palanaeum.tasks.subprocess.run")
    @mock.patch("palanaeum.tasks.time.sleep")
    def test_create_snippet_happy_path_from_scratch(self, _mock_sleep, mock_run):
        temp_base = pathlib.Path(settings.MEDIA_ROOT).parent
        snippet = SnippetFactory(source=self.source, beginning=5, length=12, file="")

        def fake_cut(cmd, **_kwargs):
            pathlib.Path(cmd[-1]).write_bytes(b"cut-audio")

        mock_run.side_effect = fake_cut
        with override_settings(BASE_DIR=temp_base):
            create_snippet(snippet.pk)

        snippet.refresh_from_db()
        self.assertEqual(snippet.file, f"media/snippets/{self.source.pk}/5_12.mp3")
        cmd = mock_run.call_args.args[0]
        self.assertEqual(cmd[:6], ["ffmpeg", "-y", "-ss", "5", "-i", self.source.transcoded_file.path])
        self.assertEqual(cmd[6:8], ["-t", "12"])

    @unittest.expectedFailure
    @mock.patch("palanaeum.tasks.subprocess.run")
    @mock.patch("palanaeum.tasks.time.sleep")
    def test_create_snippet_media_root_outside_base_dir_fails(self, _mock_sleep, mock_run):
        """
        Bug in palanaeum/tasks.py:132 — create_snippet computes
        `new_path.relative_to(settings.BASE_DIR)` unconditionally, raising
        ValueError whenever MEDIA_ROOT is located outside BASE_DIR.
        """
        snippet = SnippetFactory(source=self.source, beginning=1, length=2, file="")
        mock_run.side_effect = lambda cmd, **_kw: pathlib.Path(cmd[-1]).write_bytes(b"cut")
        create_snippet(snippet.pk)
        snippet.refresh_from_db()
        self.assertTrue(snippet.file)

    @mock.patch("palanaeum.tasks.subprocess.run")
    @mock.patch("palanaeum.tasks.time.sleep")
    def test_mute_snippet_edge_cases_and_happy_path(self, mock_sleep, mock_run):
        # Missing ID & unmuted snippet return cleanly
        with self.assertLogs("palanaeum.celery", level="ERROR"):
            mute_snippet(999999)
        unmuted = SnippetFactory(source=self.source, beginning=0, length=5, muted=False)
        mute_snippet(unmuted.pk)
        mock_run.assert_not_called()

        # Non-transcoded source returns cleanly with warning
        waiting_src = AudioSourceFactory(
            event=self.event,
            status=AudioSource.WAITING,
            length=60,
            transcoded_file=SimpleUploadedFile("waiting.mp3", b"W"),
        )
        waiting_snip = SnippetFactory(source=waiting_src, beginning=0, length=5, muted=True)
        with self.assertLogs("palanaeum.celery", level="WARNING"):
            mute_snippet(waiting_snip.pk)
        mock_run.assert_not_called()

        # Happy path WITH existing snippet.file
        temp_base = pathlib.Path(settings.MEDIA_ROOT).parent
        snip_dir = pathlib.Path(settings.MEDIA_ROOT) / "snippets" / str(self.source.pk)
        snip_dir.mkdir(parents=True, exist_ok=True)
        old_snip_file = snip_dir / "10_15.mp3"
        old_snip_file.write_bytes(b"old-snip")
        rel_snip = str(old_snip_file.relative_to(temp_base))
        muted_with_file = SnippetFactory(source=self.source, beginning=10, length=15, muted=True, file=rel_snip)

        def fake_mute(cmd):
            pathlib.Path(cmd[-1]).write_bytes(b"muted-v1")

        mock_run.side_effect = fake_mute
        with override_settings(BASE_DIR=temp_base):
            mute_snippet(muted_with_file.pk)

        cmd = mock_run.call_args.args[0]
        self.assertIn("volume=enable='between(t,10,25)':volume=0", cmd)
        self.assertEqual(pathlib.Path(self.source.transcoded_file.path).read_bytes(), b"muted-v1")
        self.assertEqual(stat.S_IMODE(os.stat(self.source.transcoded_file.path).st_mode), 0o644)
        self.assertFalse(old_snip_file.exists())
        muted_with_file.refresh_from_db()
        self.assertIsNone(muted_with_file.file)

        # Happy path WITHOUT snippet.file
        muted_no_file = SnippetFactory(source=self.source, beginning=20, length=5, muted=True, file=None)
        mock_run.side_effect = lambda cmd: pathlib.Path(cmd[-1]).write_bytes(b"muted-v2")
        with override_settings(BASE_DIR=temp_base):
            mute_snippet(muted_no_file.pk)
        self.assertEqual(pathlib.Path(self.source.transcoded_file.path).read_bytes(), b"muted-v2")
        self.assertEqual(mock_sleep.call_count, 5)


class BackupAndCloudUploadTaskTests(TestCase):
    def setUp(self):
        self.event = EventFactory(name="Backup Con", is_approved=True)

    def test_backup_palanaeum_writes_zip_with_dump_and_media(self):
        media_sample = pathlib.Path(settings.MEDIA_ROOT) / "nested" / "sample.txt"
        media_sample.parent.mkdir(parents=True, exist_ok=True)
        media_sample.write_text("backup-media-content")

        backup_palanaeum()

        expected_zip = pathlib.Path(settings.BACKUP_DIR) / f"{datetime.date.today():%Y-%m-%d}.zip"
        self.assertTrue(expected_zip.is_file())
        with zipfile.ZipFile(expected_zip, "r") as zf:
            names = set(zf.namelist())
            self.assertIn("dump.json", names)
            self.assertIn("media/nested/sample.txt", names)
            self.assertEqual(zf.read("media/nested/sample.txt"), b"backup-media-content")
            dump_records = json.loads(zf.read("dump.json").decode("utf-8"))
            self.assertTrue(
                any(
                    rec.get("model") == "palanaeum.event" and rec["fields"]["name"] == "Backup Con"
                    for rec in dump_records
                )
            )

    def test_upload_new_sources_to_cloud_noop_when_unconfigured(self):
        set_config("cloud_backend", "none")
        src = AudioSourceFactory(
            event=self.event,
            status=AudioSource.READY,
            is_approved=True,
            raw_file=SimpleUploadedFile("noop.wav", b"DATA"),
        )
        upload_new_sources_to_cloud()
        src.refresh_from_db()
        self.assertEqual(src.status, AudioSource.READY)

    @mock.patch("palanaeum.tasks.get_cloud_backend")
    def test_upload_new_sources_filters_deletes_or_keeps_raw_and_continues_on_error(self, mock_backend):
        s_ok_1 = AudioSourceFactory(
            event=self.event,
            status=AudioSource.READY,
            is_approved=True,
            raw_file=SimpleUploadedFile("ok1.wav", b"1"),
        )
        s_ok_2 = AudioSourceFactory(
            event=self.event,
            status=AudioSource.READY,
            is_approved=True,
            raw_file=SimpleUploadedFile("ok2.wav", b"2"),
        )
        s_fail = AudioSourceFactory(
            event=self.event,
            status=AudioSource.READY,
            is_approved=True,
            raw_file=SimpleUploadedFile("fail.wav", b"3"),
        )
        s_waiting = AudioSourceFactory(event=self.event, status=AudioSource.WAITING, is_approved=True)
        s_unapproved = AudioSourceFactory(event=self.event, status=AudioSource.READY, is_approved=False)

        cloud = mock.MagicMock()

        def fake_upload(source):
            if source.pk == s_fail.pk:
                raise PalanaeumCloudError("boom")

        cloud.upload_source.side_effect = fake_upload
        mock_backend.return_value = cloud

        # audio_keep_original_file=False deletes uploaded raw files while skipping failing & non-eligible sources
        set_config("audio_keep_original_file", False)
        with self.assertLogs("palanaeum.celery", level="ERROR"):
            upload_new_sources_to_cloud()

        uploaded_ids = {call.args[0].pk for call in cloud.upload_source.call_args_list}
        self.assertEqual(uploaded_ids, {s_ok_1.pk, s_ok_2.pk, s_fail.pk})
        self.assertNotIn(s_waiting.pk, uploaded_ids)
        self.assertNotIn(s_unapproved.pk, uploaded_ids)
        self.assertFalse(os.path.exists(s_ok_1.raw_file.path))
        self.assertFalse(os.path.exists(s_ok_2.raw_file.path))
        self.assertTrue(os.path.exists(s_fail.raw_file.path))

        # audio_keep_original_file=True preserves raw files after upload
        cloud.upload_source.reset_mock()
        cloud.upload_source.side_effect = None
        s_keep = AudioSourceFactory(
            event=self.event,
            status=AudioSource.READY,
            is_approved=True,
            raw_file=SimpleUploadedFile("keep.wav", b"KEEP"),
        )
        set_config("audio_keep_original_file", True)
        upload_new_sources_to_cloud()
        self.assertTrue(os.path.exists(s_keep.raw_file.path))
