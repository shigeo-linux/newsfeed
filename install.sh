#!/bin/bash
set -e

APP_NAME="newsfeed"
INSTALL_DIR="/opt/${APP_NAME}"
DESKTOP_DIR="/usr/share/applications"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=== Installing ${APP_NAME} ==="

sudo apt-get update -qq
sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-requests

pip3 install --user --break-system-packages feedparser 2>/dev/null || true

echo "Copying application files..."
sudo mkdir -p "${INSTALL_DIR}"
sudo cp -r "$(dirname "$0")"/* "${INSTALL_DIR}/"
sudo chmod +x "${INSTALL_DIR}/newsfeed.py"
sudo chmod +x "${INSTALL_DIR}/runner.py"

echo "Installing icon..."
sudo mkdir -p /usr/share/icons/hicolor/scalable/apps
sudo cp "${INSTALL_DIR}/newsfeed.svg" /usr/share/icons/hicolor/scalable/apps/newsfeed.svg
sudo gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true

echo "Installing desktop entry..."
sudo cp "${INSTALL_DIR}/newsfeed.desktop" "${DESKTOP_DIR}/"
sudo update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true

echo "Creating launcher..."
sudo tee /usr/local/bin/newsfeed > /dev/null << 'EOF'
#!/bin/bash
exec python3 /opt/newsfeed/newsfeed.py "$@"
EOF
sudo chmod +x /usr/local/bin/newsfeed

echo "Installing systemd user timer..."
mkdir -p "${SYSTEMD_USER_DIR}"
cp "${INSTALL_DIR}/newsfeed.service" "${SYSTEMD_USER_DIR}/newsfeed.service"
cp "${INSTALL_DIR}/newsfeed.timer" "${SYSTEMD_USER_DIR}/newsfeed.timer"
systemctl --user daemon-reload
systemctl --user enable newsfeed.timer
systemctl --user start newsfeed.timer

echo ""
echo "=== Installation complete! ==="
echo "Run: newsfeed"
echo ""
echo "Next steps:"
echo "  1. Enter your Telegram token and chat ID"
echo "  2. Enter your OpenRouter API key"
echo "  3. Add or remove RSS feeds"
echo "  4. Set your morning (and optional evening) briefing time"
echo "  5. Click 'Send Briefing Now' to test"
