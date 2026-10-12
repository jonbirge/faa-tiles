"""Downloading the chart series the FAA does not publish.

    python scripts/fetch_charts.py SERIES        (this is what runs these)

The FAA's series all download one way -- an edition folder of zips -- and
``fetch_charts.py`` does that itself. Everyone else publishes differently, and
each way of publishing is one function here, chosen by a series' ``fetcher``:

``links``
    An index page is read for links matching the series' ``link_pattern``. The
    pattern names a ``sheet`` and may name a ``date`` or ``year``; the latest of
    each sheet is downloaded and kept under the *sheet's* name. Publishers put
    the edition in the file name (Spain), or a random media id in the path
    (Denmark), so the URL changes with every edition while the sheet does not --
    and the reviewed map-area manifest has to go on naming the same file. A
    link to a zip is opened and the raster inside it kept.
``urls``
    The files named in the series, as they are.
``ofm``
    open flightmaps publishes finished Web Mercator tiles, a zip a region. The
    tiles wanted are fetched out of each zip and assembled into one raster a
    region (``fetch_ofm.py``).

Every fetcher is conditional: ``fetched.json`` in the series directory records
the URL, length and Last-Modified each file came from, and a file whose record
still matches the server is not downloaded again. Requests identify themselves
and, where a series asks (``fetch_delay``), wait between files.

Standard library only, except ``ofm``, which decodes and writes rasters.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urljoin, urlparse

# Honest about what is asking. Some hosts serve a bot challenge to anything
# that claims to be a browser and the real file to anything that does not.
USER_AGENT = "faa-tiles/1.0 (chart tiling pipeline; +https://github.com/jonbirge/faa-tiles)"

ATTEMPTS = 3
TIMEOUT_S = 120
CHUNK = 1 << 20
RECORD = "fetched.json"

HREF = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
# Links that appear in a page's scripts or data rather than in an attribute.
QUOTED = re.compile(r"""["']([^"'\s<>]+\.(?:tif|tiff|zip|pdf))["']""", re.IGNORECASE)


def request(url: str, *, method: str = "GET", headers: dict | None = None):
    merged = {"User-Agent": USER_AGENT, **(headers or {})}
    return urllib.request.urlopen(
        urllib.request.Request(url, method=method, headers=merged), timeout=TIMEOUT_S)


def read_text(url: str) -> str:
    with request(url) as response:
        return response.read().decode("utf-8", "replace")


def remote_state(url: str) -> dict:
    """What the server says about a file, without downloading it: its length
    and Last-Modified. Falls back to a one-byte ranged GET where HEAD is
    refused, which some chart servers do."""
    try:
        with request(url, method="HEAD") as response:
            headers = response.headers
            length = headers.get("Content-Length")
    except urllib.error.HTTPError as exc:
        if exc.code not in (403, 404, 405, 501):
            raise
        with request(url, headers={"Range": "bytes=0-0"}) as response:
            headers = response.headers
            content_range = headers.get("Content-Range", "")
            length = content_range.rsplit("/", 1)[-1] if "/" in content_range else None
    return {
        "length": int(length) if length and str(length).isdigit() else None,
        "last_modified": headers.get("Last-Modified"),
    }


def download(url: str, dest: Path) -> int:
    """Stream ``url`` to ``dest`` through a ``.part`` file, retrying on failure."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with request(url) as response, open(part, "wb") as handle:
                expected = response.headers.get("Content-Length")
                shutil.copyfileobj(response, handle, CHUNK)
                size = handle.tell()
            if expected is not None and size != int(expected):
                raise OSError(f"short read: {size} of {expected} bytes")
            os.replace(part, dest)
            return size
        except OSError as exc:      # URLError and socket timeouts are OSErrors
            part.unlink(missing_ok=True)
            if attempt == ATTEMPTS:
                raise
            print(f"  retry {attempt}/{ATTEMPTS - 1} {url}: {exc}", file=sys.stderr, flush=True)
            time.sleep(5 * attempt)
    raise AssertionError("unreachable")


# -- the record -------------------------------------------------------------

def load_record(directory: Path) -> dict:
    path = directory / RECORD
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def save_record(directory: Path, record: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / RECORD).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n",
                                    encoding="utf-8", newline="\n")


def is_current(directory: Path, name: str, url: str, state: dict, record: dict) -> bool:
    """Whether ``name`` on disk is the file the server is offering now."""
    held = record.get(name)
    if not held or not (directory / name).is_file():
        return False
    return (held.get("url") == url
            and held.get("length") == state["length"]
            and held.get("last_modified") == state["last_modified"])


# -- links ------------------------------------------------------------------

def page_links(url: str, html: str) -> list[str]:
    """Every link on a page, absolute, in the order first seen."""
    seen, out = set(), []
    for found in HREF.findall(html) + QUOTED.findall(html):
        # Percent-encoded, where the page wrote a space or an accent plainly:
        # Latvia's charts are in a folder called "VFR charts".
        absolute = quote(urljoin(url, found.replace("\\/", "/")), safe=":/?&=%#+,;@~!$'()*")
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


MONTHS = {name: number for number, name in enumerate(
    ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}


def edition_date(text: str) -> dt.date | None:
    """The date an edition is named for, as publishers write them: 20260903,
    2026_06_11, 03SEP2026, or a bare year. None if it is none of those."""
    digits = re.sub(r"[-_./ ]", "", text)
    try:
        if re.fullmatch(r"\d{8}", digits):
            return dt.date(int(digits[:4]), int(digits[4:6]), int(digits[6:]))
        named = re.fullmatch(r"(\d{1,2})([A-Za-z]{3})(\d{4})", digits)
        if named and named.group(2).upper() in MONTHS:
            return dt.date(int(named.group(3)), MONTHS[named.group(2).upper()],
                           int(named.group(1)))
        if re.fullmatch(r"\d{4}", digits):
            return dt.date(int(digits), 1, 1)
    except ValueError:
        pass
    return None


def latest_by_sheet(links: list[str], pattern: str,
                    today: dt.date | None = None) -> dict[str, tuple[str, str]]:
    """``{sheet: (edition, url)}``: the current matching link for each sheet.

    ``pattern`` is matched against the whole URL, percent-decoded. Its ``sheet``
    group names the sheet; a ``date`` or ``year`` group, if it has one, orders
    the editions, and without one the last link on the page wins.

    The current edition is the latest that is not in the future. Publishers
    post the next one before it takes effect, as the FAA does: Latvia's page
    carries the chart effective 29 October beside the one effective now. If
    every edition of a sheet is in the future, the earliest is taken.
    """
    compiled = re.compile(pattern, re.IGNORECASE)
    if "sheet" not in compiled.groupindex:
        raise ValueError("a link pattern must name a 'sheet' group")
    ordered = next((g for g in ("date", "year") if g in compiled.groupindex), None)
    today = today or dt.date.today()
    found: dict[str, list] = {}
    for position, link in enumerate(links):
        match = compiled.fullmatch(unquote(link))
        if not match:
            continue
        edition = match.group(ordered) if ordered else ""
        when = edition_date(edition) if edition else None
        found.setdefault(match.group("sheet"), []).append((when, position, edition, link))
    best = {}
    for sheet, editions in found.items():
        dated = [e for e in editions if e[0] is not None]
        current = [e for e in dated if e[0] <= today]
        if current:
            chosen = max(current, key=lambda e: (e[0], e[1]))
        elif dated:
            chosen = min(dated, key=lambda e: (e[0], e[1]))
        else:
            chosen = max(editions, key=lambda e: (e[2], e[1]))
        best[sheet] = (chosen[2], chosen[3])
    return best


def raster_from_zip(zip_path: Path, dest: Path) -> None:
    """Copy the one raster a zip holds to ``dest``."""
    with zipfile.ZipFile(zip_path) as archive:
        rasters = [info for info in archive.infolist()
                   if not info.is_dir() and info.filename.lower().endswith((".tif", ".tiff"))]
        if len(rasters) != 1:
            names = ", ".join(PurePosixPath(i.filename).name for i in rasters) or "none"
            raise RuntimeError(f"expected one raster in {zip_path.name}, found {names}")
        part = dest.with_name(dest.name + ".part")
        with archive.open(rasters[0]) as source, open(part, "wb") as target:
            shutil.copyfileobj(source, target, CHUNK)
        os.replace(part, dest)


def fetch_files(chart_series, out: Path, wanted: dict[str, tuple[str, str]],
                list_only: bool) -> int:
    """Download ``{file name: (edition, url)}`` into ``out``, skipping what is
    already current."""
    if not wanted:
        print(f"nothing to fetch for {chart_series.name}", file=sys.stderr)
        return 1
    print(f"{chart_series.title}: {len(wanted)} file{'s' if len(wanted) != 1 else ''} -> {out}",
          flush=True)
    if list_only:
        for name, (edition, url) in sorted(wanted.items()):
            print(f"  {name}  {edition}  {url}")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    record = load_record(out)
    failed = []
    started = time.monotonic()
    fetched = 0
    for name, (edition, url) in sorted(wanted.items()):
        try:
            state = remote_state(url)
            if is_current(out, name, url, state, record):
                print(f"ok   {name}: current ({edition or state['last_modified']})", flush=True)
                continue
            if fetched and chart_series.fetch_delay:
                time.sleep(chart_series.fetch_delay)
            t0 = time.monotonic()
            if urlparse(url).path.lower().endswith(".zip"):
                handle, temporary = tempfile.mkstemp(prefix=".", suffix=".zip", dir=out)
                os.close(handle)
                try:
                    download(url, Path(temporary))
                    raster_from_zip(Path(temporary), out / name)
                finally:
                    Path(temporary).unlink(missing_ok=True)
            else:
                download(url, out / name)
            fetched += 1
            record[name] = {"url": url, "edition": edition, **state,
                            "fetched": dt.date.today().isoformat()}
            save_record(out, record)
            print(f"ok   {name} ({(out / name).stat().st_size / 1e6:.0f} MB, "
                  f"{time.monotonic() - t0:.0f}s)", flush=True)
        except Exception as exc:
            failed.append(name)
            print(f"FAIL {name}: {exc}", file=sys.stderr, flush=True)
    print(f"done in {time.monotonic() - started:.0f}s: {len(wanted) - len(failed)} ok, "
          f"{len(failed)} failed")
    if failed:
        print("failed: " + ", ".join(failed), file=sys.stderr)
    return 1 if failed else 0


def fetch_links(chart_series, out: Path, list_only: bool) -> int:
    links = page_links(chart_series.index_url, read_text(chart_series.index_url))
    found = latest_by_sheet(links, chart_series.link_pattern)
    # A scan is kept as the scan it is, and a PDF as the PDF it is, in the
    # directory render_pdfs.py reads; each becomes <sheet>.tif later. Either
    # way the series' pattern is for that name.
    if chart_series.geopdf:
        out = chart_series.pdf_directory if out == chart_series.directory else out / "pdf"
        wanted = {f"{sheet}.pdf": item for sheet, item in found.items()}
    else:
        suffix = chart_series.scan_suffix or ".tif"
        wanted = {f"{sheet}{suffix}": item for sheet, item in found.items()
                  if chart_series.wants_tif(f"{sheet}.tif")}
    if not wanted:
        print(f"no link on {chart_series.index_url} matches the series' pattern; "
              "the publisher may have changed its page", file=sys.stderr)
        return 1
    return fetch_files(chart_series, out, wanted, list_only)


def fetch_urls(chart_series, out: Path, list_only: bool) -> int:
    wanted = {PurePosixPath(urlparse(url).path).name: ("", url) for url in chart_series.urls}
    return fetch_files(chart_series, out, wanted, list_only)


def fetch_ofm(chart_series, out: Path, list_only: bool) -> int:
    from fetch_ofm import fetch       # decodes and writes rasters; imported on use
    return fetch(chart_series, out, list_only)


FETCHERS = {"links": fetch_links, "urls": fetch_urls, "ofm": fetch_ofm}


def run(chart_series, out: Path, list_only: bool = False) -> int:
    try:
        fetcher = FETCHERS[chart_series.fetcher]
    except KeyError:
        raise SystemExit(f"{chart_series.name} names an unknown fetcher "
                         f"{chart_series.fetcher!r}") from None
    return fetcher(chart_series, out, list_only)
