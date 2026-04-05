from __future__ import annotations

from pathlib import Path

from shared.versioning import update_version_files


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    version_info_dir = project_root / "version_info"

    semver_file = version_info_dir / "semver.txt"
    version_file = version_info_dir / "version.txt"

    update_version_files(
        project_root=project_root,
        semver_file=semver_file,
        version_file=version_file,
    )


if __name__ == "__main__":
    main()