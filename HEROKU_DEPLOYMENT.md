# SpotShot Backend - Heroku Deployment Guide

This guide will help you deploy your Django SpotShot backend to Heroku.

## Prerequisites

1. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
2. Git repository initialized
3. Heroku account created

## Files Created for Heroku Deployment

- `.gitignore` - Excludes sensitive files and development artifacts
- `.env.example` - Template for environment variables
- `Procfile` - Tells Heroku how to run your app
- `runtime.txt` - Specifies Python version
- `spotshot/production_settings.py` - Production-ready Django settings
- `app.json` - Heroku app configuration for one-click deploy
- Updated `requirements.txt` - Added production dependencies

## Step-by-Step Deployment

### 1. Prepare Your Repository

```bash
# Make sure all files are committed
git add .
git commit -m "Prepare for Heroku deployment"
```

### 2. Create Heroku App

```bash
# Create a new Heroku app
heroku create your-app-name

# Or if you want Heroku to generate a name
heroku create
```

### 3. Add Required Add-ons

```bash
# Add PostgreSQL database
heroku addons:create heroku-postgresql:mini

# Add Redis for Celery
heroku addons:create heroku-redis:mini
```

### 4. Set Environment Variables

```bash
# Set Django settings module
heroku config:set DJANGO_SETTINGS_MODULE=spotshot.production_settings

# Set debug to false
heroku config:set DEBUG=False

# Set your app's URL in allowed hosts (replace with your actual app name)
heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com,localhost,127.0.0.1

# Set secret key (generate a new one for production)
heroku config:set SECRET_KEY="your-super-secret-key-here"

# Set frontend URL (replace with your frontend URL)
heroku config:set FRONTEND_URL=https://your-frontend-app.herokuapp.com

# Set CORS allowed origins
heroku config:set CORS_ALLOWED_ORIGINS=https://your-frontend-app.herokuapp.com
```

### 5. Configure AWS S3 (Recommended for Production)

Since MinIO isn't available on Heroku, you should use AWS S3 for file storage:

```bash
# Enable S3 usage
heroku config:set USE_S3=True

# Set AWS credentials (get these from AWS Console)
heroku config:set AWS_ACCESS_KEY_ID=your-aws-access-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-aws-secret-key
heroku config:set AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
heroku config:set AWS_S3_REGION_NAME=us-east-1
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
heroku run python manage.py migrate

# Create a superuser (optional)
heroku run python manage.py createsuperuser
```

### 8. Scale Your App

```bash
# Scale web dyno
heroku ps:scale web=1

# Scale worker dyno for Celery
heroku ps:scale worker=1

# Scale beat dyno for Celery Beat (if needed)
heroku ps:scale beat=1
```

## System Packages (pyzbar/OpenCV)

`pyzbar` requires the `zbar` shared library at runtime. On Heroku, add the apt buildpack and an `Aptfile` to install system packages:

```bash
# Add the apt buildpack (must come before python)
heroku buildpacks:add --index 1 heroku-community/apt

# Verify buildpack order
heroku buildpacks
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
heroku logs --tail --dyno=release
```

## Environment Variables Reference

Here are all the environment variables you should set:

### Required
- `DJANGO_SETTINGS_MODULE=spotshot.production_settings`
- `SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - Your app domain
- `DEBUG=False`

### Database (Automatically set by Heroku PostgreSQL addon)
- `DATABASE_URL` - PostgreSQL connection string

### Redis (Automatically set by Heroku Redis addon)
- `REDIS_URL` - Redis connection string

### AWS S3 (Required if USE_S3=True)
- `USE_S3=True`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_REGION_NAME`

### Optional
- `FRONTEND_URL` - Your frontend application URL
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins
- `DJANGO_LOG_LEVEL` - Logging level (default: INFO)

## Setting Up AWS S3

1. Create an S3 bucket in AWS Console
2. Create an IAM user with S3 permissions
3. Generate access keys for the IAM user
4. Set the bucket policy to allow public read access for media files

Example S3 bucket policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

## Monitoring and Troubleshooting

```bash
# View logs
heroku logs --tail

# Check dyno status
heroku ps

# Run one-off commands
heroku run python manage.py shell

# Check config vars
heroku config
```

## Scaling for Production

When you're ready for production traffic:

```bash
# Upgrade to paid dynos for better performance
heroku ps:scale web=2:standard-1x
heroku ps:scale worker=1:standard-1x

# Upgrade add-ons
heroku addons:upgrade heroku-postgresql:standard-0
heroku addons:upgrade heroku-redis:premium-0
```

## Continuous Deployment

To set up automatic deployment from GitHub:

1. Connect your Heroku app to your GitHub repository
2. Enable automatic deploys from your main branch
3. Optionally enable "Wait for CI to pass before deploy"

## Important Notes

1. **Never commit sensitive data** - Use environment variables for all secrets
2. **Use S3 for file storage** - Heroku's ephemeral filesystem will delete uploaded files
3. **Monitor your logs** - Use `heroku logs --tail` to watch for issues
4. **Set up error tracking** - Consider adding Sentry for error monitoring
5. **Database backups** - Heroku PostgreSQL automatically backs up your database

## Testing Your Deployment

1. Visit your app URL: `https://your-app-name.herokuapp.com`
2. Test API endpoints
3. Check that file uploads work (if using S3)
4. Verify that Celery tasks are processing

## Need Help?

- Check Heroku documentation: https://devcenter.heroku.com/
- View your app logs: `heroku logs --tail`
- Check dyno status: `heroku ps`
