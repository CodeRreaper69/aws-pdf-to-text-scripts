# systemd_service.sh - Create systemd service for auto-start
#!/bin/bash

echo "⚙️ Creating systemd service for auto-start..."

# Get current user
USER=$(whoami)
HOME_DIR=$(eval echo ~$USER)

# Create systemd service file
sudo tee /etc/systemd/system/aws-pdf-processor.service > /dev/null << EOF
[Unit]
Description=AWS PDF Processor Streamlit App
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME_DIR/aws-pdf-processor
Environment=PATH=$HOME_DIR/aws-pdf-processor/venv/bin
ExecStart=$HOME_DIR/aws-pdf-processor/venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable aws-pdf-processor.service

echo "✅ Systemd service created and enabled!"
echo ""
echo "📋 Service commands:"
echo "Start:   sudo systemctl start aws-pdf-processor"
echo "Stop:    sudo systemctl stop aws-pdf-processor"
echo "Status:  sudo systemctl status aws-pdf-processor"
echo "Logs:    sudo journalctl -u aws-pdf-processor -f"