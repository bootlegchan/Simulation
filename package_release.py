"""Master Release Packaging Tool."""
import argparse
import os
import shutil
import zipfile
from pathlib import Path

def package_release(version: str = "v168", output_dir: str = "/workspace/out"):
    base_dir = Path(__file__).resolve().parent
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_zip = out_dir / f"social-simulation-{version}-master-release.zip"

    # Clean __pycache__ and cache directories
    for root, dirs, _ in os.walk(base_dir):
        for d in list(dirs):
            if d in ("__pycache__", ".pytest_cache", ".cache"):
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)

    print(f"Packaging {version} master release...")
    total_files = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(base_dir):
            if any(part in ("__pycache__", ".pytest_cache", ".cache", ".git") for part in Path(root).parts):
                continue
            for file in sorted(files):
                if file.endswith((".pyc", ".pyo", ".log", ".tmp", ".bak")):
                    continue
                fp = Path(root) / file
                rel = fp.relative_to(base_dir)
                zf.write(fp, rel)
                total_files += 1

    print(f"Successfully created {out_zip} ({out_zip.stat().st_size:,} bytes, {total_files} files packaged).")
    return out_zip

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=str, default="v168")
    parser.add_argument("--output-dir", type=str, default="/workspace/out")
    args = parser.parse_args()
    package_release(version=args.version, output_dir=args.output_dir)
