import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app

class S3Service:
    def __init__(self):
        self.client = None
        self.bucket = None
        self._connect()

    def _connect(self):
        try:
            self.client = boto3.client(
                's3',
                aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                region_name=current_app.config.get('AWS_S3_REGION', 'us-east-1')
            )
            self.bucket = current_app.config.get('AWS_S3_BUCKET')
        except NoCredentialsError:
            current_app.logger.warning("AWS credentials not configured.")

    def upload_file(self, file_data, s3_key, content_type='application/octet-stream'):
        if not self.client or not self.bucket:
            current_app.logger.error("S3 not configured")
            return None
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type,
                ServerSideEncryption='AES256'
            )
            return s3_key
        except ClientError as e:
            current_app.logger.error(f"S3 upload failed: {e}")
            return None

    def download_file(self, s3_key):
        if not self.client or not self.bucket:
            current_app.logger.error("S3 not configured")
            return None
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=s3_key)
            return response['Body'].read()
        except ClientError as e:
            current_app.logger.error(f"S3 download failed: {e}")
            return None

    def delete_file(self, s3_key):
        if not self.client or not self.bucket:
            return False
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            current_app.logger.error(f"S3 delete failed: {e}")
            return False