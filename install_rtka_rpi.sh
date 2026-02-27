#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
WITH_TRAINERKIT=0
INSTALL_SERVICES=1
REBOOT_REQUIRED=0

log() {
  printf "[RTKA-INSTALL] %s\n" "$*"
}

warn() {
  printf "[RTKA-INSTALL][WARN] %s\n" "$*" >&2
}

die() {
  printf "[RTKA-INSTALL][ERROR] %s\n" "$*" >&2
  exit 1
}

usage() {
  cat <<'USAGE'
Usage: bash install_rtka_rpi.sh [options]

Options:
  --with-trainerkit   Try to install full TrainerKit requirements (optional/heavy)
  --no-services       Skip systemd service installation
  -h, --help          Show this help
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --with-trainerkit)
      WITH_TRAINERKIT=1
      ;;
    --no-services)
      INSTALL_SERVICES=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $arg"
      ;;
  esac
done

if ! command -v apt-get >/dev/null 2>&1; then
  die "This installer is intended for Debian/Raspberry Pi OS (apt-get not found)."
fi

if ! command -v systemctl >/dev/null 2>&1; then
  die "systemctl not found. Raspberry Pi OS with systemd is required."
fi

if [[ ! -f "${PROJECT_DIR}/main.py" ]] || [[ ! -f "${PROJECT_DIR}/NetPortal/wifi_manager.py" ]]; then
  die "Run this script from RTKA project root (main.py and NetPortal/wifi_manager.py must exist)."
fi

SUDO=""
if [[ ${EUID} -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    die "Please run as root or install sudo."
  fi
fi

RUN_USER="${SUDO_USER:-$(id -un)}"
run_as_user() {
  if [[ -n "${SUDO_USER:-}" ]] && [[ "${RUN_USER}" != "root" ]]; then
    sudo -u "${RUN_USER}" "$@"
  else
    "$@"
  fi
}

BOOT_CONFIG=""
if [[ -f /boot/firmware/config.txt ]]; then
  BOOT_CONFIG="/boot/firmware/config.txt"
elif [[ -f /boot/config.txt ]]; then
  BOOT_CONFIG="/boot/config.txt"
fi

install_apt_dependencies() {
  log "Installing OS dependencies..."
  ${SUDO} apt-get update -y
  ${SUDO} DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    python3-opencv \
    python3-gpiozero \
    python3-lgpio \
    network-manager \
    pigpio \
    v4l-utils \
    ffmpeg \
    libzbar0 \
    libatlas-base-dev \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff6 \
    libglib2.0-0 \
    libgl1 \
    build-essential

  ${SUDO} systemctl enable --now NetworkManager
  if ! ${SUDO} systemctl enable --now pigpiod; then
    warn "Failed to start pigpiod now. It can be checked later with: sudo systemctl status pigpiod"
  fi
}

configure_pwm_overlay() {
  if [[ -z "${BOOT_CONFIG}" ]]; then
    warn "Boot config not found (/boot/firmware/config.txt or /boot/config.txt). Skipping PWM overlay setup."
    return
  fi

  local overlay="dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4"
  if grep -Fxq "$overlay" "$BOOT_CONFIG"; then
    log "PWM overlay already present in ${BOOT_CONFIG}"
    return
  fi

  log "Adding PWM overlay for servo control to ${BOOT_CONFIG}"
  printf "\n# RTKA servo PWM\n%s\n" "$overlay" | ${SUDO} tee -a "$BOOT_CONFIG" >/dev/null
  REBOOT_REQUIRED=1
}

setup_venv() {
  log "Creating/updating Python virtual environment at ${VENV_DIR}"
  if [[ ! -d "${VENV_DIR}" ]]; then
    run_as_user python3 -m venv "${VENV_DIR}" --system-site-packages
  fi

  run_as_user "${VENV_DIR}/bin/pip" install --upgrade pip setuptools wheel
}

install_python_dependencies() {
  log "Installing core Python dependencies..."
  run_as_user "${VENV_DIR}/bin/pip" install \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pyzbar \
    yt-dlp \
    rpi-hardware-pwm

  if ! run_as_user "${VENV_DIR}/bin/python3" -c "import mediapipe" >/dev/null 2>&1; then
    log "Installing mediapipe..."
    if ! run_as_user "${VENV_DIR}/bin/pip" install mediapipe; then
      warn "mediapipe install failed. Trying mediapipe-rpi4 fallback..."
      run_as_user "${VENV_DIR}/bin/pip" install mediapipe-rpi4 || die "Failed to install mediapipe-compatible package."
    fi
  fi

  if ! run_as_user "${VENV_DIR}/bin/python3" -c "import tflite_runtime" >/dev/null 2>&1; then
    warn "tflite_runtime not found. Trying to install (optional but recommended for object_detection mode)."
    if ! run_as_user "${VENV_DIR}/bin/pip" install tflite-runtime; then
      warn "tflite-runtime install failed; object detection mode will fallback/limited."
    fi
  fi

  if [[ ${WITH_TRAINERKIT} -eq 1 ]]; then
    log "Installing TrainerKit requirements (this may take a long time)..."
    if ! run_as_user "${VENV_DIR}/bin/pip" install -r "${PROJECT_DIR}/TrainerKit/requirements.txt"; then
      warn "Some TrainerKit packages failed to install. Core RTKA can still run."
    fi
  fi
}

verify_runtime_imports() {
  log "Verifying core runtime imports..."
  run_as_user "${VENV_DIR}/bin/python3" - <<'PY'
import fastapi
import uvicorn
import cv2
import numpy
import gpiozero
import pyzbar
import yt_dlp
import mediapipe
print("RTKA core import check: OK")
PY
}

install_systemd_services() {
  log "Installing systemd services..."
  ${SUDO} mkdir -p "${PROJECT_DIR}/NetPortal/logs"

  cat <<EOF_SERVICE | ${SUDO} tee /etc/systemd/system/rtka-main.service >/dev/null
[Unit]
Description=RTKA Main API Service
After=network-online.target pigpiod.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/python3 ${PROJECT_DIR}/main.py
Restart=on-failure
RestartSec=2
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF_SERVICE

  cat <<EOF_SERVICE | ${SUDO} tee /etc/systemd/system/netportal.service >/dev/null
[Unit]
Description=RTKA NetPortal Wi-Fi Manager
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}/NetPortal
ExecStart=${VENV_DIR}/bin/python3 ${PROJECT_DIR}/NetPortal/wifi_manager.py
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF_SERVICE

  ${SUDO} systemctl daemon-reload
  ${SUDO} systemctl enable --now rtka-main.service
  ${SUDO} systemctl enable --now netportal.service

  if ! ${SUDO} systemctl is-active --quiet rtka-main.service; then
    warn "rtka-main.service is not active. Check: sudo journalctl -u rtka-main.service -n 100 --no-pager"
  fi

  if ! ${SUDO} systemctl is-active --quiet netportal.service; then
    warn "netportal.service is not active. Check: sudo journalctl -u netportal.service -n 100 --no-pager"
  fi
}

main() {
  log "Project directory: ${PROJECT_DIR}"
  log "Install mode: core RTKA$([[ ${WITH_TRAINERKIT} -eq 1 ]] && printf ' + TrainerKit')"

  install_apt_dependencies
  configure_pwm_overlay
  setup_venv
  install_python_dependencies
  verify_runtime_imports

  if [[ ${INSTALL_SERVICES} -eq 1 ]]; then
    install_systemd_services
  else
    log "Skipping systemd installation (--no-services)."
  fi

  log "Installation complete."
  log "Main API expected on port 8000 (see config.py)."
  log "NetPortal captive portal expected on port 80."

  if [[ ${REBOOT_REQUIRED} -eq 1 ]]; then
    warn "A reboot is recommended to apply PWM overlay changes."
  fi

  cat <<'NEXT'

Useful checks:
  source venv/bin/activate
  python3 main.py
  sudo systemctl status rtka-main.service
  sudo systemctl status netportal.service
NEXT
}

main "$@"
