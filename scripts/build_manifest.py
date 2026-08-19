"""
build_manifest.py -- generate SHA-256 hashes for every artefact.
Outputs MANIFEST.json at bundle root.
"""
import json, hashlib
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1]
OUT = BUNDLE / "MANIFEST.json"

def sha256(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

files = []
for sub in ("manuscript","scripts","results","tables","figures"):
    d = BUNDLE / sub
    if not d.exists(): continue
    for fp in sorted(d.rglob("*")):
        if fp.is_file() and not fp.name.startswith("."):
            # skip transient tex files
            if fp.suffix in (".aux",".bbl",".blg",".log",".out",".toc"): continue
            # skip office lock files (~$xxx.docx)
            if fp.name.startswith("~$"): continue
            # skip cover letters (journal-specific, not part of the bundle)
            if fp.name.startswith("cover_letter"): continue
            files.append(dict(
                path=str(fp.relative_to(BUNDLE)).replace("\\","/"),
                bytes=fp.stat().st_size,
                sha256=sha256(fp),
            ))

# root-level files
for name in ("data_charter.md","Makefile","README.md"):
    fp = BUNDLE / name
    if fp.exists():
        files.append(dict(
            path=name,
            bytes=fp.stat().st_size,
            sha256=sha256(fp),
        ))

total_bytes = sum(f["bytes"] for f in files)
OUT.write_text(json.dumps(dict(
    bundle_version="v5.0",
    snapshot_date="2026-08-07",
    manifest_generated="2026-08-19",
    total_files=len(files),
    total_bytes=total_bytes,
    files=files,
), indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Total files: {len(files)}")
print(f"Total bytes: {total_bytes:,} ({total_bytes/1024/1024:.2f} MB)")
print(f"WROTE {OUT}")
