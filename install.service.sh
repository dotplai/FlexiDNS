#!/bin/bash
echo "Installing systemd service..."

SYSTEMD_SERVICE="/etc/systemd/system/"
LOCAL_SERVICE="$(pwd)/services/"

SERVICE_RUNTIME="rxt.sh"
TEMPORARY_SERVICE="${LOCAL_SERVICE}flexidns.service"

# create service file dynamically.
cat <<EOL > $TEMPORARY_SERVICE
[Unit]
Description=FlexiDNS Service
After=network.target

[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=${LOCAL_SERVICE}${SERVICE_RUNTIME}
Restart=on-failure
User=$USER

[Install]
WantedBy=multi-user.target
EOL

echo "----- start of service file -----"
cat $TEMPORARY_SERVICE
echo "-----  end of service file  -----"

echo "If you want to change the service script, please edit the script before continue."
echo "At ${TEMPORARY_SERVICE}"
read -p "Press Enter to continue..."

# Loop through all service files
for SERVICE in "$LOCAL_SERVICE"*.service; do
    SERVICE_NAME=$(basename "$SERVICE")
    SERVICE_PATH="$SYSTEMD_SERVICE$SERVICE_NAME"
    
    if [[ -f "$SERVICE_PATH" ]]; then
        echo "Service $SERVICE_NAME already exists. Skipping installation."
    else
        sudo cp "$SERVICE" "$SERVICE_PATH"
        sudo systemctl daemon-reload
        echo "Systemd reloaded."
        sudo systemctl enable "$SERVICE_NAME"
        sudo systemctl start "$SERVICE_NAME"
        echo "Service $SERVICE_NAME installed and started."
    fi
done