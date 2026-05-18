#!/bin/bash
set -e

APP_NAME="newsfeed"
INSTALL_DIR="/opt/${APP_NAME}"
DESKTOP_DIR="/usr/share/applications"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=== Installing ${APP_NAME} ==="

sudo apt-get update -qq
sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-requests python3-venv librsvg2-bin

echo "Copying application files..."
sudo mkdir -p "${INSTALL_DIR}"
sudo cp -r "$(dirname "$0")"/* "${INSTALL_DIR}/"
sudo chmod +x "${INSTALL_DIR}/newsfeed.py"
sudo chmod +x "${INSTALL_DIR}/runner.py"

echo "Creating virtual environment..."
sudo python3 -m venv --system-site-packages "${INSTALL_DIR}/venv"
sudo "${INSTALL_DIR}/venv/bin/pip" install --quiet feedparser

echo "Installing icon..."
sudo mkdir -p /usr/share/icons/hicolor/scalable/apps
sudo mkdir -p /usr/share/icons/hicolor/48x48/apps
sudo mkdir -p /usr/share/icons/hicolor/256x256/apps
sudo cp "${INSTALL_DIR}/newsfeed.svg" /usr/share/icons/hicolor/scalable/apps/newsfeed.svg
rsvg-convert -w 48 -h 48 "${INSTALL_DIR}/newsfeed.svg" | sudo tee /usr/share/icons/hicolor/48x48/apps/newsfeed.png > /dev/null
rsvg-convert -w 256 -h 256 "${INSTALL_DIR}/newsfeed.svg" | sudo tee /usr/share/icons/hicolor/256x256/apps/newsfeed.png > /dev/null
sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo "Installing desktop entry..."
sudo cp "${INSTALL_DIR}/newsfeed.desktop" "${DESKTOP_DIR}/"
sudo update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true

echo "Creating launcher..."
sudo tee /usr/local/bin/newsfeed > /dev/null << 'EOF'
#!/bin/bash
exec /opt/newsfeed/venv/bin/python3 /opt/newsfeed/newsfeed.py "$@"
EOF
sudo chmod +x /usr/local/bin/newsfeed

echo "Creating config directory..."
mkdir -p "$HOME/.config/${APP_NAME}"

echo "Installing systemd user timer..."
mkdir -p "${SYSTEMD_USER_DIR}"
cp "${INSTALL_DIR}/newsfeed.service" "${SYSTEMD_USER_DIR}/newsfeed.service"
cp "${INSTALL_DIR}/newsfeed.timer" "${SYSTEMD_USER_DIR}/newsfeed.timer"
sudo loginctl enable-linger "$(whoami)"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
if systemctl --user daemon-reload 2>/dev/null; then
    systemctl --user enable newsfeed.timer
    systemctl --user start newsfeed.timer
else
    echo "Note: Timer files installed. Run 'systemctl --user enable --now newsfeed.timer' after logging in."
fi

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
