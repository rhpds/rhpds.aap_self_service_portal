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
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Any, Dict, List, Set


def ver_key(v: str):
    parts = []
    for p in str(v).split("."):
        try:
            parts.append((0, int(p)))
        except ValueError:
            parts.append((1, p))
    return parts


def api_get(url: str, auth_header: str, ctx: ssl.SSLContext) -> Dict[str, Any]:
    req = urllib.request.Request(
        url, headers={"Authorization": auth_header, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    base = os.environ["HUB_BASE_URL"].rstrip("/")
    user = os.environ["HUB_USER"]
    password = os.environ["HUB_PASSWORD"]
    repo = os.environ["HUB_REPO"]
    keep = max(1, int(os.environ.get("KEEP_VERSIONS", "3")))
    verify = os.environ.get("VERIFY_SSL", "true").lower() not in ("0", "false", "no")

    import base64

    auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
    ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()

    by_name: Dict[str, Set[str]] = defaultdict(set)
    offset = 0
    page_size = 100
    while True:
        qs = urllib.parse.urlencode(
            {
                "repository_name": repo,
                "limit": page_size,
                "offset": offset,
            }
        )
        url = f"{base}/api/galaxy/v3/plugin/ansible/search/collection-versions/?{qs}"
        try:
            page = api_get(url, auth, ctx)
        except urllib.error.HTTPError as exc:
            print(json.dumps({"error": f"HTTP {exc.code}: {exc.reason}"}), file=sys.stderr)
            return 1
        data = page.get("data") or []
        for item in data:
            cv = item.get("collection_version") or {}
            ns, name, ver = cv.get("namespace"), cv.get("name"), cv.get("version")
            if ns and name and ver:
                by_name[f"{ns}.{name}"].add(ver)
        if len(data) < page_size:
            break
        offset += page_size
        if offset > 5000:
            break

    pins: List[Dict[str, str]] = []
    for full_name in sorted(by_name):
        versions = sorted(by_name[full_name], key=ver_key, reverse=True)[:keep]
        for ver in versions:
            pins.append({"name": full_name, "version": ver})

    lines = ["---", "collections:"]
    for p in pins:
        lines.append(f"  - name: {p['name']}")
        lines.append(f'    version: "=={p["version"]}"')

    print(
        json.dumps(
            {
                "count_collections": len(by_name),
                "count_pins": len(pins),
                "keep_versions": keep,
                "requirements_file": "\n".join(lines) + "\n",
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
