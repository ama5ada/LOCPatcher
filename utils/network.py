import gzip
import http.client
import ssl
import urllib.error
import urllib.request
import zlib
from contextlib import contextmanager
from typing import Iterator
from urllib.parse import urlparse

from config.constants import REQUEST_TIMEOUT, USER_AGENT, REMOTE_HOST, REMOTE_PATCH_LIST


class NetworkClient:
    """
    urllib wrapper with a single SSL context, timeout, and user agent

    Handles requesting a compressed patch list and a raw byte stream for pak files

    :param ssl_ctx:
        An SSLContext to use for all requests, can be used later to further secure patching
    """

    def __init__(
            self,
            ssl_ctx: ssl.SSLContext,
            timeout: int = REQUEST_TIMEOUT,
            user_agent: str = USER_AGENT,
            remote_host: str = REMOTE_HOST,
            patch_list: str = REMOTE_PATCH_LIST
    ) -> None:
        self._ctx = ssl_ctx
        self._timeout = timeout
        self._ua = user_agent

        host_parsed = urlparse(remote_host)
        self._host = host_parsed.netloc
        self._base_download_path = host_parsed.path

        self._patch_list = patch_list


    @staticmethod
    def _check_status(url: str, resp: http.client.HTTPResponse) -> None:
        # Bad response
        if resp.status != 200:
            raise urllib.error.HTTPError(url, resp.status,
                                         f"Unexpected HTTP {resp.status} for {url}",
                                         resp.headers, None)


    def fetch_text(self) -> str:
        """
        GET url and return the decoded response body as a string

        Supports gzip/deflate

        Uses a one-off connection rather than opening a stream
        """
        req = urllib.request.Request(self._patch_list,
            headers={
                "User-Agent": self._ua,
                "Accept-Encoding": "gzip, deflate"
            })

        with urllib.request.urlopen(req, context=self._ctx, timeout=self._timeout) as resp:
            return self._decode_response(resp)


    @staticmethod
    def _decode_response(resp: http.client.HTTPResponse) -> str:
        """
        Read raw bytes from response and decode to UTF-8.

        Handle gzip and deflate manually because Accept-Encoding request header is set explicitly.
        """
        raw: bytes = resp.read()
        encoding = resp.headers.get("Content-Encoding", "").lower()
        if encoding == "gzip":
            raw = gzip.decompress(raw)
        elif encoding == "deflate":
            raw = zlib.decompress(raw)
        return raw.decode("utf-8")


    def open_connection(self) -> http.client.HTTPSConnection:
        return http.client.HTTPSConnection(self._host, context=self._ctx, timeout=self._timeout)

    @contextmanager
    def stream_binary(self, conn: http.client.HTTPSConnection, file_name: str) -> Iterator[http.client.HTTPResponse]:
        """
        Context manager that yields an open HTTP response for streaming.

        Implementing Context Manager ensures the HTTP connection is automatically closed, meaning the consuming code is
        not concerned with managing connection cleanup manually if an exception is raised.

        Request raw uncompressed bytes
        .pak files don't benefit from compression
        Content-Length is consistent with expected file size stored in the patch manifest.
        """
        file_url = self._base_download_path.rstrip("/") + "/" + file_name.lstrip("/")
        try:
            conn.request("GET", file_url, headers={"User-Agent": self._ua})
            resp = conn.getresponse()
        except http.client.RemoteDisconnected:
            conn.connect()
            conn.request("GET", file_url, headers={"User-Agent": self._ua})
            resp = conn.getresponse()

        self._check_status(file_url, resp)

        try:
            yield resp
        except BaseException:
            conn.close()
            raise
        finally:
            resp.close()

def build_ssl_context() -> ssl.SSLContext:
    # May implement certs later to increase security
    return ssl.create_default_context()
