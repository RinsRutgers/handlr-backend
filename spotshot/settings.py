"""
Django settings for spotshot project.

This file provides environment-aware configuration:
- In production (when DEBUG=False), it uses production-optimized settings
- In development, it imports from config/local.py for backwards compatibility

For modular configuration, see the config/ directory:
- config/base.py: Base settings shared across environments
- config/local.py: Local development settings
- config/production.py: Production settings
"""

import os

# Determine if we're in production based on environment variables
is_production = os.environ.get('DEBUG', '').lower() in ('false', '0', 'no', 'off') or \
                'HEROKU' in os.environ or \
                'DYNO' in os.environ

if is_production:
    # Production settings - inline to avoid import issues
    from pathlib import Path
    from datetime import timedelta
    
    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Simple config function using os.environ
    def get_env(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            if cast == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            return cast(value)
        return value
    
    # Security settings
    SECRET_KEY = get_env('SECRET_KEY', default='django-insecure-change-me-in-production')
    DEBUG = get_env('DEBUG', default=False, cast=bool)
    ALLOWED_HOSTS = get_env('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')
    
    # Application definition
    DJANGO_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
    ]
    
    THIRD_PARTY_APPS = [
        'rest_framework',
        'rest_framework_simplejwt',
        'rest_framework_simplejwt.token_blacklist',
        'corsheaders',
    ]
    
    LOCAL_APPS = [
        'users',
        'projects',
        'qr',
    ]
    
    INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
    
    MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',  # For Heroku static files
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
    
    ROOT_URLCONF = 'spotshot.urls'
    
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]
    
    WSGI_APPLICATION = 'spotshot.wsgi.application'
    
    # Database - Simple DATABASE_URL parsing for Heroku
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
    
    # Password validation
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]
    
    # Custom User Model
    AUTH_USER_MODEL = 'users.User'
    
    # Internationalization
    LANGUAGE_CODE = 'en-us'
    TIME_ZONE = 'UTC'
    USE_I18N = True
    USE_TZ = True
    
    # Static files (CSS, JavaScript, Images)
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # Default primary key field type
    DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
    
    # CORS settings for production
    CORS_ALLOW_ALL_ORIGINS = DEBUG
    CORS_ALLOWED_ORIGINS = get_env('CORS_ALLOWED_ORIGINS', default='').split(',') if not DEBUG else []
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_HEADERS = [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
        'cookie',
    ]
    CORS_ALLOW_METHODS = [
        'DELETE',
        'GET',
        'OPTIONS',
        'PATCH',
        'POST',
        'PUT',
    ]
    
    # REST Framework settings
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'users.authentication.CookieJWTAuthentication',
        ),
    }
    
    # JWT settings
    SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
        'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
        'AUTH_HEADER_TYPES': ('Bearer',),
        'ROTATE_REFRESH_TOKENS': True,
        'BLACKLIST_AFTER_ROTATION': True,
    }
    
    # Celery settings
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL
    
    # S3 Storage settings (Bucketeer support)
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
            AWS_S3_ENDPOINT_URL = None
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
    
    # SpotShoot Configuration
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
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

else:
    # Development settings - import from config/local.py for backwards compatibility
    try:
        from .config.local import *
    except ImportError:
        # Fallback to basic development settings if config module fails
        from pathlib import Path
        from datetime import timedelta
        
        BASE_DIR = Path(__file__).resolve().parent.parent
        
        SECRET_KEY = 'django-insecure-$ah4z_&eehxl*-m0bhu5*dmu0cj$!q%*2w@7ive*$0j%wu$ja0'
        DEBUG = True
        ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']
        
        # Basic app configuration
        INSTALLED_APPS = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'rest_framework',
            'rest_framework_simplejwt',
            'rest_framework_simplejwt.token_blacklist',
            'corsheaders',
            'users',
            'projects',
            'qr',
        ]
        
        MIDDLEWARE = [
            'corsheaders.middleware.CorsMiddleware',
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]
        
        ROOT_URLCONF = 'spotshot.urls'
        
        TEMPLATES = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ]
        
        WSGI_APPLICATION = 'spotshot.wsgi.application'
        
        # Basic database configuration for development
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('POSTGRES_DB', 'spotshot'),
                'USER': os.environ.get('POSTGRES_USER', 'spotshot'),
                'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'spotshot'),
                'HOST': os.environ.get('POSTGRES_HOST', 'db'),
                'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            }
        }
        
        AUTH_PASSWORD_VALIDATORS = []
        AUTH_USER_MODEL = 'users.User'
        LANGUAGE_CODE = 'en-us'
        TIME_ZONE = 'UTC'
        USE_I18N = True
        USE_TZ = True
        
        STATIC_URL = '/static/'
        STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
        DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
        
        CORS_ALLOW_ALL_ORIGINS = True
        CORS_ALLOW_CREDENTIALS = True
        CORS_ALLOW_HEADERS = [
            'accept', 'accept-encoding', 'authorization', 'content-type',
            'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with', 'cookie',
        ]
        CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
        
        REST_FRAMEWORK = {
            'DEFAULT_AUTHENTICATION_CLASSES': (
                'users.authentication.CookieJWTAuthentication',
            ),
        }
        
        SIMPLE_JWT = {
            'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
            'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
            'AUTH_HEADER_TYPES': ('Bearer',),
            'ROTATE_REFRESH_TOKENS': True,
            'BLACKLIST_AFTER_ROTATION': True,
        }
        
        CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
        CELERY_RESULT_BACKEND = CELERY_BROKER_URL
        FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
