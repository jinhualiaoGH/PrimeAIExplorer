from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping

from .base import ProviderError


@dataclass(frozen=True)
class JsonHttpResponse:
    status_code: int
    headers: Mapping[str, str]
    body: dict[str, Any]


class JsonHttpTransport:
    def post_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        payload: Mapping[str, Any],
        timeout_seconds: float,
        provider: str,
    ) -> JsonHttpResponse:
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=encoded,
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                body = json.loads(raw) if raw else {}
                return JsonHttpResponse(
                    status_code=response.status,
                    headers=dict(response.headers.items()),
                    body=body,
                )
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            retryable = exc.code in {408, 409, 429} or exc.code >= 500
            raise ProviderError(
                f"HTTP {exc.code}: {raw[:1000]}",
                provider=provider,
                status_code=exc.code,
                retryable=retryable,
            ) from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise ProviderError(
                f"Transport failure: {exc}",
                provider=provider,
                retryable=True,
            ) from exc
