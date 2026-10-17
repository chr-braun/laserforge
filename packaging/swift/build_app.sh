#!/bin/bash
set -e

DEST_DIR="${1:-.}"
PRODUCT_NAME="Steckwerk Desktop"
BUNDLE_NAME="SteckwerkDesktop"
BUNDLE_ID="de.steckwerk.desktop"
VERSION="1.0.0"
BUILD_DIR=".build/release"

echo "Building $PRODUCT_NAME..."

swift build -c release

echo "Creating app bundle..."

APP_BUNDLE="$DEST_DIR/$PRODUCT_NAME.app"
CONTENTS="$APP_BUNDLE/Contents"
MACOS_DIR="$CONTENTS/MacOS"

mkdir -p "$MACOS_DIR"
mkdir -p "$CONTENTS/Resources"

cp "$BUILD_DIR/$BUNDLE_NAME" "$MACOS_DIR/"

cat > "$CONTENTS/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>de_DE</string>
  <key>CFBundleExecutable</key>
  <string>SteckwerkDesktop</string>
  <key>CFBundleIdentifier</key>
  <string>de.steckwerk.desktop</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>Steckwerk Desktop</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>14.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
  <key>NSRequiresIPhoneOS</key>
  <false/>
</dict>
</plist>
EOF

chmod +x "$MACOS_DIR/$BUNDLE_NAME"

echo "Created $APP_BUNDLE"
echo "Build complete."
