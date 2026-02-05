#!/usr/bin/env python3
"""
RTKA Wi-Fi manager (manual run, no service/watchdog required).

Flow requested:
1) Try auto-connect to known Wi-Fi.
2) Scan nearby Wi-Fi for 10 seconds.
3) Enable AP + captive portal.
4) From portal user can:
   - connect using known saved profiles
   - connect using manual SSID/password
"""

from __future__ import annotations

import fcntl
import html
import json
import logging
import os
import socketserver
import subprocess
import threading
import time
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "portal.log"


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


WIFI_IFACE = os.getenv("RTKA_WIFI_IFACE", "wlan0")
AP_NAME = os.getenv("RTKA_AP_NAME", "EdupiRobo_AP")
AP_SSID = os.getenv("RTKA_AP_SSID", "EdupiRobo_AP")
AP_PASSWORD = os.getenv("RTKA_AP_PASSWORD", "")
AP_IPV4 = os.getenv("RTKA_AP_IPV4", "192.168.1.101/24")
PORTAL_HOST = os.getenv("RTKA_PORTAL_HOST", "0.0.0.0")
PORTAL_PORT = env_int("RTKA_PORTAL_PORT", 80)

CONNECT_TIMEOUT_SEC = env_int("RTKA_CONNECT_TIMEOUT", 25)
SCAN_WINDOW_SEC = env_int("RTKA_SCAN_WINDOW_SEC", 10)
SCAN_STEP_SEC = env_float("RTKA_SCAN_STEP_SEC", 2.0)
MONITOR_INTERVAL_SEC = env_float("RTKA_MONITOR_INTERVAL_SEC", 3.0)
PREFERRED_IP_OCTET = env_int("RTKA_PREFERRED_IP_OCTET", 101)
LOCK_FILE = os.getenv("RTKA_LOCK_FILE", "/tmp/netportal_wifi_manager.lock")


logger = logging.getLogger("wifi_manager")
INSTANCE_LOCK_HANDLE = None


@dataclass
class KnownProfile:
    name: str
    ssid: str


@dataclass
class PortalState:
    mode: str = "INIT"
    connected_ssid: Optional[str] = None
    last_error: str = ""
    last_event: str = "Starting..."
    scan_results: List[Dict[str, str]] = field(default_factory=list)
    known_profiles: List[KnownProfile] = field(default_factory=list)
    last_scan_at: float = 0.0
    connecting: bool = False


STATE = PortalState()
STATE_LOCK = threading.Lock()
WIFI_OP_LOCK = threading.Lock()


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def acquire_instance_lock() -> bool:
    global INSTANCE_LOCK_HANDLE
    try:
        lock_handle = open(LOCK_FILE, "w", encoding="utf-8")
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_handle.write(str(os.getpid()))
        lock_handle.flush()
        INSTANCE_LOCK_HANDLE = lock_handle
        return True
    except OSError as exc:
        logger.error("Another wifi_manager instance is already running (%s)", exc)
        return False


def set_state(mode: Optional[str] = None, event: Optional[str] = None, error: Optional[str] = None) -> None:
    with STATE_LOCK:
        if mode is not None:
            STATE.mode = mode
        if event is not None:
            STATE.last_event = event
        if error is not None:
            STATE.last_error = error


def set_connected_ssid(ssid: Optional[str]) -> None:
    with STATE_LOCK:
        STATE.connected_ssid = ssid


def set_connecting(value: bool) -> None:
    with STATE_LOCK:
        STATE.connecting = value


def set_known_profiles(rows: List[KnownProfile]) -> None:
    with STATE_LOCK:
        STATE.known_profiles = rows


def update_scan_results(rows: List[Dict[str, str]]) -> None:
    with STATE_LOCK:
        STATE.scan_results = rows
        STATE.last_scan_at = time.time()
        if rows:
            STATE.last_event = f"Scan complete ({len(rows)} networks)"
        else:
            STATE.last_event = "Scan complete (no networks found)"


def get_state_snapshot() -> Dict[str, object]:
    with STATE_LOCK:
        return {
            "mode": STATE.mode,
            "connected_ssid": STATE.connected_ssid,
            "last_error": STATE.last_error,
            "last_event": STATE.last_event,
            "scan_results": list(STATE.scan_results),
            "known_profiles": [{"name": p.name, "ssid": p.ssid} for p in STATE.known_profiles],
            "last_scan_at": STATE.last_scan_at,
            "connecting": STATE.connecting,
        }


def run_cmd(args: List[str], timeout: int = 20) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        stderr = (exc.stderr or "").strip()
        if stderr:
            stderr += "\n"
        stderr += f"Timeout after {timeout}s"
        return subprocess.CompletedProcess(args=args, returncode=124, stdout=(exc.stdout or ""), stderr=stderr)


def nmcli(args: List[str], timeout: int = 20) -> subprocess.CompletedProcess:
    return run_cmd(["nmcli", *args], timeout=timeout)


def connection_exists(name: str) -> bool:
    cp = nmcli(["-t", "-f", "NAME", "connection", "show"])
    if cp.returncode != 0:
        return False
    names = [line.strip() for line in cp.stdout.splitlines() if line.strip()]
    return name in names


def ensure_ap_profile() -> bool:
    if not connection_exists(AP_NAME):
        cp = nmcli(
            [
                "connection",
                "add",
                "type",
                "wifi",
                "ifname",
                WIFI_IFACE,
                "con-name",
                AP_NAME,
                "autoconnect",
                "no",
                "ssid",
                AP_SSID,
            ]
        )
        if cp.returncode != 0:
            logger.error("Failed to create AP profile: %s", cp.stderr.strip())
            return False

    cp = nmcli(
        [
            "connection",
            "modify",
            AP_NAME,
            "802-11-wireless.mode",
            "ap",
            "802-11-wireless.band",
            "bg",
            "ipv4.method",
            "shared",
            "ipv4.addresses",
            AP_IPV4,
            "ipv6.method",
            "ignore",
        ]
    )
    if cp.returncode != 0:
        logger.error("Failed to update AP profile: %s", cp.stderr.strip())
        return False

    if AP_PASSWORD:
        cp = nmcli(
            [
                "connection",
                "modify",
                AP_NAME,
                "wifi-sec.key-mgmt",
                "wpa-psk",
                "wifi-sec.psk",
                AP_PASSWORD,
            ]
        )
        if cp.returncode != 0:
            logger.error("Failed to set AP password: %s", cp.stderr.strip())
            return False
    else:
        nmcli(["connection", "modify", AP_NAME, "wifi-sec.key-mgmt", ""])

    return True


def get_wifi_status() -> Dict[str, str]:
    cp = nmcli(["-t", "-f", "GENERAL.STATE,GENERAL.CONNECTION", "device", "show", WIFI_IFACE])
    if cp.returncode != 0:
        return {"state": "unknown", "connection": "--"}

    result = {"state": "unknown", "connection": "--"}
    for line in cp.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if "GENERAL.STATE" in key:
            result["state"] = value
        elif "GENERAL.CONNECTION" in key:
            result["connection"] = value
    return result


def get_active_connection_name() -> Optional[str]:
    status = get_wifi_status()
    conn = status.get("connection", "--").strip()
    state = status.get("state", "")
    if not state.startswith("100") or conn in ("--", AP_NAME):
        return None
    return conn


def get_active_wifi_ssid() -> Optional[str]:
    conn = get_active_connection_name()
    if not conn:
        return None
    cp = nmcli(["-g", "802-11-wireless.ssid", "connection", "show", conn])
    if cp.returncode == 0 and cp.stdout.strip():
        return cp.stdout.strip()
    return conn


def is_ap_active() -> bool:
    cp = nmcli(["-t", "-f", "NAME,DEVICE", "connection", "show", "--active"])
    if cp.returncode != 0:
        return False
    for line in cp.stdout.splitlines():
        parts = line.split(":")
        if len(parts) >= 2 and parts[0] == AP_NAME and parts[1] == WIFI_IFACE:
            return True
    return False


def ap_up(retries: int = 3) -> bool:
    for idx in range(1, retries + 1):
        cp = nmcli(["connection", "up", AP_NAME], timeout=25)
        if cp.returncode == 0:
            logger.info("AP active: %s", AP_NAME)
            return True
        logger.warning("AP up attempt %s/%s failed: %s", idx, retries, cp.stderr.strip() or cp.stdout.strip())
        time.sleep(1.5)
    return False


def ap_down() -> None:
    cp = nmcli(["connection", "down", AP_NAME], timeout=20)
    if cp.returncode == 0:
        logger.info("AP disabled")


def disconnect_wifi_client() -> None:
    cp = nmcli(["device", "disconnect", WIFI_IFACE], timeout=20)
    if cp.returncode == 0:
        logger.info("Wi-Fi client disconnected on %s", WIFI_IFACE)


def get_saved_profiles() -> List[KnownProfile]:
    cp = nmcli(["-t", "-f", "NAME,TYPE", "connection", "show"])
    if cp.returncode != 0:
        return []

    profiles: List[KnownProfile] = []
    for line in cp.stdout.splitlines():
        parts = line.split(":")
        if len(parts) < 2:
            continue
        name, typ = parts[0].strip(), parts[1].strip()
        if typ != "802-11-wireless" or not name or name == AP_NAME:
            continue
        ssid_cp = nmcli(["-g", "802-11-wireless.ssid", "connection", "show", name])
        ssid = ssid_cp.stdout.strip() if ssid_cp.returncode == 0 else ""
        profiles.append(KnownProfile(name=name, ssid=ssid or name))

    profiles.sort(key=lambda p: p.ssid.lower())
    return profiles


def scan_wifi_once(rescan: bool = True) -> List[Dict[str, str]]:
    scan_flag = "yes" if rescan else "no"
    cp = nmcli(
        [
            "-m",
            "multiline",
            "-f",
            "SSID,SIGNAL,SECURITY",
            "device",
            "wifi",
            "list",
            "ifname",
            WIFI_IFACE,
            "--rescan",
            scan_flag,
        ],
        timeout=30,
    )
    if cp.returncode != 0:
        logger.warning("Wi-Fi scan failed: %s", cp.stderr.strip() or cp.stdout.strip())
        return []

    rows: List[Dict[str, str]] = []
    item: Dict[str, str] = {}
    for line in cp.stdout.splitlines():
        line = line.strip()
        if not line:
            if item:
                rows.append(item)
                item = {}
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        k = key.strip().lower()
        if k in ("ssid", "signal", "security"):
            item[k] = value.strip()
    if item:
        rows.append(item)

    best: Dict[str, Dict[str, str]] = {}
    for r in rows:
        ssid = r.get("ssid", "").strip()
        if not ssid:
            continue
        signal = int(r.get("signal", "0") or 0)
        if ssid not in best or signal > int(best[ssid].get("signal", "0") or 0):
            best[ssid] = {
                "ssid": ssid,
                "signal": str(signal),
                "security": r.get("security", "").strip() or "OPEN",
            }

    return sorted(best.values(), key=lambda x: int(x["signal"]), reverse=True)


def scan_wifi_window(seconds: int) -> List[Dict[str, str]]:
    until = time.time() + max(2, seconds)
    merged: Dict[str, Dict[str, str]] = {}
    first = True
    while time.time() < until:
        rows = scan_wifi_once(rescan=first)
        first = False
        for r in rows:
            ssid = r.get("ssid", "")
            if not ssid:
                continue
            signal = int(r.get("signal", "0") or 0)
            if ssid not in merged or signal > int(merged[ssid].get("signal", "0") or 0):
                merged[ssid] = r
        time.sleep(max(0.5, SCAN_STEP_SEC))

    return sorted(merged.values(), key=lambda x: int(x["signal"]), reverse=True)


def get_device_ipv4_context() -> Optional[Dict[str, object]]:
    cp = nmcli(["-t", "-f", "IP4.ADDRESS[1],IP4.GATEWAY,IP4.DNS[1],IP4.DNS[2]", "device", "show", WIFI_IFACE])
    if cp.returncode != 0:
        return None

    address = ""
    gateway = ""
    dns: List[str] = []
    for line in cp.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "IP4.ADDRESS[1]":
            address = value
        elif key == "IP4.GATEWAY":
            gateway = value
        elif key.startswith("IP4.DNS[") and value:
            dns.append(value)

    if "/" not in address:
        return None

    ip, prefix = address.split("/", 1)
    try:
        prefix_int = int(prefix)
    except ValueError:
        return None

    return {
        "ip": ip.strip(),
        "prefix": prefix_int,
        "gateway": gateway.strip(),
        "dns": dns,
    }


def replace_last_octet(ip: str, last_octet: int) -> Optional[str]:
    parts = ip.split(".")
    if len(parts) != 4:
        return None
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if any(n < 0 or n > 255 for n in nums):
        return None
    nums[3] = last_octet
    return ".".join(str(n) for n in nums)


def get_connection_ipv4_snapshot(conn_name: str) -> Dict[str, str]:
    snapshot: Dict[str, str] = {}
    for field in ("ipv4.method", "ipv4.addresses", "ipv4.gateway", "ipv4.dns"):
        cp = nmcli(["-g", field, "connection", "show", conn_name])
        snapshot[field] = cp.stdout.strip() if cp.returncode == 0 else ""
    return snapshot


def restore_connection_ipv4(conn_name: str, snapshot: Dict[str, str]) -> None:
    cp = nmcli(
        [
            "connection",
            "modify",
            conn_name,
            "ipv4.method",
            snapshot.get("ipv4.method", "").strip() or "auto",
            "ipv4.addresses",
            snapshot.get("ipv4.addresses", "").strip(),
            "ipv4.gateway",
            snapshot.get("ipv4.gateway", "").strip(),
            "ipv4.dns",
            snapshot.get("ipv4.dns", "").strip(),
        ]
    )
    if cp.returncode != 0:
        logger.warning("Failed to restore IPv4 profile for %s: %s", conn_name, cp.stderr.strip())
    nmcli(["connection", "up", conn_name], timeout=CONNECT_TIMEOUT_SEC + 5)


def apply_preferred_ip_policy(conn_name: str) -> None:
    if PREFERRED_IP_OCTET < 1 or PREFERRED_IP_OCTET > 254:
        return

    info = get_device_ipv4_context()
    if not info:
        return

    current_ip = str(info["ip"])
    prefix = int(info["prefix"])
    gateway = str(info["gateway"])
    dns_list = [d for d in info["dns"] if isinstance(d, str)]

    target_ip = replace_last_octet(current_ip, PREFERRED_IP_OCTET)
    if not target_ip or target_ip == current_ip:
        return

    snapshot = get_connection_ipv4_snapshot(conn_name)
    dns_value = ",".join(dns_list) if dns_list else gateway
    set_state(event=f"Trying static IP {target_ip}")

    cp = nmcli(
        [
            "connection",
            "modify",
            conn_name,
            "ipv4.method",
            "manual",
            "ipv4.addresses",
            f"{target_ip}/{prefix}",
            "ipv4.gateway",
            gateway,
            "ipv4.dns",
            dns_value,
        ]
    )
    if cp.returncode != 0:
        logger.warning("Static IP modify failed, keep DHCP")
        return

    cp = nmcli(["connection", "up", conn_name], timeout=CONNECT_TIMEOUT_SEC + 5)
    if cp.returncode != 0:
        restore_connection_ipv4(conn_name, snapshot)
        set_state(event="Static IP failed, reverted to DHCP/profile")
        return

    time.sleep(1.2)
    verify = get_device_ipv4_context()
    if verify and str(verify.get("ip", "")).strip() == target_ip:
        set_state(event=f"Connected with static IP {target_ip}", error="")
        return

    restore_connection_ipv4(conn_name, snapshot)
    set_state(event="Static IP failed, using DHCP/profile")


def auto_connect_known() -> Optional[str]:
    set_state(mode="BOOT", event="Auto connect known Wi-Fi", error="")
    cp = nmcli(["--wait", str(CONNECT_TIMEOUT_SEC), "device", "connect", WIFI_IFACE], timeout=CONNECT_TIMEOUT_SEC + 8)
    if cp.returncode != 0:
        logger.info("No known network connected: %s", cp.stderr.strip() or cp.stdout.strip())
        return None

    conn_name = get_active_connection_name()
    ssid = get_active_wifi_ssid()
    if conn_name:
        apply_preferred_ip_policy(conn_name)
    if ssid:
        set_connected_ssid(ssid)
        set_state(mode="AUTO_CONNECTED", event=f"Connected to known Wi-Fi: {ssid}", error="")
    return ssid


def connect_via_manual_ssid(ssid: str, password: str) -> Tuple[bool, str]:
    with WIFI_OP_LOCK:
        set_connecting(True)
        try:
            set_state(mode="CONNECTING", event=f"Connecting to {ssid}", error="")
            ap_down()
            time.sleep(2.0)

            cmd = [
                "--wait",
                str(CONNECT_TIMEOUT_SEC),
                "device",
                "wifi",
                "connect",
                ssid,
                "ifname",
                WIFI_IFACE,
            ]
            if password:
                cmd += ["password", password]

            cp = nmcli(cmd, timeout=CONNECT_TIMEOUT_SEC + 8)
            if cp.returncode != 0:
                err = cp.stderr.strip() or cp.stdout.strip() or "Unknown error"
                ap_up()
                set_connected_ssid(None)
                set_state(mode="PORTAL", event=f"Failed to connect to {ssid}", error=err)
                return False, err

            conn_name = get_active_connection_name()
            active_ssid = get_active_wifi_ssid() or ssid
            if conn_name:
                apply_preferred_ip_policy(conn_name)
            set_connected_ssid(active_ssid)
            set_known_profiles(get_saved_profiles())
            set_state(mode="ONLINE", event=f"Connected to {active_ssid}", error="")
            return True, ""
        finally:
            set_connecting(False)


def connect_via_known_profile(profile_name: str) -> Tuple[bool, str]:
    with WIFI_OP_LOCK:
        set_connecting(True)
        try:
            set_state(mode="CONNECTING", event=f"Connecting known profile: {profile_name}", error="")
            ap_down()
            time.sleep(2.0)

            cp = nmcli(
                ["--wait", str(CONNECT_TIMEOUT_SEC), "connection", "up", profile_name],
                timeout=CONNECT_TIMEOUT_SEC + 8,
            )
            if cp.returncode != 0:
                err = cp.stderr.strip() or cp.stdout.strip() or "Unknown error"
                ap_up()
                set_connected_ssid(None)
                set_state(mode="PORTAL", event=f"Failed profile: {profile_name}", error=err)
                return False, err

            active_ssid = get_active_wifi_ssid() or profile_name
            conn_name = get_active_connection_name()
            if conn_name:
                apply_preferred_ip_policy(conn_name)
            set_connected_ssid(active_ssid)
            set_state(mode="ONLINE", event=f"Connected via known profile: {active_ssid}", error="")
            return True, ""
        finally:
            set_connecting(False)


def refresh_scan_from_portal() -> None:
    with WIFI_OP_LOCK:
        set_state(mode="SCAN", event="Refreshing nearby Wi-Fi (AP temporarily off)", error="")
        ap_was_active = is_ap_active()
        if ap_was_active:
            ap_down()
            time.sleep(1.0)

        rows = scan_wifi_window(seconds=SCAN_WINDOW_SEC)
        update_scan_results(rows)

        if ap_was_active and not get_active_wifi_ssid():
            if not ap_up():
                set_state(mode="ERROR", event="AP failed to restart", error="Failed to restart AP after scan")
            else:
                set_state(mode="PORTAL", event=f"AP active ({AP_SSID})", error="")


def force_back_to_ap() -> Tuple[bool, str]:
    with WIFI_OP_LOCK:
        if get_state_snapshot().get("connecting"):
            return False, "Sedang proses koneksi, tunggu selesai."

        set_state(mode="FORCE_AP", event="Forcing back to AP mode", error="")
        disconnect_wifi_client()
        time.sleep(1.0)
        if ap_up():
            set_connected_ssid(None)
            set_known_profiles(get_saved_profiles())
            set_state(mode="PORTAL", event=f"Forced to AP ({AP_SSID})", error="")
            return True, ""
        set_state(mode="ERROR", event="Force AP failed", error="Tidak bisa mengaktifkan AP")
        return False, "Tidak bisa mengaktifkan AP"


def monitor_connection_loop() -> None:
    while True:
        snap = get_state_snapshot()
        if snap["connecting"]:
            time.sleep(MONITOR_INTERVAL_SEC)
            continue

        with WIFI_OP_LOCK:
            snap = get_state_snapshot()
            if snap["connecting"]:
                time.sleep(MONITOR_INTERVAL_SEC)
                continue

            ssid = get_active_wifi_ssid()
            if ssid:
                set_connected_ssid(ssid)
                if is_ap_active():
                    ap_down()
                set_state(mode="ONLINE", event=f"Connected to {ssid}", error="")
            else:
                set_connected_ssid(None)
                set_known_profiles(get_saved_profiles())
                if not is_ap_active():
                    if ap_up():
                        set_state(mode="PORTAL", event=f"Disconnected, AP active ({AP_SSID})", error="")
                    else:
                        set_state(mode="ERROR", event="Disconnected, AP activation failed", error="Cannot enable AP")
                else:
                    set_state(mode="PORTAL", event=f"AP active ({AP_SSID})", error="")

        time.sleep(MONITOR_INTERVAL_SEC)


def startup_sequence() -> None:
    set_known_profiles(get_saved_profiles())
    auto_connect_known()

    set_state(mode="SCAN", event=f"Scanning Wi-Fi for {SCAN_WINDOW_SEC} seconds", error="")
    rows = scan_wifi_window(seconds=SCAN_WINDOW_SEC)
    update_scan_results(rows)

    disconnect_wifi_client()
    time.sleep(1.0)

    if not ap_up():
        set_state(mode="ERROR", event="Cannot start AP", error="Failed to activate AP profile")
        return

    set_state(mode="PORTAL", event=f"AP active ({AP_SSID}) - open captive portal", error="")


def html_page() -> str:
    snap = get_state_snapshot()
    mode = html.escape(str(snap["mode"]))
    connected = html.escape(str(snap["connected_ssid"] or "-"))
    event = html.escape(str(snap["last_event"] or "-"))
    error = html.escape(str(snap["last_error"] or "-"))

    last_scan = "-"
    if snap["last_scan_at"]:
        last_scan = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(snap["last_scan_at"])))

    scan_rows_html = ""
    for row in snap["scan_results"]:
        raw_ssid = str(row.get("ssid", ""))
        ssid = html.escape(raw_ssid)
        ssid_js = json.dumps(raw_ssid)
        signal = html.escape(str(row.get("signal", "0")))
        security = html.escape(str(row.get("security", "OPEN")))
        scan_rows_html += (
            f"<tr><td>{ssid}</td><td>{signal}%</td><td>{security}</td>"
            f"<td><button type='button' onclick='pickSsid({ssid_js})'>Pilih</button></td></tr>"
        )
    if not scan_rows_html:
        scan_rows_html = "<tr><td colspan='4'>Belum ada data scan.</td></tr>"

    known_rows_html = ""
    for p in snap["known_profiles"]:
        name = html.escape(str(p.get("name", "")))
        ssid = html.escape(str(p.get("ssid", "")))
        known_rows_html += (
            "<tr>"
            f"<td>{ssid}</td><td>{name}</td>"
            "<td>"
            "<form method='POST' action='/connect-known' style='margin:0'>"
            f"<input type='hidden' name='profile' value='{name}'>"
            "<button type='submit'>Connect</button>"
            "</form>"
            "</td>"
            "</tr>"
        )
    if not known_rows_html:
        known_rows_html = "<tr><td colspan='3'>Belum ada profile Wi-Fi tersimpan.</td></tr>"

    return f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EdupiRobo Wi-Fi Portal</title>
  <style>
    :root {{ --bg:#f4f7fb; --card:#fff; --ink:#12324a; --muted:#60758b; --accent:#0b7fab; --danger:#c03a2b; --line:#dde6ef; }}
    body {{ font-family:"Segoe UI",Tahoma,sans-serif; margin:0; background:var(--bg); color:var(--ink); }}
    .wrap {{ max-width:980px; margin:20px auto; padding:16px; }}
    .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; margin-bottom:14px; }}
    h1 {{ margin:0 0 10px; font-size:24px; }}
    .meta {{ color:var(--muted); font-size:14px; }}
    .err {{ color:var(--danger); }}
    table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
    th,td {{ border-bottom:1px solid var(--line); text-align:left; padding:8px; font-size:14px; }}
    input,button {{ padding:10px; border-radius:10px; border:1px solid #c8d7e4; }}
    input {{ width:100%; box-sizing:border-box; margin:6px 0; }}
    button {{ cursor:pointer; background:var(--accent); color:#fff; border:none; }}
    .row {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
    @media (max-width:700px) {{ .row {{ grid-template-columns:1fr; }} }}
  </style>
  <script>
    function pickSsid(v) {{
      document.getElementById('ssid').value = v;
      window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }});
    }}
    setTimeout(function() {{ location.reload(); }}, 15000);
  </script>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>EdupiRobo Wi-Fi Setup</h1>
      <div class="meta">Mode: <b>{mode}</b> | Connected: <b>{connected}</b> | Last scan: <b>{last_scan}</b></div>
      <div class="meta">Event: {event}</div>
      <div class="meta err">Error: {error}</div>
      <form method="POST" action="/force-ap" style="margin-top:10px">
        <button type="submit">Force Back to AP</button>
      </form>
    </div>

    <div class="card">
      <h3>Connect ke Jaringan Tersimpan</h3>
      <table>
        <thead><tr><th>SSID</th><th>Profile</th><th>Aksi</th></tr></thead>
        <tbody>{known_rows_html}</tbody>
      </table>
    </div>

    <div class="card">
      <h3>Wi-Fi Terdeteksi</h3>
      <form method="POST" action="/scan"><button type="submit">Rescan {SCAN_WINDOW_SEC}s</button></form>
      <table>
        <thead><tr><th>SSID</th><th>Signal</th><th>Security</th><th>Aksi</th></tr></thead>
        <tbody>{scan_rows_html}</tbody>
      </table>
    </div>

    <div class="card">
      <h3>Connect Manual (SSID + Password)</h3>
      <form method="POST" action="/connect">
        <div class="row">
          <div><label>SSID</label><input id="ssid" name="ssid" required></div>
          <div><label>Password (kosongkan jika OPEN)</label><input name="password" type="password"></div>
        </div>
        <button type="submit">Connect</button>
      </form>
    </div>
  </div>
</body>
</html>"""


class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class PortalHandler(BaseHTTPRequestHandler):
    server_version = "RTKAPortal/3.0"

    def log_message(self, fmt: str, *args: object) -> None:
        logger.info("HTTP %s - %s", self.address_string(), fmt % args)

    def _send_json(self, payload: Dict[str, object], status: int = 200) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, content: str, status: int = 200) -> None:
        raw = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _redirect(self, path: str = "/") -> None:
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", path)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send_html(html_page())
            return
        if path == "/api/status":
            self._send_json(get_state_snapshot())
            return
        if path in ("/generate_204", "/hotspot-detect.html", "/ncsi.txt", "/connecttest.txt", "/fwlink"):
            self._redirect("/")
            return
        self._redirect("/")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        form = parse_qs(body)

        if path == "/scan":
            refresh_scan_from_portal()
            self._redirect("/")
            return

        if path == "/force-ap":
            ok, err = force_back_to_ap()
            if ok:
                self._redirect("/")
            else:
                self._send_html(f"<h2>Failed</h2><pre>{html.escape(err)}</pre><p><a href='/'>Back</a></p>", status=400)
            return

        if path == "/connect-known":
            profile = (form.get("profile", [""])[0] or "").strip()
            if not profile:
                set_state(error="Profile kosong", event="Rejected empty profile")
                self._redirect("/")
                return
            ok, err = connect_via_known_profile(profile)
            if ok:
                self._send_html(
                    "<h2>Success</h2><p>Connected using known profile.</p>"
                    "<p>Please connect your phone/laptop to the same Wi-Fi.</p>"
                )
            else:
                self._send_html(f"<h2>Failed</h2><pre>{html.escape(err)}</pre><p><a href='/'>Try again</a></p>", status=400)
            return

        if path == "/connect":
            ssid = (form.get("ssid", [""])[0] or "").strip()
            password = (form.get("password", [""])[0] or "").strip()
            if not ssid:
                set_state(error="SSID wajib diisi", event="Rejected empty SSID")
                self._redirect("/")
                return

            # Equivalent to: nmcli device wifi connect "ssid" password "password"
            ok, err = connect_via_manual_ssid(ssid, password)
            if ok:
                self._send_html(
                    "<h2>Success</h2><p>Connected to Wi-Fi.</p>"
                    "<p>Please connect your phone/laptop to the same Wi-Fi.</p>"
                )
            else:
                self._send_html(f"<h2>Failed</h2><pre>{html.escape(err)}</pre><p><a href='/'>Try again</a></p>", status=400)
            return

        self._redirect("/")


def main() -> None:
    setup_logging()
    logger.info("Starting RTKA Wi-Fi manager")
    if not acquire_instance_lock():
        return

    logger.info("iface=%s ap=%s ssid=%s portal=%s:%s", WIFI_IFACE, AP_NAME, AP_SSID, PORTAL_HOST, PORTAL_PORT)
    if not ensure_ap_profile():
        set_state(mode="ERROR", event="Cannot prepare AP profile", error="nmcli AP profile setup failed")
        return

    startup_sequence()

    monitor_thread = threading.Thread(target=monitor_connection_loop, daemon=True)
    monitor_thread.start()

    with ThreadingHTTPServer((PORTAL_HOST, PORTAL_PORT), PortalHandler) as httpd:
        logger.info("Portal listening on http://%s:%s", PORTAL_HOST, PORTAL_PORT)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
