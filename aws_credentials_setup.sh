# aws_credentials_setup.sh - Helper script for AWS credentials
#!/bin/bash

echo "🔐 AWS Credentials Setup Helper"
echo "=============================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "📦 Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

echo ""
echo "Please enter your AWS credentials:"
echo "(You can get these from AWS Console > IAM > Users > Security Credentials)"
echo ""

read -p "AWS Access Key ID: " access_key
read -s -p "AWS Secret Access Key: " secret_key
echo ""
read -p "Default region (e.g., us-east-1): " region

# Create AWS credentials file
mkdir -p ~/.aws
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = $access_key
aws_secret_access_key = $secret_key
EOF

cat > ~/.aws/config << EOF
[default]
region = $region
output = json
EOF

echo "✅ AWS credentials configured successfully!"
echo "🧪 Testing AWS connection..."

if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✅ AWS connection successful!"
else
    echo "❌ AWS connection failed. Please check your credentials."
fi
