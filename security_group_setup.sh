# security_group_setup.sh - AWS Security Group setup helper
#!/bin/bash

echo "🛡️ AWS Security Group Setup Helper"
echo "=================================="

# Get current public IP
PUBLIC_IP=$(curl -s https://checkip.amazonaws.com)
echo "Your current public IP: $PUBLIC_IP"

echo ""
echo "You need to allow port 8501 in your EC2 security group."
echo "Run these AWS CLI commands (or use AWS Console):"
echo ""

# Get instance ID
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
echo "Instance ID: $INSTANCE_ID"

# Get security group ID
if command -v aws &> /dev/null; then
    SG_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text)
    echo "Security Group ID: $SG_ID"
    
    echo ""
    echo "Command to allow Streamlit port 8501:"
    echo "aws ec2 authorize-security-group-ingress \\"
    echo "    --group-id $SG_ID \\"
    echo "    --protocol tcp \\"
    echo "    --port 8501 \\"
    echo "    --cidr $PUBLIC_IP/32"
    echo ""
    echo "Or to allow from anywhere (less secure):"
    echo "aws ec2 authorize-security-group-ingress \\"
    echo "    --group-id $SG_ID \\"
    echo "    --protocol tcp \\"
    echo "    --port 8501 \\"
    echo "    --cidr 0.0.0.0/0"
else
    echo "AWS CLI not found. Please configure security group manually."
fi