from __future__ import annotations

import zipfile
from pathlib import Path


_FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def build_deterministic_zip(bundle_root: Path, archive_path: Path) -> Path:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = archive_path.with_suffix(archive_path.suffix + ".tmp")

    with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in bundle_root.rglob("*") if p.is_file()):
            relative = path.relative_to(bundle_root).as_posix()
            info = zipfile.ZipInfo(relative, _FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())

    temp_path.replace(archive_path)
    return archive_path
