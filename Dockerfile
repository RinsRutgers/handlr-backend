FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies required by opencv-python-headless and pyzbar (Debian/Bookworm)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    zbar-tools \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "spotshot.wsgi:application", "--bind", "0.0.0.0:8000"]
