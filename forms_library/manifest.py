from __future__ import annotations

from pathlib import Path

import yaml

from forms_library.models import Agency, Form, Manifest


class ManifestError(Exception):
    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


def load_manifest(path: Path) -> Manifest:
    if not path.exists():
        raise ManifestError(f"Manifest not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ManifestError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(raw, dict):
        raise ManifestError(f"Manifest {path} must be a YAML mapping")

    errors: list[str] = []

    forms_data = raw.get("forms", [])
    if not isinstance(forms_data, list):
        raise ManifestError(f"Manifest {path} must contain a 'forms' list")

    if not forms_data:
        errors.append("Manifest contains no forms")

    forms: list[Form] = []
    for i, item in enumerate(forms_data):
        if not isinstance(item, dict):
            errors.append(f"Form {i}: must be a mapping, got {type(item).__name__}")
            continue
        try:
            form = Form.model_validate(item)
            forms.append(form)
        except Exception as e:
            errors.append(f"Form {i}: {e}")

    agencies_data = raw.get("agencies", [])
    agencies: list[Agency] = []
    if isinstance(agencies_data, list):
        for i, item in enumerate(agencies_data):
            if not isinstance(item, dict):
                errors.append(f"Agency {i}: must be a mapping")
                continue
            try:
                agencies.append(Agency.model_validate(item))
            except Exception as e:
                errors.append(f"Agency {i}: {e}")

    if errors:
        raise ManifestError(
            f"Manifest {path} has {len(errors)} validation error(s):\n"
            + "\n".join(f"  - {e}" for e in errors),
            errors=errors,
        )

    return Manifest(forms=forms)


def load_all_manifests(manifests_dir: Path) -> list[Manifest]:
    results: list[Manifest] = []
    errors: list[str] = []

    for path in sorted(manifests_dir.glob("*.yaml")):
        try:
            results.append(load_manifest(path))
        except ManifestError as e:
            errors.append(str(e))

    for path in sorted(manifests_dir.glob("*.yml")):
        if path.suffix == ".yml" and path.with_suffix(".yaml").exists():
            continue
        try:
            results.append(load_manifest(path))
        except ManifestError as e:
            errors.append(str(e))

    if errors and not results:
        raise ManifestError("All manifests failed to load", errors)

    return results
