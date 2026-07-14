#!/usr/bin/env bash
set -euo pipefail

APP_NAME="DadR3x Command Center"
VERSION="${1:-local}"
PLATFORM_LABEL="${2:-Auto}"
ARCH_LABEL="${3:-$(uname -m)}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$ROOT_DIR"

if [[ "$PLATFORM_LABEL" == "Auto" ]]; then
  if [[ "$ARCH_LABEL" == "arm64" ]]; then
    PLATFORM_LABEL="AppleSilicon"
  else
    PLATFORM_LABEL="Intel"
  fi
fi

ZIP_NAME="DadR3x_Command_Center_${VERSION}_macOS_${PLATFORM_LABEL}_${ARCH_LABEL}.zip"

echo "Building macOS app"
echo "Version: ${VERSION}"
echo "Platform label: ${PLATFORM_LABEL}"
echo "Architecture label: ${ARCH_LABEL}"
echo "Python: $(python --version)"
echo "Machine: $(uname -m)"
echo "Spec: DadR3xCommandCenter.spec"

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

rm -rf dist release .pyinstaller_build
pyinstaller --noconfirm --workpath .pyinstaller_build DadR3xCommandCenter.spec

mkdir -p release

if [[ -d "dist/${APP_NAME}.app" ]]; then
  ditto -c -k --sequesterRsrc --keepParent "dist/${APP_NAME}.app" "release/${ZIP_NAME}"
elif [[ -d "dist/${APP_NAME}" ]]; then
  ditto -c -k --sequesterRsrc --keepParent "dist/${APP_NAME}" "release/${ZIP_NAME}"
else
  echo "ERROR: Build output not found."
  echo "Dist contents:"
  find dist -maxdepth 4 -type f -o -type d || true
  exit 1
fi

cd release
shasum -a 256 "${ZIP_NAME}" > "${ZIP_NAME}.sha256"

echo "Built release/${ZIP_NAME}"
