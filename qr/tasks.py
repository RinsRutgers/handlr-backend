from celery import shared_task
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from .models import QRCard, QRCardBatch, PhotoUploadBatch, RawPhotoUpload, QRCardPhoto
from projects.models import Project
import uuid
from PIL import Image, ExifTags
from reportlab.lib import colors
import logging
import random
import cv2
import numpy as np
from pyzbar import pyzbar
import os
from datetime import datetime

QR_SIZES = {
    'small': 50,   # mm
    'medium': 70,  # mm
    'large': 90,   # mm
}

@shared_task
def generate_qr_pdf_task(project_id, amount=100, size='medium', per_page=12, batch_name="QR Card Batch"):
    try:
        project = Project.objects.get(id=project_id)
        qr_size_mm = QR_SIZES.get(size, 70)
        qr_size = qr_size_mm * mm
        page_width, page_height = A4
        margin = 15 * mm
        
        # Calculate grid layout
        cols = int((page_width - 2 * margin) // (qr_size + 5 * mm))
        rows = int((page_height - 2 * margin) // (qr_size + 5 * mm))
        actual_per_page = min(per_page, cols * rows)
        total_pages = (amount + actual_per_page - 1) // actual_per_page
        
        # Generate unique codes and PINs
        codes = [str(uuid.uuid4()) for _ in range(amount)]
        pins = [str(random.randint(1000, 9999)) for _ in range(amount)]  # 4-digit PINs
        
        # Create PDF
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Add title to first page
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, page_height - margin + 5 * mm, f"{project.name} - QR Cards")
        c.setFont("Helvetica", 10)
        c.drawString(margin, page_height - margin + 2 * mm, f"Generated: {amount} codes | Size: {size} | Per page: {actual_per_page}")
        
        code_idx = 0
        for page in range(total_pages):
            if page > 0:
                c.showPage()
                
            # Add page header
            c.setFont("Helvetica", 8)
            c.drawString(margin, page_height - 5 * mm, f"Page {page + 1} of {total_pages}")
            
            for i in range(actual_per_page):
                if code_idx >= amount:
                    break
                    
                col = i % cols
                row = i // cols
                x = margin + col * (qr_size + 5 * mm)
                y = page_height - margin - 20 * mm - (row + 1) * (qr_size + 5 * mm)
                
                # Generate QR code with URL
                # Create URL that includes both code and PIN
                qr_url = f"{settings.FRONTEND_URL}/client/{codes[code_idx]}?pin={pins[code_idx]}"
                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=1,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Draw QR code - pass PIL Image directly to reportlab
                c.drawInlineImage(qr_img, x, y, qr_size, qr_size)
                
                # Draw border and cut lines
                c.setStrokeColor(colors.lightgrey)
                c.setLineWidth(0.5)
                c.rect(x, y, qr_size, qr_size, stroke=1, fill=0)
                
                # Add code text below QR
                c.setFont("Helvetica", 6)
                text_y = y - 3 * mm
                c.drawCentredString(x + qr_size/2, text_y, codes[code_idx][:8] + "...")
                
                # Add PIN below code
                pin_y = text_y - 4 * mm
                c.setFont("Helvetica-Bold", 8)
                c.drawCentredString(x + qr_size/2, pin_y, f"PIN: {pins[code_idx]}")
                
                code_idx += 1
        
        c.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create batch record
        batch = QRCardBatch.objects.create(
            project=project,
            name=batch_name,
            amount=amount,
            size=size,
            per_page=actual_per_page
        )
        
        # Save PDF
        pdf_name = f"qr_batch_{batch.id}_{uuid.uuid4().hex[:8]}.pdf"
        batch.pdf.save(pdf_name, ContentFile(pdf_content))
        batch.save()
        
        # Create individual QRCard records for tracking
        qr_cards = []
        for i in range(amount):
            qr_url = f"{settings.FRONTEND_URL}/client/{codes[i]}?pin={pins[i]}"
            qr_cards.append(
                QRCard(
                    batch=batch, 
                    project=project, 
                    code=codes[i], 
                    access_pin=pins[i],
                    qr_url=qr_url
                )
            )
        QRCard.objects.bulk_create(qr_cards)
        
        return {
            'success': True,
            'batch_id': batch.id,
            'pdf_name': pdf_name,
            'codes_generated': amount
        }
        
    except Exception as e:
        # Log the error and return failure
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to generate QR PDF for project {project_id}: {str(e)}")
        
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def analyze_photo_batch_for_qr_codes(batch_id):
    """
    Analyze uploaded photos for QR codes and group them by detected codes
    """
    try:
        batch = PhotoUploadBatch.objects.get(id=batch_id)
        batch.status = 'analyzing'
        batch.processing_started_at = timezone.now()
        batch.save()
        
        logger = logging.getLogger(__name__)
        logger.info(f"Starting QR analysis for batch {batch_id}")
        
        # Get all raw photos ordered by timestamp
        raw_photos = batch.raw_photos.order_by('taken_at', 'uploaded_at')
        total_photos = raw_photos.count()
        batch.total_photos = total_photos
        batch.save()
        
        current_qr_card = None
        processed_count = 0
        qr_codes_found = 0
        
        for raw_photo in raw_photos:
            try:
                # Extract QR code from image
                qr_data = extract_qr_code_from_image(raw_photo.image)
                
                if qr_data:
                    # Found QR code - this starts a new photo session
                    qr_codes_found += 1
                    raw_photo.has_qr_code = True
                    raw_photo.qr_code_data = qr_data
                    
                    # Try to find matching QR card
                    current_qr_card = find_qr_card_by_url(qr_data, batch.project)
                    
                    if current_qr_card:
                        raw_photo.assigned_qr_card = current_qr_card
                        logger.info(f"Found QR code for card {current_qr_card.short_code}")
                    else:
                        logger.warning(f"QR code found but no matching card: {qr_data}")
                
                else:
                    # No QR code - assign to current session if available
                    raw_photo.has_qr_code = False
                    if current_qr_card:
                        raw_photo.assigned_qr_card = current_qr_card
                
                # Mark as processed
                raw_photo.is_processed = True
                raw_photo.processed_at = timezone.now()
                raw_photo.save()
                
                # Copy to QRCardPhoto if assigned to a card
                if raw_photo.assigned_qr_card:
                    create_qr_card_photo_from_raw(raw_photo)
                
                processed_count += 1
                
                # Update progress
                batch.processed_photos = processed_count
                batch.save()
                
            except Exception as e:
                logger.error(f"Error processing photo {raw_photo.id}: {str(e)}")
                raw_photo.processing_error = str(e)
                raw_photo.save()
                processed_count += 1
                batch.processed_photos = processed_count
                batch.save()
        
        # Complete the batch
        batch.status = 'completed'
        batch.qr_codes_found = qr_codes_found
        batch.completed_at = timezone.now()
        batch.save()
        
        # Update QR card statuses
        update_qr_card_statuses(batch)
        
        logger.info(f"Completed QR analysis for batch {batch_id}: {qr_codes_found} QR codes found, {processed_count} photos processed")
        
        return {
            'success': True,
            'batch_id': batch_id,
            'total_photos': total_photos,
            'processed_photos': processed_count,
            'qr_codes_found': qr_codes_found
        }
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to analyze photo batch {batch_id}: {str(e)}")
        
        try:
            batch = PhotoUploadBatch.objects.get(id=batch_id)
            batch.status = 'failed'
            batch.error_message = str(e)
            batch.completed_at = timezone.now()
            batch.save()
        except:
            pass
        
        return {
            'success': False,
            'batch_id': batch_id,
            'error': str(e)
        }


def extract_qr_code_from_image(image_field):
    """Extract QR code data from an image using OpenCV and pyzbar"""
    try:
        # Read image from Django file field (works with S3/MinIO)
        image_field.open()
        image_data = image_field.read()
        image_field.close()
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect QR codes
        qr_codes = pyzbar.decode(gray)
        
        if qr_codes:
            # Return the first QR code found
            return qr_codes[0].data.decode('utf-8')
        
        return None
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error extracting QR code from image: {str(e)}")
        return None


def find_qr_card_by_url(qr_data, project):
    """Find QR card by matching the URL/code in QR data"""
    try:
        # QR data should be a URL like: http://localhost:3000/client/uuid?pin=1234
        if '/client/' in qr_data:
            # Extract UUID from URL
            parts = qr_data.split('/client/')
            if len(parts) > 1:
                uuid_part = parts[1].split('?')[0]  # Remove query parameters
                
                # Find QR card with this code
                return QRCard.objects.filter(
                    project=project,
                    code=uuid_part
                ).first()
        
        return None
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error finding QR card for data {qr_data}: {str(e)}")
        return None


def create_qr_card_photo_from_raw(raw_photo):
    """Create a QRCardPhoto from a RawPhotoUpload"""
    try:
        # Check if photo already exists
        if QRCardPhoto.objects.filter(
            qr_card=raw_photo.assigned_qr_card,
            original_filename=raw_photo.original_filename
        ).exists():
            return
        
        # Copy image file
        with raw_photo.image.open('rb') as source_file:
            content = ContentFile(source_file.read())
            
            qr_photo = QRCardPhoto.objects.create(
                qr_card=raw_photo.assigned_qr_card,
                original_filename=raw_photo.original_filename,
                taken_at=raw_photo.taken_at,
                file_size=raw_photo.file_size
            )
            
            # Save the image
            qr_photo.image.save(
                raw_photo.original_filename,
                content,
                save=True
            )
            
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating QRCardPhoto from raw photo {raw_photo.id}: {str(e)}")


def update_qr_card_statuses(batch):
    """Update QR card statuses after photo processing"""
    try:
        # Get all QR cards that received photos
        qr_cards_with_photos = QRCard.objects.filter(
            project=batch.project,
            raw_source_photos__batch=batch,
            raw_source_photos__assigned_qr_card__isnull=False
        ).distinct()
        
        for qr_card in qr_cards_with_photos:
            if qr_card.photos.exists():
                qr_card.status = 'photos_uploaded'
                qr_card.photos_uploaded_at = timezone.now()
                qr_card.save()
                
    except Exception as e:
        logging.getLogger(__name__).error(f"Error updating QR card statuses for batch {batch.id}: {str(e)}")


def extract_exif_datetime(image_field):
    """Extract datetime from EXIF data"""
    try:
        image_field.open()
        image = Image.open(image_field)
        exif = image.getexif()
        
        if exif:
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag == 'DateTime':
                    return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        
        image_field.close()
        return None
        
    except Exception:
        return None
