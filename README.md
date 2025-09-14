# SpotShot Backend

A Django REST API backend for the SpotShot application - a QR code-based photo sharing platform that allows users to generate QR codes for photo collection events.

## 🚀 Features

- **QR Code Generation**: Create QR codes for photo collection events
- **Photo Management**: Upload, store, and manage photos through S3-compatible storage
- **User Authentication**: JWT-based authentication with refresh tokens
- **Project Management**: Organize photos into projects/events
- **Background Tasks**: Celery integration for handling photo processing
- **RESTful API**: Comprehensive API endpoints for frontend integration
- **Admin Interface**: Django admin panel for management
- **Production Ready**: Configured for Heroku deployment with PostgreSQL and Redis

## 🛠 Tech Stack

- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL
- **Cache/Message Broker**: Redis
- **File Storage**: MinIO (development) / AWS S3 (production)
- **Background Tasks**: Celery
- **Authentication**: JWT with Simple JWT
- **Image Processing**: Pillow, OpenCV
- **QR Code Generation**: qrcode, pyzbar
- **PDF Generation**: ReportLab
- **Deployment**: Docker, Heroku

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (for production)
- Redis (for production)
- AWS S3 bucket (for production file storage)

## 🏃‍♂️ Quick Start

### Development with Docker

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd spotshot-backend
   ```

2. **Create environment file**
   ```bash
   cp .env.example backend/.env
   ```

3. **Edit the environment file**
   ```bash
   # Update backend/.env with your local settings
   DEBUG=True
   SECRET_KEY=your-development-secret-key
   POSTGRES_DB=spotshot
   POSTGRES_USER=spotshot
   POSTGRES_PASSWORD=spotshot
   ```

4. **Start the development environment**
   ```bash
   docker-compose up -d
   ```

5. **Run migrations**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

7. **Access the application**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - MinIO Console: http://localhost:9001 (minio/minio123)

### Local Development (without Docker)

1. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up local services**
   ```bash
   # Install and start PostgreSQL
   # Install and start Redis
   # Install and start MinIO (optional)
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local database and Redis settings
   ```

4. **Run migrations and start server**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

## 🐳 Docker Services

The `docker-compose.yml` includes:

- **backend**: Django application server
- **db**: PostgreSQL database
- **redis**: Redis cache and message broker
- **minio**: S3-compatible object storage
- **celery**: Background task worker
- **nginx**: Reverse proxy (if frontend included)

## 📁 Project Structure

```
spotshot-backend/
├── backend/                    # Django application
│   ├── media/                 # Uploaded files (development)
│   │   ├── qr_photos/        # QR code photos
│   │   └── qrcards/          # Generated QR cards
│   └── staticfiles/          # Collected static files
├── projects/                  # Projects Django app
├── qr/                       # QR code Django app
├── spotshot/                 # Main Django project
│   ├── settings.py          # Development settings
│   ├── production_settings.py # Production settings
│   ├── health.py            # Health check endpoints
│   └── urls.py              # URL configuration
├── users/                    # User management Django app
├── docker-compose.yml        # Docker development setup
├── Dockerfile               # Docker image configuration
├── Procfile                 # Heroku process configuration
├── requirements.txt         # Python dependencies
├── runtime.txt             # Python version for Heroku
├── app.json                # Heroku app configuration
└── HEROKU_DEPLOYMENT.md    # Deployment guide
```

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token

### Projects
- `GET /api/projects/` - List user projects
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}/` - Get project details
- `PUT /api/projects/{id}/` - Update project
- `DELETE /api/projects/{id}/` - Delete project

### QR Codes
- `POST /api/qr/generate/` - Generate QR code
- `GET /api/qr/{id}/` - Get QR code details
- `POST /api/qr/{id}/photos/` - Upload photos to QR code
- `GET /api/qr/{id}/photos/` - List QR code photos

### Health Checks
- `GET /health/` - Application health status
- `GET /ready/` - Application readiness check

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `False` |
| `SECRET_KEY` | Django secret key | `your-secret-key` |
| `ALLOWED_HOSTS` | Allowed host names | `localhost,yourapp.herokuapp.com` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@localhost/db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_S3` | Use S3 for file storage | `False` |
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name | - |
| `FRONTEND_URL` | Frontend application URL | `http://localhost:3000` |
| `CORS_ALLOWED_ORIGINS` | CORS allowed origins | - |

## 🚀 Deployment

### Heroku Deployment

See [HEROKU_DEPLOYMENT.md](./HEROKU_DEPLOYMENT.md) for detailed deployment instructions.

**Quick Deploy:**
```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-app-name

# Add add-ons
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini

# Set environment variables
heroku config:set DJANGO_SETTINGS_MODULE=spotshot.production_settings
heroku config:set DEBUG=False
heroku config:set SECRET_KEY="your-production-secret-key"

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate
```

### Docker Production

Build and run with production settings:

```bash
# Build production image
docker build -t spotshot-backend .

# Run with production environment
docker run -d \
  -e DJANGO_SETTINGS_MODULE=spotshot.production_settings \
  -e DEBUG=False \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=your-db-url \
  -p 8000:8000 \
  spotshot-backend
```

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run tests with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Monitoring

### Health Checks

The application includes built-in health check endpoints:

- `GET /health/` - Basic health check with database connectivity
- `GET /ready/` - Readiness check for container orchestration

### Logging

Logs are configured to output to stdout in production for Heroku compatibility.

```bash
# View Heroku logs
heroku logs --tail

# View specific app logs
heroku logs --source app --tail
```

## 🔧 Development

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Celery Tasks

Start Celery worker for background tasks:

```bash
# Development
celery -A spotshot worker -l info

# With beat scheduler
celery -A spotshot beat -l info
```

### Static Files

```bash
# Collect static files
python manage.py collectstatic

# Clear static files
python manage.py collectstatic --clear
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Write tests for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check database logs
docker-compose logs db
```

**Redis Connection Error**
```bash
# Check if Redis is running
docker-compose ps

# Check Redis logs
docker-compose logs redis
```

**File Upload Issues**
- Check MinIO/S3 configuration
- Verify bucket permissions
- Check CORS settings for S3

**Celery Tasks Not Processing**
```bash
# Check Celery worker status
docker-compose logs celery

# Restart Celery worker
docker-compose restart celery
```

### Getting Help

- Check the [Issues](../../issues) page for known problems
- Review [Django Documentation](https://docs.djangoproject.com/)
- Check [Heroku Documentation](https://devcenter.heroku.com/)

## 📧 Contact

For questions or support, please open an issue or contact the development team.

---

**Built with ❤️ using Django and modern web technologies**
