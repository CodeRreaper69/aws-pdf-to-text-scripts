import streamlit as st
import boto3
import os
import json
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
import pandas as pd
from botocore.exceptions import ClientError, NoCredentialsError
import hashlib

# Import your existing extractor (assuming it's in the same directory)
# from aws_auto_healing_extractor import AWSAutoHealingExtractor

# For now, I'll include a simplified version of the key functions
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import re
from typing import Dict, List, Any, Optional

class AWSAutoHealingExtractor:
    def __init__(self):
        self.aws_services_pattern = r'\b(EC2|S3|RDS|Lambda|CloudFormation|ECS|EKS|IAM|VPC|CloudWatch|SNS|SQS|DynamoDB|Route53|ELB|ALB|NLB|API Gateway|Cognito|CloudFront|ElastiCache|Redshift|EMR|Glue|Step Functions|SageMaker|Bedrock|CodeBuild|CodeDeploy|CodePipeline|Systems Manager|SSM|Parameter Store|Secrets Manager|KMS|ACM|WAF|Shield|GuardDuty|Security Hub|Config|CloudTrail|X-Ray|EventBridge|Kinesis|MSK|OpenSearch|DocumentDB|Aurora|Neptune|QLDB|Timestream|AppSync|Amplify|Auto Scaling|Elastic Beanstalk|Batch|Fargate)\b'
        
        self.auto_healing_patterns = {
            'error_scenarios': r'(?i)(error|failed|failure|exception|timeout|connection\s*refused|access\s*denied|not\s*found|unavailable|down|outage)',
            'solution_patterns': r'(?i)(solution|fix|resolve|remediation|workaround|recovery|restore|restart|retry|rollback)',
            'monitoring_alerts': r'(?i)(alert|alarm|threshold|metric|monitoring|dashboard|notification|trigger)',
            'troubleshooting': r'(?i)(troubleshoot|diagnose|investigate|debug|check|verify|validate|test)',
            'automation': r'(?i)(automate|script|lambda|function|trigger|schedule|cron|event\s*driven)',
            'health_checks': r'(?i)(health\s*check|status|ping|probe|heartbeat|availability|uptime)',
            'scaling_actions': r'(?i)(scale\s*up|scale\s*down|auto\s*scaling|capacity|instance|load|cpu|memory)',
            'recovery_procedures': r'(?i)(backup|snapshot|restore|failover|disaster\s*recovery|DR|redundancy)'
        }

    def extract_text_from_image(self, image_data: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(image_data))
            image = image.convert('RGB')
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except Exception as e:
            st.error(f"OCR failed: {e}")
            return ""

    def identify_auto_healing_content(self, text: str) -> Dict[str, Any]:
        content_analysis = {
            'content_types': [],
            'error_scenarios': [],
            'solutions': [],
            'automation_opportunities': [],
            'priority_score': 0
        }
        
        for pattern_type, pattern in self.auto_healing_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                content_analysis['content_types'].append(pattern_type)
                content_analysis['priority_score'] += len(matches)
        
        return content_analysis

    def extract_aws_services(self, text: str) -> List[str]:
        services = set(re.findall(self.aws_services_pattern, text, re.IGNORECASE))
        return list(services)

    def extract_actionable_content(self, text: str) -> Dict[str, Any]:
        actionable_content = {
            'procedures': [],
            'commands': [],
            'conditions': [],
            'thresholds': [],
            'configurations': []
        }
        
        # Extract step-by-step procedures
        step_patterns = [
            r'(?i)(?:step\s*)?(\d+)[\.\:\-\s]+([^\n]+(?:\n(?!\s*(?:step\s*)?\d+[\.\:\-])[^\n]*)*)',
            r'(?i)(first|then|next|finally|lastly)[,\s]+([^\n\.]+)',
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    actionable_content['procedures'].append({
                        'step': match[0],
                        'action': match[1].strip()
                    })
        
        # Extract AWS CLI commands
        command_patterns = [
            r'(?:^|\n)\s*(?:\$\s*|aws\s+|sudo\s+|docker\s+|kubectl\s+|terraform\s+)([^\n]+)',
            r'(?i)(aws\s+\w+\s+[^\n]+)',
        ]
        
        for pattern in command_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            actionable_content['commands'].extend(matches)
        
        return actionable_content

    def process_pdf_for_auto_healing(self, pdf_path: str) -> Dict[str, Any]:
        try:
            doc = fitz.open(pdf_path)
            pdf_name = Path(pdf_path).stem
            
            extraction_data = {
                'metadata': {
                    'source_file': pdf_name,
                    'extraction_date': datetime.now().isoformat(),
                    'total_pages': len(doc),
                    'document_title': doc.metadata.get('title', pdf_name),
                    'extraction_type': 'auto_healing_focused'
                },
                'consolidated_text': "",
                'auto_healing_scenarios': [],
                'aws_services_found': set(),
                'training_examples': [],
                'high_priority_content': []
            }
            
            all_text_content = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                # Process images with OCR
                image_list = page.get_images(full=True)
                ocr_text_from_page = ""
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.width < 50 or pix.height < 50:
                            pix = None
                            continue
                        
                        img_data = pix.tobytes("png")
                        ocr_text = self.extract_text_from_image(img_data)
                        
                        if ocr_text:
                            ocr_text_from_page += f"\n[OCR from Image {img_index + 1}]: {ocr_text}\n"
                        
                        pix = None
                        
                    except Exception as e:
                        st.warning(f"Error processing image {img_index + 1} on page {page_num + 1}: {e}")
                
                combined_page_text = page_text + ocr_text_from_page
                all_text_content.append(combined_page_text)
                
                # Analyze content for auto healing relevance
                auto_healing_analysis = self.identify_auto_healing_content(combined_page_text)
                
                if auto_healing_analysis['priority_score'] > 0:
                    page_scenario = {
                        'page_number': page_num + 1,
                        'text_content': combined_page_text,
                        'aws_services': self.extract_aws_services(combined_page_text),
                        'auto_healing_analysis': auto_healing_analysis,
                        'actionable_content': self.extract_actionable_content(combined_page_text)
                    }
                    
                    extraction_data['auto_healing_scenarios'].append(page_scenario)
                    extraction_data['aws_services_found'].update(page_scenario['aws_services'])
                    
                    if auto_healing_analysis['priority_score'] > 3:
                        extraction_data['high_priority_content'].append(page_scenario)
                
                # Update progress
                progress = (page_num + 1) / len(doc)
                progress_bar.progress(progress)
                status_text.text(f"Processing page {page_num + 1}/{len(doc)} (Priority Score: {auto_healing_analysis['priority_score']})")
            
            doc.close()
            
            extraction_data['consolidated_text'] = "\n\n".join(all_text_content)
            extraction_data['aws_services_found'] = list(extraction_data['aws_services_found'])
            
            # Generate training examples
            self.generate_auto_healing_training_data(extraction_data)
            
            return extraction_data
            
        except Exception as e:
            st.error(f"Error processing PDF: {e}")
            return None

    def generate_auto_healing_training_data(self, extraction_data: Dict[str, Any]) -> None:
        training_examples = []
        
        # Problem-Solution pairs
        for scenario in extraction_data['auto_healing_scenarios']:
            if scenario['auto_healing_analysis']['error_scenarios'] and scenario['actionable_content']['procedures']:
                
                error_context = " ".join(scenario['auto_healing_analysis']['error_scenarios'][:3])
                solution_steps = "\n".join([f"{proc['step']}. {proc['action']}" 
                                          for proc in scenario['actionable_content']['procedures'][:5]])
                
                training_example = {
                    "instruction": "Provide an auto healing solution for this AWS issue",
                    "input": f"Problem: {error_context}\nAWS Services: {', '.join(scenario['aws_services'])}",
                    "output": solution_steps,
                    "metadata": {
                        "source_page": scenario['page_number'],
                        "priority_score": scenario['auto_healing_analysis']['priority_score'],
                        "aws_services": scenario['aws_services'],
                        "content_types": scenario['auto_healing_analysis']['content_types']
                    }
                }
                training_examples.append(training_example)
        
        # Command-based examples
        for scenario in extraction_data['auto_healing_scenarios']:
            if scenario['actionable_content']['commands']:
                command_text = "\n".join(scenario['actionable_content']['commands'][:5])
                
                training_example = {
                    "instruction": "What AWS CLI commands would help resolve this issue?",
                    "input": f"AWS Services: {', '.join(scenario['aws_services'])}\nContext: Auto healing scenario",
                    "output": command_text,
                    "metadata": {
                        "source_page": scenario['page_number'],
                        "command_count": len(scenario['actionable_content']['commands'])
                    }
                }
                training_examples.append(training_example)
        
        extraction_data['training_examples'] = training_examples

class S3Manager:
    def __init__(self):
        try:
            self.s3_client = boto3.client('s3')
            self.bucket_name = None
        except NoCredentialsError:
            st.error("AWS credentials not found. Please configure your AWS credentials.")
            self.s3_client = None

    def list_buckets(self):
        if not self.s3_client:
            return []
        try:
            response = self.s3_client.list_buckets()
            return [bucket['Name'] for bucket in response['Buckets']]
        except ClientError as e:
            st.error(f"Error listing buckets: {e}")
            return []

    def create_bucket(self, bucket_name, region='us-east-1'):
        if not self.s3_client:
            return False
        try:
            if region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            return True
        except ClientError as e:
            st.error(f"Error creating bucket: {e}")
            return False

    def upload_training_data_to_s3(self, bucket_name: str, extraction_data: Dict[str, Any], pdf_name: str) -> bool:
        if not self.s3_client:
            return False
        
        try:
            # Create a unique folder name based on PDF name and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"training_data/{pdf_name}_{timestamp}"
            
            # Upload training data as JSONL
            training_jsonl = "\n".join([json.dumps(item, ensure_ascii=False) 
                                      for item in extraction_data['training_examples']])
            
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=f"{folder_name}/auto_healing_training.jsonl",
                Body=training_jsonl.encode('utf-8'),
                ContentType='application/jsonl'
            )
            
            # Upload consolidated text
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=f"{folder_name}/consolidated_text.txt",
                Body=extraction_data['consolidated_text'].encode('utf-8'),
                ContentType='text/plain'
            )
            
            # Upload high priority scenarios
            if extraction_data['high_priority_content']:
                priority_json = json.dumps(extraction_data['high_priority_content'], 
                                         indent=2, ensure_ascii=False)
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=f"{folder_name}/high_priority_scenarios.json",
                    Body=priority_json.encode('utf-8'),
                    ContentType='application/json'
                )
            
            # Upload summary
            summary = {
                "extraction_summary": {
                    "total_pages": extraction_data['metadata']['total_pages'],
                    "auto_healing_scenarios": len(extraction_data['auto_healing_scenarios']),
                    "high_priority_scenarios": len(extraction_data['high_priority_content']),
                    "training_examples": len(extraction_data['training_examples']),
                    "aws_services_found": extraction_data['aws_services_found'],
                    "total_text_length": len(extraction_data['consolidated_text'])
                }
            }
            
            summary_json = json.dumps(summary, indent=2, ensure_ascii=False)
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=f"{folder_name}/extraction_summary.json",
                Body=summary_json.encode('utf-8'),
                ContentType='application/json'
            )
            
            st.success(f"✅ Training data uploaded to S3: s3://{bucket_name}/{folder_name}/")
            return True
            
        except ClientError as e:
            st.error(f"Error uploading to S3: {e}")
            return False

def main():
    st.set_page_config(
        page_title="AWS Auto-Healing PDF Processor",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 AWS Auto-Healing PDF Processor")
    st.markdown("Convert AWS runbook PDFs into LLM training data and store in S3")
    
    # Initialize components
    extractor = AWSAutoHealingExtractor()
    s3_manager = S3Manager()
    
    # Sidebar for AWS configuration
    with st.sidebar:
        st.header("AWS Configuration")
        
        # S3 Bucket selection/creation
        buckets = s3_manager.list_buckets()
        
        if buckets:
            bucket_option = st.selectbox(
                "Select S3 Bucket",
                ["Select existing bucket..."] + buckets + ["Create new bucket"]
            )
            
            if bucket_option == "Create new bucket":
                new_bucket_name = st.text_input("New bucket name")
                region = st.selectbox("Region", ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"])
                
                if st.button("Create Bucket"):
                    if new_bucket_name:
                        if s3_manager.create_bucket(new_bucket_name, region):
                            st.success(f"Bucket '{new_bucket_name}' created successfully!")
                            st.rerun()
                    else:
                        st.error("Please enter a bucket name")
            
            elif bucket_option != "Select existing bucket...":
                selected_bucket = bucket_option
                st.success(f"Selected bucket: {selected_bucket}")
        else:
            st.error("No S3 buckets found or AWS credentials not configured")
            selected_bucket = None
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Upload AWS Runbook PDF")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload AWS runbook PDFs to extract auto-healing training data"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
            
            # Process button
            if st.button("🔄 Process PDF", type="primary", use_container_width=True):
                if not s3_manager.s3_client:
                    st.error("AWS credentials not configured. Cannot upload to S3.")
                elif 'selected_bucket' not in locals() or not selected_bucket:
                    st.error("Please select an S3 bucket first.")
                else:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Process the PDF
                        st.info("🔄 Processing PDF for auto-healing training data...")
                        extraction_data = extractor.process_pdf_for_auto_healing(tmp_file_path)
                        
                        if extraction_data:
                            # Display results
                            with col2:
                                st.header("📊 Extraction Results")
                                
                                metrics_col1, metrics_col2 = st.columns(2)
                                
                                with metrics_col1:
                                    st.metric("Total Pages", extraction_data['metadata']['total_pages'])
                                    st.metric("Auto Healing Scenarios", len(extraction_data['auto_healing_scenarios']))
                                    st.metric("Training Examples", len(extraction_data['training_examples']))
                                
                                with metrics_col2:
                                    st.metric("High Priority Scenarios", len(extraction_data['high_priority_content']))
                                    st.metric("AWS Services Found", len(extraction_data['aws_services_found']))
                                    st.metric("Text Length", f"{len(extraction_data['consolidated_text']):,}")
                                
                                if extraction_data['aws_services_found']:
                                    st.subheader("🔧 AWS Services Found")
                                    for service in extraction_data['aws_services_found']:
                                        st.badge(service)
                            
                            # Upload to S3
                            st.info("☁️ Uploading training data to S3...")
                            pdf_name = Path(uploaded_file.name).stem
                            
                            if s3_manager.upload_training_data_to_s3(selected_bucket, extraction_data, pdf_name):
                                st.success("🎉 Training data successfully processed and uploaded to S3!")
                                
                                # Show sample training data
                                if extraction_data['training_examples']:
                                    st.subheader("📝 Sample Training Data")
                                    sample_example = extraction_data['training_examples'][0]
                                    
                                    st.json({
                                        "instruction": sample_example["instruction"],
                                        "input": sample_example["input"][:200] + "..." if len(sample_example["input"]) > 200 else sample_example["input"],
                                        "output": sample_example["output"][:200] + "..." if len(sample_example["output"]) > 200 else sample_example["output"]
                                    })
                        else:
                            st.error("Failed to process PDF. Please check the file and try again.")
                    
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_file_path)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Tip**: This tool extracts auto-healing scenarios, troubleshooting steps, "
        "AWS CLI commands, and monitoring thresholds from your runbooks to create "
        "high-quality training data for LLM fine-tuning."
    )

if __name__ == "__main__":
    main()