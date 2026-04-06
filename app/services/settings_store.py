"""Load/save application settings (delegates to split config repository)."""

from __future__ import annotations

from app.models.settings import AppSettings
from app.services.config_repository import load_merged_settings, save_merged_settings


def load_settings() -> AppSettings:
    return load_merged_settings()


def save_settings(settings: AppSettings) -> None:
    save_merged_settings(settings)
