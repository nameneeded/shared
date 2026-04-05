# shared

Shared utilities for personal Python projects.

## cli_args.py

## file_io.py

## logging_setup.py

## settings.py

## time_utilities.py

## versioning.py

Provides a lightweight, reusable versioning utility that combines:

- Semantic versioning (`semver`)
- Git commit identification (`long_sha`, `short_sha`)
- Incrementing internal build numbers

This is designed for projects that:
- are run directly from source (not packaged releases yet)
- want traceability between runs and git state
- want human-readable and machine-readable version strings

---

### 📁 Expected Project Structure

Each consuming project should include a `version_info/` directory:

```text
your_project/
  version_info/
    semver.txt
    version.txt
```

#### `semver.txt` (manual)

```text
semver: 0.1.0
```

- Controlled manually
- Represents product version
- Should only change intentionally (not automated)

#### `version.txt` (generated)

```text
semver: 0.1.0
long_sha: <full git sha>
short_sha: <short git sha>
internal_build: <incrementing int>
version: 0.1.0+sha.<short_sha>-build.<n>
display_version: 0.1.0 (<short_sha>, build <n>)
```

- Generated automatically
- Should **never be edited manually**

---

### ⚙️ How It Works

Each time the versioning script runs:

1. Reads `semver.txt`
2. Reads existing `version.txt` (if present)
3. Increments `internal_build`
4. Gets current git commit SHA
5. Writes updated `version.txt`

---

### 🚀 Usage

#### 1. Import from shared repo

```python
from shared.versioning.versioning import update_version_files
```

---

#### 2. Call from your project

Example wrapper script:

```python
from pathlib import Path
from shared.versioning.versioning import update_version_files


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
```

---

### 🧠 Version Fields Explained

| Field              | Purpose |
|------------------|--------|
| `semver`          | Manual product version |
| `long_sha`        | Full git commit hash |
| `short_sha`       | Short git hash (UI/log friendly) |
| `internal_build`  | Incrementing counter per run |
| `version`         | Machine-readable composite version |
| `display_version` | Human-readable version string |

---

### 🧩 Example Output

```text
semver: 0.1.0
long_sha: 7a8c9f3d...
short_sha: 7a8c9f3
internal_build: 12
version: 0.1.0+sha.7a8c9f3-build.12
display_version: 0.1.0 (7a8c9f3, build 12)
```

---

### ⚠️ Notes

- Requires the project to be inside a **git repository**
- `internal_build` increments **every time the script runs**
- Missing `version.txt` is treated as build `0`
- `semver.txt` must contain a valid line:
  ```text
  semver: x.y.z
  ```

---

### 🔮 Future Extensions (Optional)

- Only increment build when git SHA changes
- Add timestamp metadata
- Support CI/CD tagging workflows
- Export version info to application runtime (UI/logging)

---

This utility is intentionally simple and explicit — designed to be easy to drop into any project without introducing heavy tooling.