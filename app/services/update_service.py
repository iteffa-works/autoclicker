"""Check GitHub Releases for newer versions (stdlib only)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseInfo:
    tag_name: str
    html_url: str
    body: str


class UpdateService:
    def __init__(self, owner: str, repo: str, user_agent: str = "FlowaxyAutoclicker") -> None:
        self._owner = owner
        self._repo = repo
        self._user_agent = user_agent

    def fetch_latest(self, timeout_sec: float = 12.0) -> ReleaseInfo | None:
        url = f"https://api.github.com/repos/{self._owner}/{self._repo}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": self._user_agent, "Accept": "application/vnd.github+json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None
        tag = str(raw.get("tag_name", "") or "").strip()
        if not tag:
            return None
        return ReleaseInfo(
            tag_name=tag,
            html_url=str(raw.get("html_url", "") or ""),
            body=str(raw.get("body", "") or ""),
        )

    @staticmethod
    def is_newer_than(current_version: str, release_tag: str) -> bool:
        """Rough compare: strip leading v and compare as strings (works for semver x.y.z)."""
        a = current_version.strip().lstrip("vV")
        b = release_tag.strip().lstrip("vV")
        return a != b and b > a
