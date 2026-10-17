#!/bin/bash
set -e

OUTPUT_DIR="${1:-.}"
BUNDLE_NAME="Steckwerk Desktop.app"
BUNDLE_PATH="$OUTPUT_DIR/$BUNDLE_NAME"
CONTENTS_DIR="$BUNDLE_PATH/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

echo "Building Swift app..."
swift build -v --configuration release

echo "Creating app bundle structure..."
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

echo "Copying executable..."
cp ".build/release/SteckwerkDesktop" "$MACOS_DIR/Steckwerk Desktop"
chmod +x "$MACOS_DIR/Steckwerk Desktop"

echo "Creating Info.plist..."
cat > "$CONTENTS_DIR/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>de_DE</string>
	<key>CFBundleExecutable</key>
	<string>Steckwerk Desktop</string>
	<key>CFBundleIdentifier</key>
	<string>de.steckwerk.desktop</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundleName</key>
	<string>Steckwerk Desktop</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>2.8.0</string>
	<key>CFBundleVersion</key>
	<string>1</string>
	<key>LSMinimumSystemVersion</key>
	<string>14.0</string>
	<key>NSHighResolutionCapable</key>
	<true/>
	<key>NSPrincipalClass</key>
	<string>NSApplication</string>
</dict>
</plist>
EOF

echo "App bundle created at: $BUNDLE_PATH"
