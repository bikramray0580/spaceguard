"""Fetch CelesTrak GP data, with a clearly labeled local fallback."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

from data_ingestion.models import NormalizedRecord
from data_ingestion.normalizer.normalize import ingest_path, ingest_text

CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php"
DEFAULT_GROUP = "STATIONS"
# TLE/3LE is substantially smaller than the JSON representation and keeps the
# exact line format required by SpaceGuard's current SGP4 propagation layer.
DEFAULT_FORMAT = "TLE"
DEFAULT_CONNECT_TIMEOUT = 30.0
DEFAULT_READ_TIMEOUT = 90.0
DEFAULT_MAX_RETRIES = 3

_NO_RETRY_STATUSES = frozenset({301, 400, 401, 403, 404})
_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_USER_AGENT = "SpaceGuard/1.0 (orbital-data-ingestion; educational use)"

_FALLBACK_CANDIDATES = (
    Path("shared/data/sample/celestrak_fallback.json"),
    Path("data/raw/celestrak_fallback.json"),
    Path(__file__).resolve().parents[2]
    / "shared"
    / "data"
    / "sample"
    / "celestrak_fallback.json",
)


class CelesTrakFetchError(Exception):
    """Raised when a live CelesTrak request cannot be completed."""


def fetch_celestrak_data(limit: int | None = None) -> list[dict]:
    """Download current GP records from CelesTrak.

    TLE/3LE is used by default because the backend currently propagates TLEs
    with SGP4. If the live request fails, a clearly labeled development sample
    is returned so existing ingestion workflows remain usable offline.
    """
    group = _env("CELESTRAK_GROUP", DEFAULT_GROUP).upper()
    fmt = _env("CELESTRAK_FORMAT", DEFAULT_FORMAT).upper()
    url = _env("CELESTRAK_BASE_URL", CELESTRAK_GP_URL)

    print("Fetching data from CelesTrak...")
    print("Connecting to CelesTrak...")

    try:
        records = _download_gp_data(url=url, group=group, fmt=fmt)
        live = True
    except CelesTrakFetchError as exc:
        print("CelesTrak unavailable.")
        print(f"Reason: {exc}")
        print("Using local sample data for development.")
        records = _load_fallback_sample()
        live = False

    if limit is not None:
        if limit < 1:
            return []
        records = records[:limit]

    source_label = "live CelesTrak" if live else "local development fallback"
    print(
        f"Fetched {len(records)} records from {source_label} "
        f"(GROUP={group}, FORMAT={fmt})."
    )

    return records


def load_celestrak_tles(
    source: str | Path,
    *,
    catalog: str = "gp",
) -> list[NormalizedRecord]:
    originator = "CelesTrak"

    if isinstance(source, Path) or _is_existing_path(source):
        return ingest_path(source, source="celestrak")

    return ingest_text(
        str(source),
        source="celestrak",
        originator=originator,
        raw_uri=f"celestrak:{catalog}",
        format_hint="tle",
    )


def _download_gp_data(
    *,
    url: str,
    group: str,
    fmt: str,
) -> list[dict]:
    params = {
        "GROUP": group,
        "FORMAT": fmt,
    }

    timeout = (
        _env_float("CELESTRAK_CONNECT_TIMEOUT", DEFAULT_CONNECT_TIMEOUT),
        _env_float("CELESTRAK_READ_TIMEOUT", DEFAULT_READ_TIMEOUT),
    )
    retries = _env_int("CELESTRAK_MAX_RETRIES", DEFAULT_MAX_RETRIES)

    response = _get_with_retries(
        url,
        params=params,
        timeout=timeout,
        retries=retries,
    )

    if fmt in {"TLE", "3LE"}:
        return _parse_tle_payload(response.text)

    return _parse_json_payload(response.text)


def _get_with_retries(
    url: str,
    *,
    params: dict[str, str],
    timeout: tuple[float, float],
    retries: int,
) -> requests.Response:
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "text/plain, application/json, */*",
    }

    attempts = max(1, retries)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
        except Timeout as exc:
            last_error = CelesTrakFetchError(
                f"HTTPSConnectionPool(host='celestrak.org', port=443): "
                f"connection/read timed out after {timeout} "
                f"on attempt {attempt}/{attempts}"
            )
            last_error.__cause__ = exc
        except ConnectionError as exc:
            last_error = CelesTrakFetchError(str(exc))
        except RequestException as exc:
            last_error = CelesTrakFetchError(str(exc))
        else:
            if response.status_code in _NO_RETRY_STATUSES:
                snippet = (response.text or "").strip().replace("\n", " ")[:300]
                raise CelesTrakFetchError(
                    f"HTTP {response.status_code} from CelesTrak. {snippet}".strip()
                )

            if response.status_code in _RETRY_STATUSES:
                last_error = CelesTrakFetchError(
                    f"HTTP {response.status_code} from CelesTrak "
                    f"on attempt {attempt}/{attempts}"
                )
            elif response.status_code != 200:
                snippet = (response.text or "").strip().replace("\n", " ")[:300]
                raise CelesTrakFetchError(
                    f"HTTP {response.status_code} from CelesTrak. {snippet}".strip()
                )
            else:
                return response

        if attempt < attempts:
            wait_s = 2 ** (attempt - 1)
            print(
                f"Attempt {attempt}/{attempts} failed ({last_error}). "
                f"Retrying in {wait_s}s..."
            )
            time.sleep(wait_s)
            continue

        raise last_error or CelesTrakFetchError("CelesTrak request failed")

    raise CelesTrakFetchError("CelesTrak request failed")


def _parse_tle_payload(text: str) -> list[dict]:
    """Parse CelesTrak's 3LE/TLE response into the fields SpaceGuard uses."""
    lines = [line.rstrip() for line in (text or "").splitlines() if line.strip()]
    records: list[dict] = []
    index = 0

    while index + 2 < len(lines):
        name = lines[index].strip()
        line1 = lines[index + 1].strip()
        line2 = lines[index + 2].strip()

        if line1.startswith("1 ") and line2.startswith("2 "):
            try:
                object_id = line1[2:7].strip()
                epoch = line1[18:32].strip()
            except IndexError:
                object_id = ""
                epoch = ""

            if object_id and len(line1) >= 69 and len(line2) >= 69:
                records.append(
                    {
                        "OBJECT_NAME": name,
                        "NORAD_CAT_ID": object_id,
                        "TLE_LINE1": line1,
                        "TLE_LINE2": line2,
                        "EPOCH": epoch,
                    }
                )
            index += 3
            continue

        # Be tolerant of a 2LE payload accidentally being requested.
        if line1.startswith("1 ") and line2.startswith("2 "):
            index += 2
        else:
            index += 1

    if not records:
        raise CelesTrakFetchError("CelesTrak returned no usable TLE records")

    return records


def _parse_json_payload(text: str) -> list[dict]:
    if not text or not str(text).strip():
        raise CelesTrakFetchError("CelesTrak returned an empty response")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CelesTrakFetchError(
            f"CelesTrak returned malformed JSON: {exc}"
        ) from exc

    if isinstance(payload, dict):
        payload = [payload]

    if not isinstance(payload, list):
        raise CelesTrakFetchError("CelesTrak JSON must be a list of GP records")

    records = [item for item in payload if isinstance(item, dict)]
    if not records:
        raise CelesTrakFetchError("CelesTrak returned zero usable GP records")

    return records


def _load_fallback_sample() -> list[dict]:
    for path in _FALLBACK_CANDIDATES:
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
            records = [item for item in payload if isinstance(item, dict)]

            for item in records:
                item["SOURCE"] = "local_fallback"
                item["SOURCE_NOTE"] = (
                    "development fallback; not live CelesTrak data"
                )

            if records:
                return records
            break

    raise CelesTrakFetchError(
        "CelesTrak is unavailable and no local sample file was found at "
        "shared/data/sample/celestrak_fallback.json"
    )


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _is_existing_path(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return Path(value).is_file()
    except OSError:
        return False
