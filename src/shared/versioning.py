from __future__ import annotations

import subprocess
from pathlib import Path


def get_git_sha(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_short_sha(project_root: Path, long_sha: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", long_sha],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def read_project_semver(semver_file: Path) -> str:
    if not semver_file.exists():
        raise FileNotFoundError(f"Missing file: {semver_file}")

    for raw_line in semver_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == "semver":
            semver = value.strip()
            if not semver:
                raise ValueError("semver.txt contains an empty semver value")
            return semver

    raise ValueError("semver.txt must contain a line like: semver: n.n.n")


def read_existing_internal_build(version_file: Path) -> int:
    if not version_file.exists():
        return 0

    for raw_line in version_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == "internal_build":
            value = value.strip()
            if not value:
                return 0
            return int(value)

    return 0


def write_version(
    version_file: Path,
    semver: str,
    long_sha: str,
    short_sha: str,
    internal_build: int,
) -> None:
    version = f"{semver}+sha.{short_sha}-build.{internal_build}"
    display_version = f"{semver} ({short_sha}, build {internal_build})"

    content = "\n".join(
        [
            f"semver: {semver}",
            f"long_sha: {long_sha}",
            f"short_sha: {short_sha}",
            f"internal_build: {internal_build}",
            f"version: {version}",
            f"display_version: {display_version}",
            "",
        ]
    )

    version_file.write_text(content, encoding="utf-8")


def update_version_files(
    project_root: Path,
    semver_file: Path,
    version_file: Path,
) -> None:
    semver = read_project_semver(semver_file)
    long_sha = get_git_sha(project_root)
    short_sha = get_short_sha(project_root, long_sha)
    internal_build = read_existing_internal_build(version_file) + 1

    write_version(
        version_file=version_file,
        semver=semver,
        long_sha=long_sha,
        short_sha=short_sha,
        internal_build=internal_build,
    )