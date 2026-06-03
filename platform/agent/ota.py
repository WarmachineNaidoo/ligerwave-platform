#!/usr/bin/env python3
"""
Ligerwave Router Agent OTA Updater
Checks GitHub releases, downloads, verifies SHA256, replaces self.
"""

import hashlib
import json
import logging
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("ligerwave-ota")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

REPO = "ligerwave/router-agent"
RELEASES_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
ASSET_NAME = "ligerwave-router-agent.py"
BACKUP_SUFFIX = ".bak"
OWN_PATH = Path(__file__).resolve()


def get_latest_release() -> Optional[dict]:
    import urllib.request
    req = urllib.request.Request(RELEASES_URL, headers={"Accept": "application/json", "User-Agent": "ligerwave-ota/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        logger.error("failed to fetch latest release: %s", exc)
        return None


def download_asset(asset_url: str) -> Optional[bytes]:
    req = urllib.request.Request(asset_url, headers={"User-Agent": "ligerwave-ota/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as exc:
        logger.error("download failed: %s", exc)
        return None


def verify_sha256(data: bytes, expected_hash: str) -> bool:
    actual = hashlib.sha256(data).hexdigest()
    return actual.lower() == expected_hash.lower()


def get_current_version() -> str:
    """Extract version string from self."""
    for line in OWN_PATH.read_text().splitlines():
        if line.startswith("# Ligerwave Router CSI Agent"):
            parts = line.split("v")
            if len(parts) > 1:
                return parts[-1].strip()
    return "0.1.0"


def replace_self(new_data: bytes) -> Tuple[bool, str]:
    """Atomically replace the running script. Keeps backup for rollback."""
    backup_path = OWN_PATH.with_suffix(OWN_PATH.suffix + BACKUP_SUFFIX)
    temp_path = OWN_PATH.with_suffix(".tmp")

    try:
        # Backup current
        shutil.copy2(str(OWN_PATH), str(backup_path))
        logger.info("backup saved to %s", backup_path)

        # Write new version atomically
        with open(temp_path, "wb") as f:
            f.write(new_data)
        temp_path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        temp_path.replace(OWN_PATH)
        logger.info("update applied: %s", OWN_PATH)
        return True, str(backup_path)
    except Exception as exc:
        logger.error("replace failed: %s", exc)
        return False, ""


def rollback(backup_path: str) -> bool:
    try:
        shutil.copy2(backup_path, str(OWN_PATH))
        OWN_PATH.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        logger.info("rolled back from %s", backup_path)
        return True
    except Exception as exc:
        logger.error("rollback failed: %s", exc)
        return False


def restart_agent():
    """Restart the agent via init.d or systemd."""
    for svc in ["/etc/init.d/ligerwave-agent", "/etc/systemd/system/ligerwave-agent.service"]:
        if os.path.exists(svc):
            try:
                subprocess.run(["service", "ligerwave-agent", "restart"], check=False)
                return
            except Exception:
                pass
    logger.warning("no service file found, manual restart required")


def check_update() -> Optional[str]:
    release = get_latest_release()
    if not release:
        return None

    tag = release.get("tag_name", "")
    current = get_current_version()
    logger.info("current=%s latest=%s", current, tag.lstrip("v"))

    if tag.lstrip("v") == current:
        logger.info("already up to date")
        return None

    assets = release.get("assets", [])
    target = None
    for asset in assets:
        if asset.get("name") == ASSET_NAME:
            target = asset
            break

    if not target:
        logger.warning("asset %s not found in release", ASSET_NAME)
        return None

    dl_url = target.get("browser_download_url")
    sha_url = dl_url + ".sha256"

    # Fetch SHA256
    expected_hash = None
    try:
        req = urllib.request.Request(sha_url, headers={"User-Agent": "ligerwave-ota/0.1"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            expected_hash = resp.read().decode("utf-8").strip().split()[0]
    except Exception:
        # Try getting SHA from release body or fallback
        body = release.get("body", "")
        for line in body.splitlines():
            if "sha256" in line.lower() or ASSET_NAME in line:
                parts = line.split()
                for p in parts:
                    if len(p) == 64 and all(c in "0123456789abcdef" for c in p.lower()):
                        expected_hash = p
                        break

    if not expected_hash:
        logger.warning("no SHA256 found in release, skipping verification")
        return None

    data = download_asset(dl_url)
    if not data:
        return None

    if not verify_sha256(data, expected_hash):
        logger.error("SHA256 mismatch: expected=%s", expected_hash)
        return None

    logger.info("SHA256 verified")

    success, backup_path = replace_self(data)
    if success:
        restart_agent()
        return tag
    else:
        if backup_path:
            rollback(backup_path)
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ligerwave Agent OTA Updater")
    parser.add_argument("--check", action="store_true", help="Check for update")
    parser.add_argument("--apply", action="store_true", help="Check and apply update")
    args = parser.parse_args()

    if args.check:
        release = get_latest_release()
        if release:
            tag = release.get("tag_name", "unknown")
            current = get_current_version()
            print(f"Current version: v{current}")
            print(f"Latest version:  {tag}")
            print(f"Update available: {'yes' if tag.lstrip('v') != current else 'no'}")
        else:
            print("Failed to check for updates")
    elif args.apply:
        result = check_update()
        if result:
            print(f"Updated to {result}")
        else:
            print("No update available or update failed")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
