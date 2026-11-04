"""Check every citation URL used in the diagrams (the `link` field of elements).

    python tools/check_links.py            # all diagrams
    python tools/check_links.py agent-service-overview

Reports non-2xx responses and tiny pages. Results are cached in tools/.link-cache.json (delete to recheck).
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "tools" / ".link-cache.json"
UA = "Mozilla/5.0 (foundry-explainers link checker)"


def check(url: str) -> tuple[str, int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read(4096)
            return url, r.status, r.geturl() if r.geturl() != url else ""
    except urllib.error.HTTPError as e:
        return url, e.code, ""
    except Exception as e:  # noqa: BLE001
        return url, 0, str(e)[:80]


def main(argv: list[str]) -> int:
    ids = [a for a in argv if not a.startswith("-")]
    files = [ROOT / "diagrams" / f"{i}.excalidraw" for i in ids] if ids else sorted(
        p for p in (ROOT / "diagrams").glob("*.excalidraw") if not p.name.startswith("_"))
    urls: dict[str, set[str]] = defaultdict(set)
    for f in files:
        for e in json.loads(f.read_text(encoding="utf-8"))["elements"]:
            link = e.get("link")
            if link and re.match(r"https?://", link):
                urls[link].add(f.stem)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [u for u in urls if u not in cache]
    print(f"{len(urls)} unique URLs ({len(todo)} to check)")
    with cf.ThreadPoolExecutor(6) as ex:
        for url, status, note in ex.map(check, todo):
            cache[url] = [status, note]
    CACHE.write_text(json.dumps(cache, indent=0))
    bad = [(u, cache[u]) for u in urls if not (200 <= cache[u][0] < 300)]
    for u, (status, note) in sorted(bad):
        print(f"  [{status}] {u}  {note}  <- {', '.join(sorted(urls[u]))}")
    print(f"OK: {len(urls) - len(bad)}   problems: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
