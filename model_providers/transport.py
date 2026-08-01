from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

@dataclass(frozen=True, slots=True)
class HttpJsonResponse:
    status_code: int
    headers: Mapping[str, str]
    body: Mapping[str, Any]

class JsonTransport(Protocol):
    def post_json(self, url: str, *, headers: Mapping[str, str],
                  body: Mapping[str, Any], timeout_seconds: float) -> HttpJsonResponse: ...

class UrllibJsonTransport:
    def post_json(self, url, *, headers, body, timeout_seconds):
        request = Request(
            url, data=json.dumps(dict(body), allow_nan=False).encode("utf-8"),
            headers={"Content-Type":"application/json", **dict(headers)}, method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read()
                response_headers = {k.lower(): v for k, v in response.headers.items()}
                status = int(response.status)
        except HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode(errors='replace')}") from exc
        except URLError as exc:
            raise RuntimeError(f"Transport failure: {exc.reason}") from exc
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict): raise RuntimeError("Expected JSON object.")
        return HttpJsonResponse(status, response_headers, value)
