import base64
import hashlib
import logging
import multiprocessing
import os
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, Future

import requests

from palanaeum.cloud import CloudBackend, MAX_PART_FILE_SIZE
from palanaeum.cloud.exceptions import AuthorizationError, FileNotStored, \
    ConfigurationError, DownloadError, UploadFailed
from palanaeum.configuration import get_config
from palanaeum.models import AudioSource

logger = logging.getLogger('palanaeum.cloud.b2')


class B2(CloudBackend):
    AUTH_URL = 'https://api.backblazeb2.com/b2api/v1/b2_authorize_account'
    API_PREFIX = '/b2api/v1/'
    UPLOAD_RETRY_COUNT = 5
    EXPIRE_OLD_UPLOADS = 24

    def __init__(self, app_id, app_secret):
        super(B2, self).__init__(app_id, app_secret)
        self.auth_token = ''
        self.api_url = ''
        self.download_url = ''
        self.account_id = ''
        self.recommended_part_size = 0

        self._authorize()

        self.bucket_id = get_config('cloud_b2_bucket_id')
        self.bucket_name = ''

        if not self._check_bucket_exists(self.bucket_id):
            raise ConfigurationError

    def _api_call(self, endpoint, body=None):
        """
        Use this function to preform standard API calls.
        (No downloading or uploading files.)
        """
        address = self.api_url + self.API_PREFIX + endpoint

        if not body:
            body = {}

        headers = {'Authorization': self.auth_token}

        logger.debug("Requesting %s with body: %s and headers: %s", address, body, headers)
        request = requests.post(address, json=body, headers=headers)
        try:
            request.raise_for_status()
        except requests.RequestException:
            logger.exception("API call to %s with %s %s failed: %s", endpoint, headers, body, request.json())
            raise
        return request.json()

    def _authorize(self):
        """
        Perform the authorization with B2 service, exchanging application ID and secret for
        authorization token and additional usage information.
        """
        encoded_key = base64.b64encode((self.cloud_login + ':' + self.cloud_passwd).encode()).decode()

        auth_request = requests.get(self.AUTH_URL, headers={'Authorization': 'Basic ' + encoded_key})

        if auth_request.status_code != 200:
            logger.error("Authorization with B2 service failed. Reason: %s", auth_request.json())
            raise AuthorizationError()

        auth_response = auth_request.json()
        self.auth_token = auth_response['authorizationToken']
        self.api_url = auth_response['apiUrl']
        self.download_url = auth_response['downloadUrl']
        self.account_id = auth_response['accountId']
        self.part_size = int(auth_response['recommendedPartSize'])
        self.part_size = min(self.part_size, MAX_PART_FILE_SIZE)
        self.part_size = max(self.part_size, int(auth_response['absoluteMinimumPartSize']))
        logger.info("Successfully authorized with B2 service.")
        logger.info("Recommended part size: %s", auth_response['recommendedPartSize'])
        logger.info("Minimal part size: %s", auth_response['absoluteMinimumPartSize'])
        logger.info("Final part size: %d", self.part_size)
        return

    def _check_bucket_exists(self, bucket_id):
        """
        Check if bucket with given ID exists and save it's name if it does.
        """
        buckets_list = self._api_call('b2_list_buckets', body={'accountId': self.account_id})
        for bucket in buckets_list['buckets']:
            if bucket['bucketId'] == bucket_id:
                self.bucket_name = bucket['bucketName']
                return True
        return False

    def get_file_info(self, audio_source: AudioSource):
        """
        Return information stored about the file in B2 by fileId.
        """
        try:
            file_id = audio_source.cloud_status['fileId']
        except KeyError:
            raise FileNotStored("Audio source {} isn't stored in B2.".format(audio_source.id))

        return self._api_call('b2_get_file_info', {'fileId': file_id})

    @staticmethod
    def _get_hash(file_path):
        """
        Returns sha1 hash of the file in memory efficient way.
        """
        hasher = hashlib.sha1()
        with open(file_path, mode='rb') as opened_file:
            while opened_file.readable():
                chunk = opened_file.read(4096)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    def upload_file(self, file_path, extra_params=None, file_name=""):
        """
        Uploads a file to the cloud.
        """
        file_size = os.stat(file_path).st_size

        if file_size >= self.part_size:
            return self._upload_big_file(file_path, extra_params, file_name)

        file_hash = self._get_hash(file_path)
        fail_reason = {}

        for try_number in range(self.UPLOAD_RETRY_COUNT):
            upload_url_request = self._api_call(
                'b2_get_upload_url',
                {'bucketId': self.bucket_id}
            )
            upload_url = upload_url_request['uploadUrl']
            upload_token = upload_url_request['authorizationToken']
            logger.info("Received upload url: %s", upload_url)

            headers = {
                'Authorization': upload_token,
                'X-Bz-File-Name': self._url_encode(file_name or file_path),
                'Content-Type': 'b2/x-auto',
                'Content-Length': str(file_size),
                'X-Bz-Content-Sha1': str(file_hash),
            }

            if extra_params:
                for key, value in extra_params.items():
                    headers['X-Bz-Info-' + key] = self._url_encode(value)

            with open(file_path, mode='rb') as up_file:
                try:
                    upload_request = requests.post(
                        upload_url, data=up_file.read(), headers=headers)
                except requests.RequestException:
                    fail_reason = upload_request.json()
                    logger.warning(
                        "Failed to upload file %s: status %s, json: %s, %s",
                        file_path, upload_request.status_code, fail_reason
                    )
                    continue
            logger.info("File %s uploaded.", file_path)
            return upload_request.json()
        else:
            logger.error(
                "Failed to upload file %s in %d tries. Last reason: %s",
                file_path, self.UPLOAD_RETRY_COUNT, fail_reason
            )
            raise UploadFailed(str(fail_reason))

    def _check_unfinished_files(self, file_name, start_id=None):
        if start_id:
            files_req = self._api_call('b2_list_unfinished_large_files',
                                       {'bucketId': self.bucket_id, 'startId': start_id})
        else:
            files_req = self._api_call('b2_list_unfinished_large_files', {'bucketId': self.bucket_id})

        for file in files_req['files']:
            if file['fileName'] == file_name:
                return file

        if files_req['nextFileId'] is not None:
            return self._check_unfinished_files(file_name, start_id=files_req['nextFileId'])

        return None

    def _get_large_file_parts(self, file_id, part_num=None):
        if part_num:
            parts_req = self._api_call('b2_list_parts', {'fileId': file_id, 'startPartNumber': part_num})
        else:
            parts_req = self._api_call('b2_list_parts', {'fileId': file_id})

        yield from parts_req['parts']

        if parts_req['nextPartNumber'] is not None:
            yield from self._get_large_file_parts(file_id, parts_req['nextPartNumber'])

    def _upload_big_file(self, file_path, extra_params=None, file_name=""):
        """
        Upload file in multiple threads in many parts.
        """
        file_size = os.stat(file_path).st_size

        if file_size < self.part_size:
            return self.upload_file(file_path, extra_params)

        if not file_name:
            file_name = file_path

        self._cancel_expired_big_file_uploads()

        file_hash = self._get_hash(file_path)

        # Check if file is partially sent.
        unfinished_file = self._check_unfinished_files(file_name)
        parts_map = {}

        if unfinished_file is not None:
            if unfinished_file['fileInfo']['large_file_sha1'] != file_hash:
                logger.info("File %s changed since last upload attempt. Starting from scratch.", file_name)
                self._cancel_big_file(unfinished_file['fileId'])
                unfinished_file = None

        if unfinished_file is not None:
            # The file is unfinished and didn't completely upload last time.
            for part in self._get_large_file_parts(unfinished_file['fileId']):
                parts_map[part['partNumber']] = part
            file_id = unfinished_file['fileId']
            logger.info("Resuming upload of %s", file_name)
        else:
            if extra_params is None:
                extra_params = {}
            extra_params['large_file_sha1'] = file_hash
            start_file_request = self._api_call(
                'b2_start_large_file',
                {
                    'bucketId': self.bucket_id,
                    'fileName': file_name or file_path,
                    'contentType': 'b2/x-auto',
                    'fileInfo': extra_params
                }
            )
            file_id = start_file_request['fileId']
            logger.info("Starting to upload file %s", file_name)

        # Start thread pool to upload all parts
        hashes_list = []
        logger.info("Part size is %d, number of parts: %d", self.part_size, file_size//self.part_size + 1)
        with ThreadPoolExecutor(multiprocessing.cpu_count()) as pool:
            for num, part_start in enumerate(range(0, file_size, self.part_size), start=1):
                if num in parts_map:
                    hashes_list.append(parts_map[num]['contentSha1'])
                else:
                    hashes_list.append(
                        pool.submit(
                            self._send_piece_of_file,
                            file_id, num, file_path, part_start
                        )
                    )

        # When all pieces are sent, finish the file
        hashes_list = [promise.result() if isinstance(promise, Future) else promise for promise in hashes_list]

        if any(part_hash is None for part_hash in hashes_list):
            logger.error("Failed to upload file %s.", file_path)
            return {}

        return self._api_call('b2_finish_large_file', {'fileId': file_id, 'partSha1Array': hashes_list})

    def _send_piece_of_file(self, file_id, part_number, file_path, start):
        """
        Upload a single piece of a file. Return the piece's SHA1.
        """
        data = b''
        with open(file_path, mode='rb') as file:
            file.seek(start)
            while len(data) < self.part_size:
                part = file.read(self.part_size - len(data))
                if not part:
                    break
                data += part

        data_hash = hashlib.sha1()
        data_hash.update(data)
        data_hash = data_hash.hexdigest()
        last_response = {}

        for try_num in range(self.UPLOAD_RETRY_COUNT):
            logger.info("Starting to upload part %d of file %s (%d try)",
                        part_number, file_path, try_num + 1)
            try:
                url_request = self._api_call('b2_get_upload_part_url', {'fileId': file_id})

                upload_url = url_request['uploadUrl']
                token = url_request['authorizationToken']

                upload_req = requests.post(upload_url, data, headers={
                    'Authorization': token,
                    'X-Bz-Part-Number': str(part_number),
                    'Content-Length': str(len(data)),
                    'X-Bz-Content-Sha1': str(data_hash)
                })
            except requests.RequestException as err:
                logger.warning("Couldn't upload part %s of %s because: %s", part_number, file_path, str(err))
                continue

            last_response = upload_req.json()
            if upload_req.status_code == 200:
                logging.info("Successfully uploaded part %d of file %s",
                             part_number, file_path)
                return data_hash
        else:
            logging.error(
                "Failed to upload part %d of file %s. Reason: %s",
                part_number, file_path, last_response
            )
            return None

    def _cancel_expired_big_file_uploads(self, file_id=None):
        """
        Cancel all big file uploads older than EXPIRE_OLD_UPLOADS hours.
        This is an ugly solution to handle broken uploads, but I don't have time
        for anything better.
        """
        yesterday_ms = time.time()*1000 - self.EXPIRE_OLD_UPLOADS*60*60*1000
        if file_id:
            unfinished_uploads = self._api_call('b2_list_unfinished_large_files', {'bucketId': self.bucket_id,
                                                                                   'startFileId': file_id})
        else:
            unfinished_uploads = self._api_call('b2_list_unfinished_large_files', {'bucketId': self.bucket_id})

        for big_file in unfinished_uploads['files']:
            if big_file['uploadTimestamp'] < yesterday_ms:
                self._cancel_big_file(big_file['fileId'])

        if unfinished_uploads.get('nextFileId', None) is not None:
            self._cancel_expired_big_file_uploads(unfinished_uploads['nextFileId'])

        return

    def _cancel_big_file(self, file_id):
        self._api_call('b2_cancel_large_file', {'fileId': file_id})

    def download_file(self, file_name: str, dest_path: str):
        """
        Download a file by name.
        """
        logger.info("Trying to download %s to %s", file_name, dest_path)
        download_addr = urllib.parse.urljoin(self.download_url, 'file/{}/{}'.format(self.bucket_name,
                                                                                    self._url_encode(file_name)))
        headers = {
            'Authorization': self.auth_token
        }
        range_start = 0
        file_size = 0
        file_hash = hashlib.sha1()
        part_num = 1

        with open(dest_path, mode='wb') as out:
            while True:

                headers['Range'] = "bytes={}-{}".format(range_start, range_start + self.part_size - 1)
                range_start += self.part_size
                logger.info("Downloading file %s part %d", file_name, part_num)
                part_num += 1
                for _ in range(5):
                    part = requests.get(download_addr, headers=headers)
                    if part.status_code == 404:
                        # Try to resolve some file encoding errors from the past
                        file_name = self._url_encode(file_name)
                        download_addr = urllib.parse.urljoin(self.download_url, 'file/{}/{}'.format(self.bucket_name,
                                                                                                    file_name))
                        continue
                    else:
                        break

                if part.status_code == 416:
                    break  # We have the whole file

                if part.status_code >= 400:
                    logger.error("Error while downloading file %s from %s", file_name, part.url)
                    raise DownloadError("Downloading part of the file ended with status {}".format(part.status_code))

                file_size += out.write(part.content)
                file_hash.update(part.content)

        # if file_hash.hexdigest() != cloud_sha1:
        #     # TODO FIX the SHA1 verification!
        #     raise DownloadError("Incorrect SHA1 hash of downloaded file!")

        return dest_path

    def get_download_url(self, audio_source: AudioSource):
        """
        Return an URL that allows you to download the original audio file.
        """
        file_name = self._url_encode(str(audio_source.raw_file))
        download_auth_req = self._api_call('b2_get_download_authorization',
                                           {'bucketId': self.bucket_id, 'validDurationInSeconds': 24*60*60,
                                            'fileNamePrefix': self._url_encode(file_name)})

        auth = "?Authorization=" + download_auth_req['authorizationToken']

        return urllib.parse.urljoin(self.download_url, 'file/{}/{}'.format(self.bucket_name, file_name)) + auth

    @classmethod
    def test_configuration(cls):
        app_id = get_config('cloud_login')
        app_passwd = get_config('cloud_passwd')
        bucket_id = get_config('cloud_b2_bucket_id')
        # TODO: finish this!

    @staticmethod
    def _url_encode(s):
        """
        URL-encodes a unicode string to be sent to B2 in an HTTP header.
        """
        return urllib.parse.quote(str(s).encode('utf-8'))

    @staticmethod
    def _url_decode(s):
        """
        Decodes a Unicode string returned from B2 in an HTTP header.

        Returns a Python unicode string.
        """
        # Use str() to make sure that the input to unquote is a str, not
        # unicode, which ensures that the result is a str, which allows
        # the decoding to work properly.
        return urllib.parse.unquote_plus(str(s)).decode('utf-8')
