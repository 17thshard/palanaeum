import base64
import hashlib
import pathlib
import tempfile
import threading
import time
import unittest
from unittest import mock

import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from palanaeum.cloud import CloudBackend, get_cloud_backend
from palanaeum.cloud.b2 import B2
from palanaeum.cloud.exceptions import (
    AuthorizationError,
    ConfigurationError,
    DownloadError,
    FileNotStored,
    InvalidSourceError,
    UploadFailed,
)
from palanaeum.configuration import set_config
from palanaeum.models import AudioSource
from palanaeum.tests.factories import AudioSourceFactory, EventFactory


def _fake_response(status_code=200, json_data=None, content=b"", url="https://b2.example/"):
    resp = mock.MagicMock()
    resp.status_code = status_code
    resp.content = content
    resp.url = url
    resp.json.return_value = {} if json_data is None else json_data
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status_code}", response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


def _auth_ok_response(recommended=5_000_000, min_part=100):
    return _fake_response(
        200,
        json_data={
            "authorizationToken": "auth-tok",
            "apiUrl": "https://api.example",
            "downloadUrl": "https://dl.example",
            "accountId": "acct-1",
            "recommendedPartSize": recommended,
            "absoluteMinimumPartSize": min_part,
        },
    )


def _list_buckets_ok_response(bucket_id="bucket-1", bucket_name="palanaeum-audio"):
    return _fake_response(
        200,
        json_data={"buckets": [{"bucketId": bucket_id, "bucketName": bucket_name}]},
    )


class CloudFactoryAndBaseTests(TestCase):
    def setUp(self):
        self.event = EventFactory(name="Cloud Con", is_approved=True)

    def test_get_cloud_backend_none_unknown_and_b2(self):
        set_config("cloud_backend", "none")
        self.assertIsNone(get_cloud_backend())

        set_config("cloud_backend", "nonexistent")
        with self.assertRaises(KeyError):
            get_cloud_backend()

        set_config("cloud_backend", "b2")
        set_config("cloud_login", "app-key-id")
        set_config("cloud_passwd", "app-secret")
        set_config("cloud_b2_bucket_id", "bucket-1")
        with mock.patch("palanaeum.cloud.b2.requests.get", return_value=_auth_ok_response()), mock.patch(
            "palanaeum.cloud.b2.requests.post", return_value=_list_buckets_ok_response()
        ):
            backend = get_cloud_backend()
        self.assertIsInstance(backend, B2)
        self.assertEqual(backend.cloud_login, "app-key-id")
        self.assertEqual(backend.cloud_passwd, "app-secret")
        self.assertEqual(backend.bucket_name, "palanaeum-audio")

    @unittest.expectedFailure
    def test_get_cloud_backend_default_empty_string_returns_none(self):
        """
        Bug in palanaeum/configuration.py:26 & palanaeum/cloud/__init__.py:9,104 —
        `CONFIG_ENTRIES['cloud_backend']` defaults to `''` while `CLOUD_BACKENDS`
        only maps `'none'` -> None, causing `get_cloud_backend()` to raise KeyError
        out of the box when no cloud backend is configured.
        """
        set_config("cloud_backend", "")
        self.assertIsNone(get_cloud_backend())

    def test_cloud_backend_base_methods_and_upload_source_validation(self):
        class DummyBackend(CloudBackend):
            def __init__(self):
                super().__init__("u", "p")
                self.uploaded = []
                self.downloaded = []

            @classmethod
            def test_configuration(cls):
                return super().test_configuration()

            def get_file_info(self, audio_source):
                return super().get_file_info(audio_source)

            def upload_file(self, file_path, extra_params=None, file_name=""):
                self.uploaded.append((file_path, extra_params, file_name))
                return {"fileId": "fid-1"}

            def download_file(self, file_name, dest_path):
                self.downloaded.append((file_name, dest_path))
                return dest_path

            def get_download_url(self, audio_source):
                return super().get_download_url(audio_source)

        backend = DummyBackend()
        src = AudioSourceFactory(
            event=self.event,
            file_title="Brandon Talk",
            status=AudioSource.READY,
            length=60,
            raw_file=SimpleUploadedFile("cloud_src.wav", b"RAW-DATA"),
        )

        # Abstract methods raise NotImplementedError when calling super()
        with self.assertRaises(NotImplementedError):
            DummyBackend.test_configuration()
        with self.assertRaises(NotImplementedError):
            backend.get_file_info(src)
        with self.assertRaises(NotImplementedError):
            backend.get_download_url(src)
        with self.assertRaises(NotImplementedError):
            CloudBackend.upload_file(backend, "x")
        with self.assertRaises(NotImplementedError):
            CloudBackend.download_file(backend, "x", "y")

        # Invalid status
        src.status = AudioSource.WAITING
        with self.assertRaises(InvalidSourceError):
            backend.upload_source(src)

        # Already stored -> no-op
        src.status = AudioSource.STORED_IN_CLOUD
        backend.upload_source(src)
        self.assertEqual(backend.uploaded, [])

        # Ready -> uploads & marks STORED_IN_CLOUD
        src.status = AudioSource.READY
        backend.upload_source(src)
        src.refresh_from_db()
        self.assertEqual(src.status, AudioSource.STORED_IN_CLOUD)
        self.assertEqual(src.cloud_status, {"fileId": "fid-1"})
        self.assertEqual(
            backend.uploaded[0][1],
            {"Event-Id": str(self.event.pk), "Event-Name": "Cloud Con", "Title": "Brandon Talk"},
        )

        # download_source delegates to download_file
        backend.download_source(src)
        self.assertEqual(backend.downloaded, [(src.raw_file.name, src.raw_file.path)])

        # Missing file on disk raises FileNotFoundError
        pathlib.Path(src.raw_file.path).unlink()
        src.status = AudioSource.READY
        with self.assertRaises(FileNotFoundError):
            backend.upload_source(src)


class B2BackendTests(TestCase):
    def setUp(self):
        set_config("cloud_login", "b2-key")
        set_config("cloud_passwd", "b2-sec")
        set_config("cloud_b2_bucket_id", "bucket-1")
        self.event = EventFactory(name="Dragonsteel", is_approved=True)

    def _make_b2(self, recommended=100_000_000, min_part=100):
        with mock.patch(
            "palanaeum.cloud.b2.requests.get",
            return_value=_auth_ok_response(recommended=recommended, min_part=min_part),
        ) as m_get, mock.patch(
            "palanaeum.cloud.b2.requests.post",
            return_value=_list_buckets_ok_response(),
        ):
            b2 = B2("b2-key", "b2-sec")
        return b2, m_get

    def test_authorization_success_clamping_and_failures(self):
        b2, m_get = self._make_b2(recommended=100_000_000, min_part=100)
        expected_basic = base64.b64encode(b"b2-key:b2-sec").decode()
        self.assertEqual(m_get.call_args.kwargs["headers"]["Authorization"], f"Basic {expected_basic}")
        # Clamped down to MAX_PART_FILE_SIZE (20 MiB)
        self.assertEqual(b2.part_size, 20 * 1024 * 1024)

        # Clamped up to absoluteMinimumPartSize
        b2_small, _ = self._make_b2(recommended=5, min_part=250)
        self.assertEqual(b2_small.part_size, 250)

        # Non-200 auth raises AuthorizationError
        with mock.patch(
            "palanaeum.cloud.b2.requests.get",
            return_value=_fake_response(401, json_data={"code": "unauthorized"}),
        ):
            with self.assertRaises(AuthorizationError):
                B2("bad", "creds")

        # Missing bucket raises ConfigurationError
        with mock.patch("palanaeum.cloud.b2.requests.get", return_value=_auth_ok_response()), mock.patch(
            "palanaeum.cloud.b2.requests.post",
            return_value=_fake_response(200, json_data={"buckets": [{"bucketId": "other", "bucketName": "x"}]}),
        ):
            with self.assertRaises(ConfigurationError):
                B2("b2-key", "b2-sec")

    def test_api_call_get_file_info_and_url_helpers(self):
        b2, _ = self._make_b2()

        # _api_call error propagates HTTPError
        with mock.patch(
            "palanaeum.cloud.b2.requests.post",
            return_value=_fake_response(500, json_data={"message": "server error"}),
        ):
            with self.assertRaises(requests.HTTPError):
                b2._api_call("b2_some_endpoint")

        src = AudioSourceFactory(event=self.event, length=10, cloud_status={})
        with self.assertRaises(FileNotStored):
            b2.get_file_info(src)

        src.cloud_status = {"fileId": "f-123"}
        with mock.patch(
            "palanaeum.cloud.b2.requests.post",
            return_value=_fake_response(200, json_data={"fileId": "f-123", "contentLength": 999}),
        ) as m_post:
            info = b2.get_file_info(src)
        self.assertEqual(info["contentLength"], 999)
        self.assertEqual(m_post.call_args.kwargs["json"], {"fileId": "f-123"})

        # get_download_url
        src.raw_file = "sources/talk (1).wav"
        with mock.patch(
            "palanaeum.cloud.b2.requests.post",
            return_value=_fake_response(200, json_data={"authorizationToken": "dl-tok"}),
        ):
            url = b2.get_download_url(src)
        self.assertEqual(
            url,
            "https://dl.example/file/palanaeum-audio/sources/talk%20%281%29.wav?Authorization=dl-tok",
        )

        # test_configuration and _url_encode
        B2.test_configuration()
        self.assertEqual(B2._url_encode("a (b) żółć"), "a%20%28b%29%20%C5%BC%C3%B3%C5%82%C4%87")

    @unittest.expectedFailure
    def test_url_decode_returns_decoded_unicode(self):
        """
        Bug in palanaeum/cloud/b2.py:439 — B2._url_decode calls `.decode('utf-8')`
        on the `str` returned by `urllib.parse.unquote_plus`, raising AttributeError
        in Python 3.
        """
        self.assertEqual(B2._url_decode("a%20%28b%29%20%C5%BC%C3%B3%C5%82%C4%87"), "a (b) żółć")

    def test_upload_file_single_part_and_hash_multi_chunk(self):
        b2, _ = self._make_b2(recommended=100_000)
        payload = b"ABCD" * 1500  # 6000 bytes (> 4096 read buffer in _get_hash)
        expected_sha1 = hashlib.sha1(payload).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        self.addCleanup(lambda: pathlib.Path(tmp_path).unlink(missing_ok=True))

        def fake_post(url, data=None, json=None, headers=None):
            if url.endswith("b2_get_upload_url"):
                return _fake_response(200, json_data={"uploadUrl": "https://up.example/u1", "authorizationToken": "up-tok"})
            if url == "https://up.example/u1":
                self.assertEqual(data, payload)
                self.assertEqual(headers["X-Bz-Content-Sha1"], expected_sha1)
                self.assertEqual(headers["X-Bz-File-Name"], "dir/file%20%281%29.wav")
                self.assertEqual(headers["X-Bz-Info-Event-Name"], "Roshar%20Con")
                return _fake_response(200, json_data={"fileId": "b2-file-1"})
            raise AssertionError(f"Unexpected POST url={url}")

        with mock.patch("palanaeum.cloud.b2.requests.post", side_effect=fake_post):
            res = b2.upload_file(tmp_path, extra_params={"Event-Name": "Roshar Con"}, file_name="dir/file (1).wav")
        self.assertEqual(res, {"fileId": "b2-file-1"})

    @unittest.expectedFailure
    def test_upload_file_network_error_raises_upload_failed(self):
        """
        Bug in palanaeum/cloud/b2.py:164-169 — When `requests.post` raises
        `requests.RequestException`, the except handler executes
        `fail_reason = upload_request.json()` before `upload_request` is assigned,
        raising UnboundLocalError instead of retrying / raising UploadFailed.
        """
        b2, _ = self._make_b2(recommended=100_000)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"small")
            tmp_path = tmp.name
        self.addCleanup(lambda: pathlib.Path(tmp_path).unlink(missing_ok=True))

        def fake_post(url, **_kwargs):
            if url.endswith("b2_get_upload_url"):
                return _fake_response(200, json_data={"uploadUrl": "https://up.example/fail", "authorizationToken": "t"})
            raise requests.ConnectionError("network dropped")

        with mock.patch("palanaeum.cloud.b2.requests.post", side_effect=fake_post):
            with self.assertRaises(UploadFailed):
                b2.upload_file(tmp_path)

    def test_multipart_big_file_fresh_resume_stale_and_part_failure(self):
        b2, _ = self._make_b2(recommended=10, min_part=10)
        b2.part_size = 10

        # Small file dispatched to _upload_big_file redirects back to upload_file
        with tempfile.NamedTemporaryFile(delete=False) as small_tmp:
            small_tmp.write(b"tiny")
            small_path = small_tmp.name
        self.addCleanup(lambda: pathlib.Path(small_path).unlink(missing_ok=True))
        with mock.patch.object(b2, "upload_file", return_value={"fileId": "single"}) as m_single:
            self.assertEqual(b2._upload_big_file(small_path), {"fileId": "single"})
        m_single.assert_called_once()

        # 25-byte file -> 3 parts (10, 10, 5)
        big_data = b"0123456789abcdefghijKLMNO"
        part_hashes = [
            hashlib.sha1(big_data[0:10]).hexdigest(),
            hashlib.sha1(big_data[10:20]).hexdigest(),
            hashlib.sha1(big_data[20:25]).hexdigest(),
        ]
        big_hash = hashlib.sha1(big_data).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as big_tmp:
            big_tmp.write(big_data)
            big_path = big_tmp.name
        self.addCleanup(lambda: pathlib.Path(big_path).unlink(missing_ok=True))

        # Case 1: Fresh upload with expired-file pagination and stale-hash cleanup
        cancelled_ids = []
        list_calls = {"n": 0}
        now_ms = int(time.time() * 1000)
        lock = threading.Lock()
        uploaded_parts = {}
        finish_payload = {}

        def fake_post_fresh(url, data=None, json=None, headers=None):
            if url.endswith("b2_list_unfinished_large_files"):
                with lock:
                    list_calls["n"] += 1
                    n = list_calls["n"]
                # First pagination pair (from _cancel_expired_big_file_uploads), then pair (from _check_unfinished_files)
                if n in (1, 3):
                    return _fake_response(
                        200,
                        json_data={
                            "files": [
                                {
                                    "fileId": "old-expired",
                                    "fileName": "other.wav",
                                    "uploadTimestamp": now_ms - 48 * 3600 * 1000,
                                    "fileInfo": {"large_file_sha1": "old"},
                                }
                            ],
                            "nextFileId": "cursor-2",
                        },
                    )
                return _fake_response(
                    200,
                    json_data={
                        "files": [
                            {
                                "fileId": "stale-target",
                                "fileName": "big.wav",
                                "uploadTimestamp": now_ms,
                                "fileInfo": {"large_file_sha1": "different-hash"},
                            }
                        ],
                        "nextFileId": None,
                    },
                )
            if url.endswith("b2_cancel_large_file"):
                with lock:
                    cancelled_ids.append(json["fileId"])
                return _fake_response(200, json_data={"fileId": json["fileId"]})
            if url.endswith("b2_start_large_file"):
                return _fake_response(200, json_data={"fileId": "large-1"})
            if url.endswith("b2_get_upload_part_url"):
                return _fake_response(
                    200,
                    json_data={"uploadUrl": "https://up.example/part", "authorizationToken": "ptok"},
                )
            if url == "https://up.example/part":
                with lock:
                    uploaded_parts[int(headers["X-Bz-Part-Number"])] = data
                return _fake_response(200, json_data={"partNumber": headers["X-Bz-Part-Number"]})
            if url.endswith("b2_finish_large_file"):
                finish_payload.update(json)
                return _fake_response(200, json_data={"fileId": "large-1", "finished": True})
            raise AssertionError(f"Unexpected POST url={url}")

        with mock.patch("palanaeum.cloud.b2.requests.post", side_effect=fake_post_fresh):
            res = b2.upload_file(big_path, extra_params={"Event-Name": "Big"}, file_name="big.wav")

        self.assertTrue(res["finished"])
        self.assertIn("old-expired", cancelled_ids)
        self.assertIn("stale-target", cancelled_ids)
        self.assertEqual(uploaded_parts, {1: big_data[0:10], 2: big_data[10:20], 3: big_data[20:25]})
        self.assertEqual(finish_payload, {"fileId": "large-1", "partSha1Array": part_hashes})

        # Case 2: Resume matching large_file_sha1 with paginated b2_list_parts
        resumed_uploads = []
        finish_resume = {}

        def fake_post_resume(url, data=None, json=None, headers=None):
            if url.endswith("b2_list_unfinished_large_files"):
                return _fake_response(
                    200,
                    json_data={
                        "files": [
                            {
                                "fileId": "resume-id",
                                "fileName": big_path,
                                "uploadTimestamp": now_ms,
                                "fileInfo": {"large_file_sha1": big_hash},
                            }
                        ],
                        "nextFileId": None,
                    },
                )
            if url.endswith("b2_list_parts"):
                if "startPartNumber" not in json:
                    return _fake_response(
                        200,
                        json_data={
                            "parts": [{"partNumber": 1, "contentSha1": part_hashes[0]}],
                            "nextPartNumber": 2,
                        },
                    )
                return _fake_response(
                    200,
                    json_data={
                        "parts": [{"partNumber": 2, "contentSha1": part_hashes[1]}],
                        "nextPartNumber": None,
                    },
                )
            if url.endswith("b2_get_upload_part_url"):
                return _fake_response(
                    200,
                    json_data={"uploadUrl": "https://up.example/part", "authorizationToken": "ptok"},
                )
            if url == "https://up.example/part":
                resumed_uploads.append(int(headers["X-Bz-Part-Number"]))
                return _fake_response(200, json_data={"ok": True})
            if url.endswith("b2_finish_large_file"):
                finish_resume.update(json)
                return _fake_response(200, json_data={"fileId": "resume-id"})
            raise AssertionError(f"Unexpected POST url={url}")

        with mock.patch("palanaeum.cloud.b2.requests.post", side_effect=fake_post_resume):
            res_resume = b2.upload_file(big_path)
        self.assertEqual(res_resume, {"fileId": "resume-id"})
        self.assertEqual(resumed_uploads, [3])
        self.assertEqual(finish_resume["partSha1Array"], part_hashes)

        # Case 3: Part upload fails all retries -> returns {} without b2_finish_large_file
        def fake_post_part_fail(url, data=None, json=None, headers=None):
            if url.endswith("b2_list_unfinished_large_files"):
                return _fake_response(200, json_data={"files": [], "nextFileId": None})
            if url.endswith("b2_start_large_file"):
                return _fake_response(200, json_data={"fileId": "fail-id"})
            if url.endswith("b2_get_upload_part_url"):
                return _fake_response(
                    200,
                    json_data={"uploadUrl": "https://up.example/part", "authorizationToken": "ptok"},
                )
            if url == "https://up.example/part":
                if headers["X-Bz-Part-Number"] == "2":
                    raise requests.ConnectionError("part 2 dropped")
                return _fake_response(503, json_data={"error": "busy"})
            raise AssertionError(f"Unexpected POST url={url}")

        with mock.patch("palanaeum.cloud.b2.requests.post", side_effect=fake_post_part_fail):
            self.assertEqual(b2.upload_file(big_path, file_name="fail.wav"), {})

    def test_download_file_ranges_404_retry_and_error(self):
        b2, _ = self._make_b2(recommended=6, min_part=6)
        b2.part_size = 6

        with tempfile.NamedTemporaryFile(delete=False) as dst:
            dest_path = dst.name
        self.addCleanup(lambda: pathlib.Path(dest_path).unlink(missing_ok=True))

        # Chunked range download: two 404 retries test re-encoding fallback -> 206 -> 206 -> 416 EOF
        responses = [
            _fake_response(404, url="https://dl.example/file/palanaeum-audio/my%20file.wav"),
            _fake_response(404, url="https://dl.example/file/palanaeum-audio/my%20file.wav"),
            _fake_response(206, content=b"hello "),
            _fake_response(206, content=b"world"),
            _fake_response(416),
        ]
        ranges = []

        def fake_get(url, headers=None):
            ranges.append((url, headers["Range"]))
            return responses.pop(0)

        with mock.patch("palanaeum.cloud.b2.requests.get", side_effect=fake_get):
            out = b2.download_file("my file.wav", dest_path)

        self.assertEqual(out, dest_path)
        self.assertEqual(pathlib.Path(dest_path).read_bytes(), b"hello world")
        self.assertEqual(ranges[0][1], "bytes=0-5")
        self.assertIn("my%20file.wav", ranges[1][0])
        self.assertIn("my%2520file.wav", ranges[2][0])  # double-encoded after second 404
        self.assertEqual(ranges[3][1], "bytes=6-11")
        self.assertEqual(ranges[4][1], "bytes=12-17")

        # Status >= 400 (not 404/416) raises DownloadError
        with mock.patch("palanaeum.cloud.b2.requests.get", return_value=_fake_response(500)):
            with self.assertRaises(DownloadError):
                b2.download_file("bad.wav", dest_path)

        # Exhausting all 5 404 retries also raises DownloadError
        with mock.patch("palanaeum.cloud.b2.requests.get", return_value=_fake_response(404)):
            with self.assertRaises(DownloadError):
                b2.download_file("missing_forever.wav", dest_path)
