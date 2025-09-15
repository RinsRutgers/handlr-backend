# SpotShot Configuration

This project uses a modular settings configuration structure located in `spotshot/config/`.

## Configuration Files

### `config/base.py`
Contains common settings shared across all environments:
- Django core configuration
- Installed apps
- Middleware
- Templates
- Authentication settings
- REST Framework configuration
- JWT settings
- Basic CORS settings

### `config/local.py`
Development settings that inherit from base:
- `DEBUG = True`
- Local PostgreSQL database configuration
- MinIO for file storage
- Permissive CORS settings
- Local environment-specific configurations

### `config/production.py`
Production settings that inherit from base:
- `DEBUG = False` by default
- Heroku PostgreSQL via `DATABASE_URL`
- AWS S3 support for file storage
- Security settings for HTTPS
- WhiteNoise for static files
- Restricted CORS settings
- Production logging configuration

## Usage

### For Development
Set your environment variable to:
```bash
export DJANGO_SETTINGS_MODULE=spotshot.config.local
```

Or in your `.env` file:
```
DJANGO_SETTINGS_MODULE=spotshot.config.local
```

### For Production
Set your environment variable to:
```bash
export DJANGO_SETTINGS_MODULE=spotshot.config.production
```

Or in your production environment (like Heroku):
```
DJANGO_SETTINGS_MODULE=spotshot.config.production
```

## Default Behavior

- `manage.py` defaults to `spotshot.config.local` for development convenience
- `wsgi.py` and `asgi.py` default to `spotshot.config.production` for deployment
- `celery.py` defaults to `spotshot.config.local` but can be overridden
- `settings.py` is kept for backwards compatibility and imports local settings

## Environment Variables

### Required for Production
```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://username:password@hostname:port/database_name
ALLOWED_HOSTS=your-domain.com,another-domain.com
```

### Optional for S3 (Production)
```bash
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=your-bucket-name.s3.amazonaws.com
```

### CORS Configuration (Production)
```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://anotherdomain.com
```

## Migration from Old Settings

The old `settings.py` and `production_settings.py` files have been replaced with this modular structure. The new `settings.py` file imports from `config/local.py` for backwards compatibility.

If you have any custom settings, you should add them to the appropriate config file:
- Common settings → `config/base.py`
- Development-only settings → `config/local.py`  
- Production-only settings → `config/production.py`