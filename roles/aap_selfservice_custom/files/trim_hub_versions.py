#!/usr/bin/env python3
# SPDX-License-Identifier: MIT-0
"""Pin a Hub remote to the newest N versions of each collection, then print
JSON with requirements_file for Ansible to PATCH + mirror-sync.

Env:
  HUB_BASE_URL   gateway URL (no trailing slash)
  HUB_USER       admin username
  HUB_PASSWORD   admin password
  HUB_REPO       repository / remote name (e.g. rh-certified)
  KEEP_VERSIONS  integer, default 3
  VERIFY_SSL     true/false, default true
  COLLECTIONS    optional comma-separated ns.name allow-list. When set, only
                 those collections are queried (avoids paging the whole repo,
                 which 502s on heavy remotes like community / community.general).
  ERROR_FILE     optional path; on failure write a short reason here (no secrets)
                 so Ansible can surface it despite no_log on the command task.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


def ver_key(v: str):
    parts = []
    for p in str(v).split("."):
        try:
            parts.append((0, int(p)))
        except ValueError:
            parts.append((1, p))
    return parts


def write_error(msg: str) -> None:
    path = os.environ.get("ERROR_FILE", "").strip()
    if path:
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(msg.rstrip() + "\n")
        except OSError:
            pass
    print(json.dumps({"error": msg}), file=sys.stderr)


def api_get(
    url: str, auth_header: str, ctx: ssl.SSLContext, retries: int = 4
) -> Dict[str, Any]:
    last_exc: Optional[BaseException] = None
    for attempt in range(retries):
        req = urllib.request.Request(
            url, headers={"Authorization": auth_header, "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_exc = exc
            # Deep / large collection-version lists often 502/503 on Hub.
            if exc.code in (502, 503, 504) and attempt + 1 < retries:
                time.sleep(2 ** attempt)
                continue
            raise
        except (TimeoutError, urllib.error.URLError) as exc:
            last_exc = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"api_get failed after retries: {last_exc}")


def parse_collections(raw: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for part in raw.split(","):
        name = part.strip()
        if not name:
            continue
        if "." not in name:
            raise ValueError(f"collection '{name}' must be namespace.name")
        ns, coll = name.split(".", 1)
        if not ns or not coll:
            raise ValueError(f"collection '{name}' must be namespace.name")
        out.append((ns, coll))
    return out


def page_versions(
    base: str,
    auth: str,
    ctx: ssl.SSLContext,
    repo: str,
    *,
    namespace: Optional[str] = None,
    name: Optional[str] = None,
    is_highest: Optional[bool] = None,
    page_size: int = 100,
    max_offset: int = 2000,
) -> Iterable[Dict[str, Any]]:
    offset = 0
    while offset <= max_offset:
        params: Dict[str, Any] = {
            "repository_name": repo,
            "limit": page_size,
            "offset": offset,
        }
        if namespace:
            params["namespace"] = namespace
        if name:
            params["name"] = name
        if is_highest is not None:
            params["is_highest"] = "true" if is_highest else "false"
        qs = urllib.parse.urlencode(params)
        url = f"{base}/api/galaxy/v3/plugin/ansible/search/collection-versions/?{qs}"
        page = api_get(url, auth, ctx)
        data = page.get("data") or []
        for item in data:
            yield item
        if len(data) < page_size:
            break
        offset += page_size


def versions_for_collection(
    base: str,
    auth: str,
    ctx: ssl.SSLContext,
    repo: str,
    ns: str,
    name: str,
    keep: int,
) -> List[str]:
    """Return up to `keep` newest versions already in the Hub repo.

    Prefer a filtered list for this collection. If Hub 502s on the full
    list (common for community.general), fall back to is_highest only.
    """
    found: Set[str] = set()
    try:
        for item in page_versions(
            base, auth, ctx, repo, namespace=ns, name=name, max_offset=1500
        ):
            cv = item.get("collection_version") or {}
            ver = cv.get("version")
            if ver:
                found.add(ver)
    except urllib.error.HTTPError as exc:
        if exc.code not in (502, 503, 504):
            raise
        found.clear()

    if not found:
        # Fallback: only the marked-highest version in this repo.
        for item in page_versions(
            base,
            auth,
            ctx,
            repo,
            namespace=ns,
            name=name,
            is_highest=True,
            page_size=10,
            max_offset=0,
        ):
            cv = item.get("collection_version") or {}
            ver = cv.get("version")
            if ver:
                found.add(ver)

    return sorted(found, key=ver_key, reverse=True)[:keep]


def discover_collection_names(
    base: str, auth: str, ctx: ssl.SSLContext, repo: str
) -> List[Tuple[str, str]]:
    """One row per collection via is_highest (avoids paging every version)."""
    names: Dict[str, Tuple[str, str]] = {}
    for item in page_versions(
        base, auth, ctx, repo, is_highest=True, page_size=100, max_offset=5000
    ):
        cv = item.get("collection_version") or {}
        ns, name = cv.get("namespace"), cv.get("name")
        if ns and name:
            names[f"{ns}.{name}"] = (ns, name)
    return [names[k] for k in sorted(names)]


def main() -> int:
    try:
        base = os.environ["HUB_BASE_URL"].rstrip("/")
        user = os.environ["HUB_USER"]
        password = os.environ["HUB_PASSWORD"]
        repo = os.environ["HUB_REPO"]
        keep = max(1, int(os.environ.get("KEEP_VERSIONS", "3")))
        verify = os.environ.get("VERIFY_SSL", "true").lower() not in ("0", "false", "no")
        collections_raw = os.environ.get("COLLECTIONS", "").strip()
    except KeyError as exc:
        write_error(f"missing env {exc}")
        return 1

    import base64

    auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
    ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()

    try:
        if collections_raw:
            targets = parse_collections(collections_raw)
        else:
            targets = discover_collection_names(base, auth, ctx, repo)
    except Exception as exc:  # noqa: BLE001 - surface to Ansible
        write_error(f"discover collections failed for {repo}: {exc}")
        return 1

    by_name: Dict[str, List[str]] = defaultdict(list)
    for ns, name in targets:
        full = f"{ns}.{name}"
        try:
            by_name[full] = versions_for_collection(
                base, auth, ctx, repo, ns, name, keep
            )
        except Exception as exc:  # noqa: BLE001
            write_error(f"list versions failed for {repo}/{full}: {exc}")
            return 1

    pins: List[Dict[str, str]] = []
    for full_name in sorted(by_name):
        for ver in by_name[full_name]:
            pins.append({"name": full_name, "version": ver})

    lines = ["---", "collections:"]
    for p in pins:
        lines.append(f"  - name: {p['name']}")
        lines.append(f'    version: "=={p["version"]}"')

    print(
        json.dumps(
            {
                "count_collections": len([n for n, vs in by_name.items() if vs]),
                "count_pins": len(pins),
                "keep_versions": keep,
                "requirements_file": "\n".join(lines) + "\n",
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
