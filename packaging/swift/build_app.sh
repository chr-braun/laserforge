#!/bin/bash
# Baut „Steckwerk Desktop.app“ (universell: Apple Silicon und Intel) mit eingebauter Python-Engine.
#
#   ./build_app.sh [Zielordner]               App bauen (Default: ../dist), nur auf macOS
#   ./build_app.sh --engine-only <Ordner>     nur die Engine-Dateien kopieren (zum Prüfen, auch unter Linux)
#
# Die App ist ad hoc signiert, nicht notarisiert: beim ersten Start einmal unter
# Systemeinstellungen → Datenschutz & Sicherheit → „Dennoch öffnen“ freigeben.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
EXE="SteckwerkDesktop"

copy_engine() {
  local dest="$1"
  mkdir -p "$dest"
  # Dieselben Dateien wie die bestehende Mac-App (packaging/build_macos.py) plus das Startskript.
  (cd "$ROOT" && python3 -c 'import sys; sys.path.insert(0, "packaging"); import build_macos; print("\n".join(build_macos.code_files()))') |
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      mkdir -p "$dest/$(dirname "$f")"
      cp "$ROOT/$f" "$dest/$f"
    done
  cp "$HERE/bridge_start.py" "$dest/bridge_start.py"
}

if [ "${1:-}" = "--engine-only" ]; then
  [ -n "${2:-}" ] || { echo "Zielordner fehlt" >&2; exit 2; }
  copy_engine "$2"
  echo "Engine kopiert nach $2"
  exit 0
fi

if [ "$(uname)" != "Darwin" ]; then
  echo "Das App-Bundle lässt sich nur auf macOS bauen (SwiftUI/AppKit)." >&2
  exit 1
fi

OUT="${1:-$HERE/../dist}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
APP="$OUT/Steckwerk Desktop.app"
VERSION="$(cd "$ROOT" && python3 -c 'from steckwerk import __version__; print(__version__)')"

ARCH_FLAGS=()
for a in ${STECKWERK_ARCHS:-arm64 x86_64}; do
  ARCH_FLAGS+=(--arch "$a")
done

cd "$HERE"
swift build -c release "${ARCH_FLAGS[@]}"
BIN_DIR="$(swift build -c release "${ARCH_FLAGS[@]}" --show-bin-path)"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BIN_DIR/$EXE" "$APP/Contents/MacOS/$EXE"
copy_engine "$APP/Contents/Resources/engine"
cp "$ROOT/packaging/macos/Steckwerk.icns" "$APP/Contents/Resources/Steckwerk.icns"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key><string>de</string>
  <key>CFBundleName</key><string>Steckwerk Desktop</string>
  <key>CFBundleDisplayName</key><string>Steckwerk Desktop</string>
  <key>CFBundleIdentifier</key><string>de.steckwerk.desktop</string>
  <key>CFBundleExecutable</key><string>$EXE</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>CFBundleVersion</key><string>$VERSION</string>
  <key>CFBundleIconFile</key><string>Steckwerk</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>LSApplicationCategoryType</key><string>public.app-category.productivity</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSPrincipalClass</key><string>NSApplication</string>
  <key>NSDocumentsFolderUsageDescription</key><string>Steckwerk speichert Schnittdateien und Prüfberichte im Ordner Dokumente/Steckwerk.</string>
</dict>
</plist>
PLIST

codesign --force --deep --sign - "$APP"
echo "Fertig: $APP (Version $VERSION, $(lipo -archs "$APP/Contents/MacOS/$EXE"))"
