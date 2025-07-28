#!/bin/bash

echo "🔧 Installing FlexiDNS systemd service..."

SYSTEMD_DIR="/etc/systemd/system/"
LOCAL_DIR="$(pwd)/services/"
SERVICE_NAME="FlexiDns.service"
SERVICE_EXEC="rxt.sh"
TEMP_SERVICE="${LOCAL_DIR}${SERVICE_NAME}"
DEFAULT_USER="$USER"

# Check if template service file exists
if [[ -f "$TEMP_SERVICE" ]]; then
    echo "⚠️  Template service file already exists at: $TEMP_SERVICE"
    read -p "Override it? (y/n): " OVERWRITE
    case "$OVERWRITE" in
        [Yy])
            ;;
        [Nn])
            echo "ℹ️ Keeping existing service template."
            ;;
        *)
            echo "❌ Invalid input. Please enter 'y' or 'n'."
            exit 1
            ;;
    esac
else
    OVERWRITE="y"
fi

# Create or overwrite the service file
if [[ "$OVERWRITE" =~ ^[Yy]$ ]]; then
    cat <<EOF > "$TEMP_SERVICE"
[Unit]
Description=FlexiDNS WAN Resolver Service
Documentation=
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=${LOCAL_DIR}${SERVICE_EXEC}
Restart=on-failure
User=${DEFAULT_USER}

[Install]
WantedBy=multi-user.target
EOF
    echo "✅ Service template created at: $TEMP_SERVICE"
fi

echo "----- start of service file -----"
cat "$TEMP_SERVICE"
echo "-----  end of service file  -----"

read -p "➡️ Press Enter to continue installing..."

# Install and activate the service
for SERVICE_FILE in "$LOCAL_DIR"*.service; do
    BASENAME=$(basename "$SERVICE_FILE")
    TARGET_PATH="${SYSTEMD_DIR}${BASENAME}"

    if [[ -f "$TARGET_PATH" ]]; then
        echo "🟡 $BASENAME already exists in systemd."

        # Reinstall confirmation
        read -p "Do you want to reinstall it? (y/n): " REINSTALL
        case "$REINSTALL" in
            [Yy])
                sudo cp "$SERVICE_FILE" "$TARGET_PATH"
                sudo systemctl daemon-reload
                sudo systemctl enable "$BASENAME"
                sudo systemctl restart "$BASENAME"

                echo "✅ Reinstalled and restarted: $BASENAME"
                ;;
            [Nn])
                ;;
            *)
                echo "❌ Invalid input. Please enter 'y' or 'n'."
                exit 1
                ;;
        esac
    else
        sudo cp "$SERVICE_FILE" "$TARGET_PATH"
        sudo systemctl daemon-reload
        sudo systemctl enable "$BASENAME"
        sudo systemctl start "$BASENAME"
        echo "✅ Installed and started: $BASENAME"
    fi
done
