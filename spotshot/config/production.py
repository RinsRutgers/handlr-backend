"""
Production settings for spotshot project.
This file should be used for production deployment.
"""

import os
from .base import *

# Simple config function using os.environ
def get_env(key, default=None, cast=None):
    value = os.environ.get(key, default)
    if cast and value is not None:
        if cast == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        return cast(value)
    return value

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env('SECRET_KEY', default='django-insecure-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_env('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = get_env('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Add WhiteNoise middleware for serving static files on Heroku
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Database - Simple DATABASE_URL parsing
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    import urllib.parse as urlparse
    url = urlparse.urlparse(database_url)
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': get_env('POSTGRES_DB', 'spotshot'),
            'USER': get_env('POSTGRES_USER', 'spotshot'),
            'PASSWORD': get_env('POSTGRES_PASSWORD', 'spotshot'),
            'HOST': get_env('POSTGRES_HOST', 'localhost'),
            'PORT': get_env('POSTGRES_PORT', '5432'),
        }
    }

# Configure WhiteNoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only allow all origins in debug mode
CORS_ALLOWED_ORIGINS = get_env('CORS_ALLOWED_ORIGINS', default='').split(',') if not DEBUG else []

# AWS/S3 settings for production (supports both AWS S3 and Bucketeer)
USE_S3 = get_env('USE_S3', default=False, cast=bool)

if USE_S3:
    # Try Bucketeer environment variables first, then fall back to AWS
    AWS_ACCESS_KEY_ID = get_env('BUCKETEER_AWS_ACCESS_KEY_ID', default=get_env('AWS_ACCESS_KEY_ID', default=''))
    AWS_SECRET_ACCESS_KEY = get_env('BUCKETEER_AWS_SECRET_ACCESS_KEY', default=get_env('AWS_SECRET_ACCESS_KEY', default=''))
    AWS_STORAGE_BUCKET_NAME = get_env('BUCKETEER_BUCKET_NAME', default=get_env('AWS_STORAGE_BUCKET_NAME', default=''))
    AWS_S3_REGION_NAME = get_env('BUCKETEER_AWS_REGION', default=get_env('AWS_S3_REGION_NAME', default='us-east-1'))
    
    # For Bucketeer, use the bucket endpoint; for AWS, allow custom domain
    if get_env('BUCKETEER_BUCKET_NAME', default=None):
        # Using Bucketeer
        AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
        AWS_S3_ENDPOINT_URL = None  # Use default S3 endpoint
    else:
        # Using regular AWS S3
        AWS_S3_CUSTOM_DOMAIN = get_env('AWS_S3_CUSTOM_DOMAIN', default=f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com')
        AWS_S3_ENDPOINT_URL = get_env('AWS_S3_ENDPOINT_URL', default=None)
    
    AWS_DEFAULT_ACL = get_env('AWS_DEFAULT_ACL', default='public-read')
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False
    
    # Configure S3 storage
    storage_options = {
        'bucket_name': AWS_STORAGE_BUCKET_NAME,
        'region_name': AWS_S3_REGION_NAME,
        'custom_domain': AWS_S3_CUSTOM_DOMAIN,
        'default_acl': AWS_DEFAULT_ACL,
        'object_parameters': AWS_S3_OBJECT_PARAMETERS,
        'file_overwrite': AWS_S3_FILE_OVERWRITE,
        'querystring_auth': AWS_QUERYSTRING_AUTH,
    }
    
    # Add endpoint URL if specified (for custom S3-compatible services)
    if AWS_S3_ENDPOINT_URL:
        storage_options['endpoint_url'] = AWS_S3_ENDPOINT_URL
    
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': storage_options
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        }
    }
    
    # Media files URL
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    # Local file storage (fallback)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': get_env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'spotshot': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}