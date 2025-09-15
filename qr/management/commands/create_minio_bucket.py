from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create MinIO bucket for media storage'

    def handle(self, *args, **options):
        # Lazy import and config guard
        try:
            from django.conf import settings
            if getattr(settings, 'USE_S3', False):
                self.stdout.write(self.style.WARNING('USE_S3=True; skipping MinIO bucket creation.'))
                return

            try:
                from minio import Minio
                from minio.error import S3Error
            except Exception as imp_err:
                self.stdout.write(self.style.WARNING(f'Minio not available ({imp_err}). Skipping.'))
                return

            required = ['MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'MINIO_BUCKET_NAME']
            if not all(hasattr(settings, k) for k in required):
                self.stdout.write(self.style.WARNING('MinIO settings missing. Skipping.'))
                return

            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=getattr(settings, 'MINIO_SECURE', False)
            )

            bucket_name = settings.MINIO_BUCKET_NAME

            if client.bucket_exists(bucket_name):
                self.stdout.write(self.style.SUCCESS(f'Bucket "{bucket_name}" already exists.'))
            else:
                client.make_bucket(bucket_name)
                self.stdout.write(self.style.SUCCESS(f'Successfully created bucket "{bucket_name}".'))

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
                self.stdout.write(self.style.SUCCESS(f'Set public read policy for bucket "{bucket_name}".'))

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'MinIO setup skipped due to error: {e}'))
