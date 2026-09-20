# data_ingestion/upload_to_s3.py
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class S3Uploader:
    """Upload data files to AWS S3"""
    
    def __init__(self, bucket_name, region='ap-south-1'):
        self.bucket_name = bucket_name
        self.region = region
        
        # Create S3 client
        self.s3_client = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        print(f"✅ Connected to S3 bucket: {bucket_name}")
    
    def upload_file(self, local_filepath, s3_folder):
        """
        Upload a single file to S3
        
        Args:
            local_filepath (str): Local path to file
            s3_folder (str): Folder in S3 (e.g., 'raw_data')
        
        Returns:
            str: S3 object key (path)
        """
        filename = os.path.basename(local_filepath)
        s3_key = f"{s3_folder}/{filename}"
        
        try:
            print(f"📤 Uploading {filename} to S3...")
            
            self.s3_client.upload_file(
                local_filepath,
                self.bucket_name,
                s3_key
            )
            
            print(f"✅ Uploaded: s3://{self.bucket_name}/{s3_key}")
            return s3_key
        
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None
    
    def upload_folder(self, local_folder, s3_folder):
        """Upload all files from a local folder"""
        
        for filename in os.listdir(local_folder):
            if filename.startswith('.'):
                continue  # Skip hidden files
            
            local_path = os.path.join(local_folder, filename)
            
            if os.path.isfile(local_path):
                self.upload_file(local_path, s3_folder)
    
    def list_files(self, s3_folder):
        """List all files in a folder"""
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=s3_folder
            )
            
            if 'Contents' not in response:
                print(f"No files in {s3_folder}")
                return []
            
            files = [obj['Key'] for obj in response['Contents']]
            
            print(f"\n📁 Files in {s3_folder}:")
            for file in files:
                print(f"   ├─ {file}")
            
            return files
        
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def download_file(self, s3_key, local_filepath):
        """Download a file from S3"""
        
        try:
            print(f"📥 Downloading {s3_key}...")
            
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_filepath
            )
            
            print(f"✅ Downloaded to {local_filepath}")
        
        except Exception as e:
            print(f"❌ Download failed: {e}")


# ============== MAIN EXECUTION ==============

if __name__ == "__main__":
    
    # Configure
    BUCKET_NAME = "stock-weather-analytics-sanzzzworks"  
    
    # Initialize uploader
    uploader = S3Uploader(BUCKET_NAME)
    
    # Step 1: Upload raw data
    print("\n=== UPLOADING RAW DATA ===")
    raw_data_folder = "data_ingestion/raw_data"
    uploader.upload_folder(raw_data_folder, "raw_data")
    
    # Step 2: List files in S3
    print("\n=== VERIFYING UPLOAD ===")
    uploader.list_files("raw_data")
    
    print("\n✅ Data upload to S3 complete!")