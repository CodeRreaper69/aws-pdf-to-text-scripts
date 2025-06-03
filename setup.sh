# setup.sh - Run this on your EC2 instance
#!/bin/bash

echo "🚀 Setting up AWS Auto-Healing PDF Processor on EC2"
echo "=================================================="

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip if not already installed
echo "🐍 Installing Python and pip..."
sudo apt install python3 python3-pip python3-venv -y

# Install Tesseract OCR
echo "🔍 Installing Tesseract OCR..."
sudo apt install tesseract-ocr -y
sudo apt install libtesseract-dev -y

# Install system dependencies for PIL/Pillow
echo "🖼️ Installing image processing dependencies..."
sudo apt install libjpeg-dev zlib1g-dev -y

# Create project directory
echo "📁 Creating project directory..."
mkdir -p ~/aws-pdf-processor
cd ~/aws-pdf-processor

# Create virtual environment
echo "🏗️ Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install streamlit==1.29.0
pip install boto3==1.34.0
pip install PyMuPDF==1.23.0
pip install Pillow==10.1.0
pip install pytesseract==0.3.10
pip install pandas==2.1.4

# Create AWS credentials directory (if not exists)
echo "🔐 Setting up AWS credentials directory..."
mkdir -p ~/.aws

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Configure AWS credentials:"
echo "   aws configure"
echo "   (or edit ~/.aws/credentials manually)"
echo ""
echo "2. Start the Streamlit app:"
echo "   cd ~/aws-pdf-processor"
echo "   source venv/bin/activate"
echo "   streamlit run app.py --server.address 0.0.0.0 --server.port 8501"
echo ""
echo "3. Access the app at: http://YOUR_EC2_PUBLIC_IP:8501"
echo ""
echo "🔥 Make sure to configure security group to allow port 8501!"