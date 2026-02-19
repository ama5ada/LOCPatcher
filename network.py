import gzip
import ssl
import urllib.error
import urllib.request
import zlib
from contextlib import contextmanager
from typing import Generator

from constants import REQUEST_TIMEOUT, USER_AGENT

class NetworkClient:
    """
    urllib wrapper with a single SSL context, timeout, and user agent

    Handles requesting a compressed patch list and a raw byte stream for pak files

    :param ssl_ctx:
        An SSLContext to use for all requests, can be used later to further secure patching
    """

    def __init__(self, ssl_ctx: ssl.SSLContext, timeout: int = REQUEST_TIMEOUT, user_agent: str = USER_AGENT) -> None:
        self._ctx = ssl_ctx
        self._timeout = timeout
        self._ua = user_agent


    @staticmethod
    def _check_status(url: str, resp) -> None:
        # Bad response
        if resp.status != 200:
            raise urllib.error.HTTPError(url, resp.status,
                                         f"Unexpected HTTP {resp.status} for {url}",
                                         resp.headers, None)


    def fetch_text(self, url: str) -> str:
        """
        GET url and return the decoded response body as a string

        Supports gzip/deflate
        """
        req = urllib.request.Request(url,
            headers={
                "User-Agent": self._ua,
                "Accept-Encoding": "gzip, deflate"
            })

        with urllib.request.urlopen(req, context=self._ctx, timeout=self._timeout) as resp:
            self._check_status(url, resp)
            return self._decode_response(resp)


    @staticmethod
    def _decode_response(resp) -> str:
        """
        Read raw bytes from response and decode to UTF-8.

        Handle gzip and deflate manually because Accept-Encoding request header is set explicitly.
        """
        raw = resp.read()
        encoding = resp.headers.get("Content-Encoding", "").lower()
        if encoding == "gzip":
            raw = gzip.decompress(raw)
        elif encoding == "deflate":
            raw = zlib.decompress(raw)
        return raw.decode("utf-8")


    @contextmanager
    def stream_binary(self, url: str) -> Generator:
        """
        Context manager that yields an open HTTP response for streaming.

        Request raw uncompressed bytes

        .pak files don't benefit from compression

        Content-Length is consistent with expected file size stored in the patch manifest.
        """
        req = urllib.request.Request(url, headers={"User-Agent": self._ua})

        with urllib.request.urlopen(req, context=self._ctx, timeout=self._timeout) as resp:
            self._check_status(url, resp)
            yield resp


def build_ssl_context() -> ssl.SSLContext:
    # May implement certs later to increase security
    return ssl.create_default_context()
