from django.db import models
from projects.models import Project

# Create your models here.

class QRCardBatch(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='qrcard_batches')
    name = models.CharField(max_length=255, default="QR Card Batch")
    pdf = models.FileField(upload_to='qrcards/')
    amount = models.PositiveIntegerField()
    size = models.CharField(max_length=20, default='medium')
    per_page = models.PositiveIntegerField(default=12)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QRCard Batch {self.name} for {self.project.name} ({self.amount} codes)"

class QRCard(models.Model):
    # Basic QR card info
    batch = models.ForeignKey(QRCardBatch, on_delete=models.CASCADE, related_name='qrcards', null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='qrcards')
    code = models.CharField(max_length=64, unique=True)
    qr_url = models.URLField(help_text="The URL encoded in the QR code", blank=True, null=True)
    pdf = models.FileField(upload_to='qrcards/', null=True, blank=True)  # Individual PDFs are optional
    
    # Security - PIN code for accessing photos (4-6 digits)
    access_pin = models.CharField(max_length=6, help_text="PIN code for tourists to access their photos")
    
    # Client information (filled when tourist scans QR and provides info)
    client_email = models.EmailField(blank=True, null=True, help_text="Tourist's email for photo delivery")
    client_name = models.CharField(max_length=100, blank=True, null=True, help_text="Tourist's name")
    client_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Tourist's phone number")
    
    # Photo session info
    session_notes = models.TextField(blank=True, null=True, help_text="Photographer's notes about the session")
    location_name = models.CharField(max_length=200, blank=True, null=True, help_text="Specific location where photos were taken")
    
    # Status tracking
    STATUS_CHOICES = [
        ('distributed', 'Card Distributed'),
        ('scanned', 'QR Code Scanned'),
        ('info_provided', 'Client Info Provided'),
        ('photos_uploaded', 'Photos Uploaded'),
        ('completed', 'Completed - Photos Delivered'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='distributed')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    scanned_at = models.DateTimeField(null=True, blank=True, help_text="When the QR code was first scanned")
    info_provided_at = models.DateTimeField(null=True, blank=True, help_text="When client provided their info")
    photos_uploaded_at = models.DateTimeField(null=True, blank=True, help_text="When photos were uploaded")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When photos were delivered to client")

    def __str__(self):
        return f"QRCard {self.code} for {self.project.name} - {self.get_status_display()}"
    
    @property
    def short_code(self):
        """Returns first 8 characters of the code for display"""
        return self.code[:8]
    
    @property
    def has_client_info(self):
        """Returns True if client has provided their information"""
        return bool(self.client_email)
    
    @property
    def photo_count(self):
        """Returns the number of photos uploaded for this QR card"""
        return self.photos.count()


class QRCardPhoto(models.Model):
    """Photos taken for a specific QR card"""
    qr_card = models.ForeignKey(QRCard, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='qr_photos/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255, help_text="Original filename when uploaded")
    
    # Photo metadata
    taken_at = models.DateTimeField(null=True, blank=True, help_text="When the photo was taken (if available)")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    
    # Processing status
    is_processed = models.BooleanField(default=False, help_text="Whether photo has been processed/optimized")
    
    class Meta:
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"Photo for {self.qr_card.short_code} - {self.original_filename}"
    
    @property
    def file_size_mb(self):
        """Returns file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)


class PhotoUploadBatch(models.Model):
    """Batch upload of photos by photographer for QR code analysis"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='photo_batches')
    name = models.CharField(max_length=255, default="Photo Batch")
    
    # Processing status
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('analyzing', 'Analyzing QR Codes'),
        ('completed', 'Analysis Complete'),
        ('failed', 'Analysis Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    
    # Statistics
    total_photos = models.PositiveIntegerField(default=0)
    processed_photos = models.PositiveIntegerField(default=0)
    qr_codes_found = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Photo Batch {self.name} for {self.project.name} ({self.total_photos} photos)"
    
    @property
    def progress_percentage(self):
        """Returns processing progress as percentage"""
        if self.total_photos == 0:
            return 0
        return round((self.processed_photos / self.total_photos) * 100, 1)


class RawPhotoUpload(models.Model):
    """Individual photos uploaded in a batch before QR analysis"""
    batch = models.ForeignKey(PhotoUploadBatch, on_delete=models.CASCADE, related_name='raw_photos')
    image = models.ImageField(upload_to='raw_photos/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    s3_key = models.CharField(max_length=500, blank=True, null=True, help_text="S3 object key for direct uploads")
    
    # EXIF data
    taken_at = models.DateTimeField(null=True, blank=True, help_text="Extracted from EXIF data")
    camera_make = models.CharField(max_length=100, blank=True, null=True)
    camera_model = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    has_qr_code = models.BooleanField(default=False)
    qr_code_data = models.TextField(blank=True, null=True, help_text="Decoded QR code content")
    assigned_qr_card = models.ForeignKey(QRCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='raw_source_photos')
    
    # Error handling
    processing_error = models.TextField(blank=True, null=True)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['taken_at', 'uploaded_at']
    
    def __str__(self):
        return f"Raw Photo {self.original_filename} in {self.batch.name}"
    
    @property
    def file_size_mb(self):
        """Returns file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
