# SpotShot Backend - Heroku Deployment Guide

This guide will help you deploy your Django SpotShot backend to Heroku using the new configuration structure.

## Prerequisites

1. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
2. Git repository initialized
3. Heroku account created

## New Configuration Structure

This project now uses a modular settings configuration:
- `spotshot/config/base.py` - Common settings for all environments
- `spotshot/config/local.py` - Development settings
- `spotshot/config/production.py` - Production settings
- `spotshot/config/README.md` - Configuration documentation

## Files Created for Heroku Deployment

- `.gitignore` - Excludes sensitive files and development artifacts
- `.env.example` - Template for environment variables
- `Procfile` - Tells Heroku how to run your app
- `runtime.txt` - Specifies Python version
- `spotshot/production_settings.py` - Production-ready Django settings
- `app.json` - Heroku app configuration for one-click deploy
- Updated `requirements.txt` - Added production dependencies

## Quick Start Commands (Free Tier)

Here's the complete sequence of commands to deploy SpotShot with free services:

```bash
# 1. Create Heroku app
heroku create handlr-staging-backend --buildpack heroku/python

# 2. Add free add-ons
heroku addons:create heroku-postgresql:essential-0 --app handlr-staging-backend
heroku addons:create heroku-redis:mini --app handlr-staging-backend
heroku addons:create mailgun:starter --app handlr-staging-backend
heroku addons:create bucketeer:hobbyist --app handlr-staging-backend

# 3. Set environment variables
heroku config:set DJANGO_SETTINGS_MODULE=spotshot.settings --app handlr-staging-backend
heroku config:set SECRET_KEY="$(openssl rand -base64 64)" --app handlr-staging-backend
heroku config:set DEBUG=False --app handlr-staging-backend
heroku config:set ALLOWED_HOSTS=handlr-staging-backend.herokuapp.com --app handlr-staging-backend
heroku config:set USE_S3=True --app handlr-staging-backend
heroku config:set FRONTEND_URL=handlr-frontend-jw3j5ddp1-rinsrutgers-projects.vercel.app --app handlr-staging-backend
heroku config:set CORS_ALLOWED_ORIGINS=handlr-frontend-jw3j5ddp1-rinsrutgers-projects.vercel.app --app handlr-staging-backend

# 4. Deploy
git push heroku main

# 5. Run migrations and create superuser
heroku run python manage.py migrate --app handlr-staging-backend
heroku run python manage.py createsuperuser --app handlr-staging-backend

# 6. Open your app
heroku open --app handlr-staging-backend
```

## Step-by-Step Deployment

### 1. Prepare Your Repository

```bash
# Make sure all files are committed
git add .
git commit -m "Prepare for Heroku deployment"
```

### 2. Create Heroku App

```bash
# Create a new Heroku app with Python buildpack
heroku create handlr-staging-backend --buildpack heroku/python

# Or if you want Heroku to generate a name
heroku create --buildpack heroku/python
```

### 3. Add Required Add-ons

```bash
# Add PostgreSQL database (Free tier)
heroku addons:create heroku-postgresql:hobby-dev --app handlr-staging-backend

# Promote the database (usually automatic)
heroku pg:promote DATABASE_URL --app handlr-staging-backend

# Add Redis for Celery (Free tier)
heroku addons:create heroku-redis:mini --app handlr-staging-backend

# Add email service (Free tier)
heroku addons:create mailgun:starter --app handlr-staging-backend

# Add S3-compatible storage (Free tier)
heroku addons:create bucketeer:hobbyist --app handlr-staging-backend
```

### 4. Set Environment Variables

```bash
# Set Django settings module (using backwards-compatible settings.py)
heroku config:set DJANGO_SETTINGS_MODULE=spotshot.settings --app handlr-staging-backend

# Generate and set secret key
heroku config:set SECRET_KEY="$(openssl rand -base64 64)" --app handlr-staging-backend

# Set debug to false
heroku config:set DEBUG=False --app handlr-staging-backend

# Set your app's URL in allowed hosts (replace with your actual app name)
heroku config:set ALLOWED_HOSTS=handlr-staging-backend.herokuapp.com,your-custom-domain.com --app handlr-staging-backend

# Set frontend URL (replace with your frontend URL)
heroku config:set FRONTEND_URL=handlr-frontend-jw3j5ddp1-rinsrutgers-projects.vercel.app --app handlr-staging-backend

# Set CORS allowed origins
heroku config:set CORS_ALLOWED_ORIGINS=handlr-frontend-jw3j5ddp1-rinsrutgers-projects.vercel.app --app handlr-staging-backend
```

### 5. Configure Bucketeer S3 Storage (Free)

Bucketeer provides free S3-compatible storage on Heroku:

```bash
# Enable S3 usage
heroku config:set USE_S3=True --app handlr-staging-backend

# Bucketeer automatically sets these environment variables:
# BUCKETEER_AWS_ACCESS_KEY_ID
# BUCKETEER_AWS_SECRET_ACCESS_KEY  
# BUCKETEER_BUCKET_NAME
# BUCKETEER_AWS_REGION

# You can also set them manually if needed:
# heroku config:set AWS_ACCESS_KEY_ID=$(heroku config:get BUCKETEER_AWS_ACCESS_KEY_ID --app handlr-staging-backend) --app handlr-staging-backend
# heroku config:set AWS_SECRET_ACCESS_KEY=$(heroku config:get BUCKETEER_AWS_SECRET_ACCESS_KEY --app handlr-staging-backend) --app handlr-staging-backend
# heroku config:set AWS_STORAGE_BUCKET_NAME=$(heroku config:get BUCKETEER_BUCKET_NAME --app handlr-staging-backend) --app handlr-staging-backend
# heroku config:set AWS_S3_REGION_NAME=$(heroku config:get BUCKETEER_AWS_REGION --app handlr-staging-backend) --app handlr-staging-backend
```

### 6. Deploy to Heroku

```bash
# Deploy your app
git push heroku main

# Or if your main branch is named differently
git push heroku master
```

### 7. Run Database Migrations

```bash
# Run migrations
heroku run python manage.py migrate --app handlr-staging-backend

# Create a superuser (optional)
heroku run python manage.py createsuperuser --app handlr-staging-backend
```

### 8. Scale Your App

```bash
# Scale web dyno
heroku ps:scale web=1 --app handlr-staging-backend

# Scale worker dyno for Celery
heroku ps:scale worker=1 --app handlr-staging-backend

# Scale beat dyno for Celery Beat (if needed)
heroku ps:scale beat=1 --app handlr-staging-backend
```

## System Packages (pyzbar/OpenCV)

`pyzbar` requires the `zbar` shared library at runtime. On Heroku, add the apt buildpack and an `Aptfile` to install system packages:

```bash
# Add the apt buildpack (must come before python)
heroku buildpacks:add --index 1 heroku-community/apt --app handlr-staging-backend

# Verify buildpack order
heroku buildpacks --app handlr-staging-backend
```

This repository includes an `Aptfile` that installs:

- libzbar0 (required for pyzbar)
- libgl1 (OpenCV runtime)
- libglib2.0-0 (OpenCV runtime)

After adding the buildpack, trigger a rebuild:

```bash
git commit --allow-empty -m "Trigger rebuild for apt packages"
git push heroku main
```

## Release Phase

We use a `release` phase (see `Procfile`) to collect static files and run migrations before starting dynos. If migrations fail, the deploy will be rejected.

```bash
heroku logs --tail --dyno=release --app handlr-staging-backend
```

## Environment Variables Reference

Here are all the environment variables you should set:

### Required
- `DJANGO_SETTINGS_MODULE=spotshot.config.production`
- `SECRET_KEY` - Django secret key (use `openssl rand -base64 64` to generate)
- `ALLOWED_HOSTS` - Your app domain(s)
- `DEBUG=False`

### Database (Automatically set by Heroku PostgreSQL addon)
- `DATABASE_URL` - PostgreSQL connection string

### Redis (Automatically set by Heroku Redis addon)
- `REDIS_URL` - Redis connection string

### Bucketeer S3 Storage (Automatically set by Bucketeer addon)
- `USE_S3=True`
- `BUCKETEER_AWS_ACCESS_KEY_ID` - Access key (auto-set)
- `BUCKETEER_AWS_SECRET_ACCESS_KEY` - Secret key (auto-set)
- `BUCKETEER_BUCKET_NAME` - Bucket name (auto-set)
- `BUCKETEER_AWS_REGION` - AWS region (auto-set)

### Mailgun (Automatically set by Mailgun addon)
- `MAILGUN_API_KEY` - Mailgun API key (auto-set)
- `MAILGUN_DOMAIN` - Mailgun domain (auto-set)

### Optional
- `FRONTEND_URL` - Your frontend application URL
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins (comma-separated)
- `DJANGO_LOG_LEVEL` - Logging level (default: INFO)

## Setting Up Bucketeer S3 Storage

Bucketeer provides free S3-compatible storage that works seamlessly with django-storages:

1. Add the Bucketeer addon: `heroku addons:create bucketeer:hobbyist`
2. Bucketeer automatically creates and configures your S3 bucket
3. Environment variables are automatically set in your Heroku app
4. No additional AWS account or setup required!

### Bucketeer Benefits:
- **Free tier**: 1GB storage, 10GB bandwidth per month
- **No AWS account needed**: Bucketeer handles everything
- **Auto-configuration**: Works out of the box with django-storages
- **S3-compatible**: Uses standard S3 API

## Monitoring and Troubleshooting

```bash
# View logs
heroku logs --tail --app handlr-staging-backend

# Check dyno status
heroku ps --app handlr-staging-backend

# Run one-off commands
heroku run python manage.py shell --app handlr-staging-backend

# Check config vars
heroku config --app handlr-staging-backend
```

## Scaling for Production

When you're ready for production traffic:

```bash
# Upgrade to paid dynos for better performance
heroku ps:scale web=2:standard-1x --app handlr-staging-backend
heroku ps:scale worker=1:standard-1x --app handlr-staging-backend

# Upgrade add-ons
heroku addons:upgrade heroku-postgresql:standard-0 --app handlr-staging-backend
heroku addons:upgrade heroku-redis:premium-0 --app handlr-staging-backend
```

## Continuous Deployment

To set up automatic deployment from GitHub:

1. Connect your Heroku app to your GitHub repository
2. Enable automatic deploys from your main branch
3. Optionally enable "Wait for CI to pass before deploy"

## Important Notes

1. **Never commit sensitive data** - Use environment variables for all secrets
2. **Free tier limitations** - Monitor your usage:
   - PostgreSQL: 10,000 rows limit
   - Redis: 25MB memory limit
   - Bucketeer: 1GB storage, 10GB bandwidth per month
   - Mailgun: 300 emails per month
3. **Monitor your logs** - Use `heroku logs --tail` to watch for issues
4. **Heroku dyno sleeping** - Free dynos sleep after 30 minutes of inactivity
5. **Database backups** - Not included with hobby-dev plan (upgrade for backups)

## Testing Your Deployment

1. Visit your app URL: `https://handlr-staging-backend.herokuapp.com`
2. Test API endpoints
3. Check that file uploads work (if using S3)
4. Verify that Celery tasks are processing

## Need Help?

- Check Heroku documentation: https://devcenter.heroku.com/
- View your app logs: `heroku logs --tail --app handlr-staging-backend`
- Check dyno status: `heroku ps --app handlr-staging-backend`
