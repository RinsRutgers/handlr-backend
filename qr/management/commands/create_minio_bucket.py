from django.core.management.base import BaseCommand
from minio import Minio
from minio.error import S3Error
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create MinIO bucket for media storage'

    def handle(self, *args, **options):
        try:
            # Initialize MinIO client
            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False  # Set to True for HTTPS
            )

            bucket_name = settings.MINIO_BUCKET_NAME

            # Check if bucket exists
            if client.bucket_exists(bucket_name):
                self.stdout.write(
                    self.style.SUCCESS(f'Bucket "{bucket_name}" already exists.')
                )
            else:
                # Create bucket
                client.make_bucket(bucket_name)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created bucket "{bucket_name}".')
                )

                # Set bucket policy to public read for media files
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                        }
                    ]
                }

                import json
                client.set_bucket_policy(bucket_name, json.dumps(policy))
                self.stdout.write(
                    self.style.SUCCESS(f'Set public read policy for bucket "{bucket_name}".')
                )

        except S3Error as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating bucket: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
