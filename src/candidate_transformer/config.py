from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application settings loaded from environment variables and YAML."""

    model_config = SettingsConfigDict(env_prefix="CT_", extra="ignore")

    fuzzy_threshold: int = Field(default=88, ge=0, le=100)
    default_country: str = Field(default="IN")
    date_formats: list[str] = Field(
        default_factory=lambda: [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%B %d, %Y",
        ]
    )
    output_dir: str = Field(default="output")
    output_filename: str = Field(default="candidates_unified.jsonl")
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    projection_fields: list[str] | None = None
    field_rename: dict[str, str] = Field(default_factory=dict)
    canonical_path_mapping: dict[str, str] = Field(default_factory=dict)
    include_confidence: bool = False
    include_provenance: bool = False
    on_missing: Literal["null", "omit", "error"] = "null"


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load settings from a YAML file and then overlay environment variables."""

    resolved_path = Path(config_path) if config_path else None
    if resolved_path is None:
        default_path = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"
        resolved_path = default_path if default_path.exists() else None

    yaml_data: dict[str, Any] = {}
    if resolved_path is not None and resolved_path.exists():
        with resolved_path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
            if isinstance(loaded, dict):
                yaml_data = loaded

    env_data: dict[str, Any] = {}
    for field_name in AppConfig.model_fields:
        env_name = f"CT_{field_name.upper()}"
        if env_name in os.environ:
            env_data[field_name] = os.environ[env_name]

    combined = {**yaml_data, **env_data}
    return AppConfig(**combined)
