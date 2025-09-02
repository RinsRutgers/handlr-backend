from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
import io
import qrcode
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import QRCard, QRCardBatch, QRCardPhoto, PhotoUploadBatch, RawPhotoUpload
from .serializers import (
    QRCardSerializer, QRCardBatchSerializer, QRCardGenerationOptionsSerializer,
    QRCardDetailSerializer, QRCardClientSerializer, QRCardPhotoSerializer,
    PhotoUploadBatchSerializer, RawPhotoUploadSerializer
)
from projects.models import Project
from .tasks import generate_qr_pdf_task, analyze_photo_batch_for_qr_codes
import uuid
import random
import string
import boto3
from botocore.exceptions import ClientError
import mimetypes
from datetime import datetime, timedelta

# Create your views here.

def get_s3_client():
    """Get configured S3 client"""
    return boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

def generate_s3_key(project_id, filename):
    """Generate S3 key for photo upload"""
    # Create a unique key with timestamp and UUID
    timestamp = datetime.now().strftime('%Y/%m/%d')
    unique_id = str(uuid.uuid4())[:8]
    return f"qr_photos/{timestamp}/{project_id}/{unique_id}_{filename}"

class PhotoUploadSignedURLViewSet(viewsets.ViewSet):
    """ViewSet for generating S3 signed upload URLs"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate_upload_urls(self, request):
        """Generate signed upload URLs for multiple photos"""
        project_id = request.data.get('project_id')
        files = request.data.get('files', [])  # List of {filename, content_type, size}
        batch_name = request.data.get('batch_name', 'Photo Batch')
        
        if not project_id:
            return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not files:
            return Response({'error': 'files list is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create photo upload batch
        batch = PhotoUploadBatch.objects.create(
            project=project,
            name=batch_name,
            total_photos=len(files),
            status='uploading'
        )
        
        s3_client = get_s3_client()
        upload_urls = []
        
        for file_info in files:
            filename = file_info.get('filename')
            content_type = file_info.get('content_type')
            file_size = file_info.get('size', 0)
            
            if not filename or not content_type:
                continue
            
            # Validate file type
            if not content_type.startswith('image/'):
                continue
            
            # Generate S3 key
            s3_key = generate_s3_key(project_id, filename)
            
            # Create RawPhotoUpload record
            raw_photo = RawPhotoUpload.objects.create(
                batch=batch,
                original_filename=filename,
                file_size=file_size,
                s3_key=s3_key,
                is_processed=False
            )
            
            try:
                # Generate presigned URL for upload (expires in 1 hour)
                presigned_url = s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': s3_key,
                        'ContentType': content_type
                    },
                    ExpiresIn=3600  # 1 hour
                )
                
                upload_urls.append({
                    'photo_id': raw_photo.id,
                    'filename': filename,
                    'upload_url': presigned_url,
                    's3_key': s3_key,
                    'content_type': content_type
                })
                
            except ClientError as e:
                return Response({'error': f'Failed to generate upload URL: {str(e)}'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'batch_id': batch.id,
            'upload_urls': upload_urls
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def confirm_uploads(self, request):
        """Confirm completed uploads and start QR code analysis"""
        batch_id = request.data.get('batch_id')
        completed_uploads = request.data.get('completed_uploads', [])  # List of photo_ids
        
        if not batch_id:
            return Response({'error': 'batch_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            batch = PhotoUploadBatch.objects.get(id=batch_id, project__user=request.user)
        except PhotoUploadBatch.DoesNotExist:
            return Response({'error': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update raw photo records for completed uploads
        s3_client = get_s3_client()
        successful_uploads = 0
        
        for photo_id in completed_uploads:
            try:
                raw_photo = RawPhotoUpload.objects.get(id=photo_id, batch=batch)
                
                # Verify file exists in S3
                try:
                    s3_client.head_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=raw_photo.s3_key
                    )
                    
                    # Update the image field with S3 URL
                    raw_photo.image.name = raw_photo.s3_key
                    raw_photo.is_processed = False  # Will be processed by Celery task
                    raw_photo.save()
                    successful_uploads += 1
                    
                except ClientError:
                    # File not found in S3, mark as failed
                    raw_photo.processing_error = "File not found in S3 after upload"
                    raw_photo.save()
                    
            except RawPhotoUpload.DoesNotExist:
                continue
        
        # Update batch status
        batch.total_photos = successful_uploads
        if successful_uploads > 0:
            batch.status = 'analyzing'
            batch.save()
            
            # Start QR code analysis
            task = analyze_photo_batch_for_qr_codes.delay(batch.id)
            
            return Response({
                'batch_id': batch.id,
                'successful_uploads': successful_uploads,
                'analysis_started': True,
                'task_id': task.id
            }, status=status.HTTP_200_OK)
        else:
            batch.status = 'failed'
            batch.error_message = 'No files were successfully uploaded'
            batch.save()
            
            return Response({
                'error': 'No files were successfully uploaded',
                'batch_id': batch.id
            }, status=status.HTTP_400_BAD_REQUEST)

class QRCardBatchViewSet(viewsets.ModelViewSet):
    serializer_class = QRCardBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = QRCardBatch.objects.filter(project__user=self.request.user)
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.order_by('-created_at')

class QRCardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QRCardDetailSerializer
        return QRCardSerializer

    def get_queryset(self):
        queryset = QRCard.objects.filter(project__user=self.request.user).select_related('batch', 'project').prefetch_related('photos')
        
        # Filter by project
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filter by batch
        batch_id = self.request.query_params.get('batch')
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(client_email__icontains=search) |
                Q(client_name__icontains=search) |
                Q(location_name__icontains=search) |
                Q(session_notes__icontains=search)
            )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_photos(self, request, pk=None):
        """Upload photos for a specific QR card"""
        qr_card = self.get_object()
        
        if 'photos' not in request.FILES:
            return Response({'error': 'No photos provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        photos = request.FILES.getlist('photos')
        uploaded_photos = []
        
        for photo in photos:
            # Validate file type
            if not photo.content_type.startswith('image/'):
                continue
            
            photo_obj = QRCardPhoto.objects.create(
                qr_card=qr_card,
                image=photo,
                original_filename=photo.name,
                file_size=photo.size
            )
            uploaded_photos.append(photo_obj)
        
        # Update QR card status and timestamp
        if uploaded_photos and qr_card.status in ['distributed', 'scanned', 'info_provided']:
            qr_card.status = 'photos_uploaded'
            qr_card.photos_uploaded_at = timezone.now()
            qr_card.save()
        
        serializer = QRCardPhotoSerializer(uploaded_photos, many=True)
        return Response({
            'message': f'Successfully uploaded {len(uploaded_photos)} photos',
            'photos': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def update_session_info(self, request, pk=None):
        """Update session notes and location info"""
        qr_card = self.get_object()
        
        if 'session_notes' in request.data:
            qr_card.session_notes = request.data['session_notes']
        if 'location_name' in request.data:
            qr_card.location_name = request.data['location_name']
        
        qr_card.save()
        
        serializer = self.get_serializer(qr_card)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark QR card as completed (photos delivered)"""
        qr_card = self.get_object()
        
        if qr_card.status != 'photos_uploaded':
            return Response(
                {'error': 'QR card must have photos uploaded before marking as completed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        qr_card.status = 'completed'
        qr_card.completed_at = timezone.now()
        qr_card.save()
        
        serializer = self.get_serializer(qr_card)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        options_serializer = QRCardGenerationOptionsSerializer(data=request.data)
        if not options_serializer.is_valid():
            return Response(options_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        opts = options_serializer.validated_data
        project_id = opts['project']
        amount = opts['amount']
        size = opts['size']
        per_page = opts['per_page']
        batch_name = opts.get('name', 'QR Card Batch')
        
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Start Celery task and get result
        task = generate_qr_pdf_task.delay(project.id, amount, size, per_page, batch_name)
        
        # Wait for task to complete (max 30 seconds)
        try:
            result = task.get(timeout=30)
            if result.get('success', False):
                return Response({
                    'success': True,
                    'batch_id': result['batch_id'],
                    'pdf_name': result['pdf_name'],
                    'codes_generated': result['codes_generated'],
                    'message': f'Successfully generated {result["codes_generated"]} QR codes'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Unknown error occurred'),
                    'message': 'Failed to generate QR batch'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Task failed or timed out'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QRCardClientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for client (tourist) interaction with QR codes"""
    serializer_class = QRCardClientSerializer
    permission_classes = [permissions.AllowAny]  # Accessible without authentication
    
    def get_queryset(self):
        return QRCard.objects.all()
    
    def retrieve(self, request, pk=None):
        """Get QR card details using code and PIN"""
        code = pk  # The QR code
        pin = request.query_params.get('pin')
        
        if not pin:
            return Response({'error': 'PIN is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            qr_card = QRCard.objects.get(code=code, access_pin=pin)
        except QRCard.DoesNotExist:
            return Response({'error': 'Invalid QR code or PIN'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update status if first scan
        if qr_card.status == 'distributed':
            qr_card.status = 'scanned'
            qr_card.scanned_at = timezone.now()
            qr_card.save()
        
        serializer = self.get_serializer(qr_card)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def provide_info(self, request, pk=None):
        """Client provides their contact information"""
        code = pk
        pin = request.data.get('pin')
        
        if not pin:
            return Response({'error': 'PIN is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            qr_card = QRCard.objects.get(code=code, access_pin=pin)
        except QRCard.DoesNotExist:
            return Response({'error': 'Invalid QR code or PIN'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update client information
        qr_card.client_email = request.data.get('email')
        qr_card.client_name = request.data.get('name')
        qr_card.client_phone = request.data.get('phone', '')
        
        if qr_card.status in ['distributed', 'scanned']:
            qr_card.status = 'info_provided'
            qr_card.info_provided_at = timezone.now()
        
        qr_card.save()
        
        serializer = self.get_serializer(qr_card)
        return Response(serializer.data)

class PhotoUploadBatchViewSet(viewsets.ModelViewSet):
    serializer_class = PhotoUploadBatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = PhotoUploadBatch.objects.filter(project__user=self.request.user)
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['post'])
    def upload_photos(self, request):
        """Upload photos for QR code analysis"""
        project_id = request.data.get('project')
        batch_name = request.data.get('name', 'Photo Batch')
        
        if not project_id:
            return Response({'error': 'Project ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if 'photos' not in request.FILES:
            return Response({'error': 'No photos provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        photos = request.FILES.getlist('photos')
        if not photos:
            return Response({'error': 'No photos provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create batch
        batch = PhotoUploadBatch.objects.create(
            project=project,
            name=batch_name,
            total_photos=len(photos)
        )
        
        uploaded_photos = []
        
        for photo in photos:
            # Validate file type
            if not photo.content_type.startswith('image/'):
                continue
            
            # Create raw photo upload
            raw_photo = RawPhotoUpload.objects.create(
                batch=batch,
                image=photo,
                original_filename=photo.name,
                file_size=photo.size
            )
            
            # Try to extract EXIF datetime
            try:
                from .tasks import extract_exif_datetime
                taken_at = extract_exif_datetime(raw_photo.image)
                if taken_at:
                    raw_photo.taken_at = taken_at
                    raw_photo.save()
            except:
                pass
            
            uploaded_photos.append(raw_photo)
        
        # Update batch with actual count
        batch.total_photos = len(uploaded_photos)
        batch.save()
        
        # Start QR code analysis
        task = analyze_photo_batch_for_qr_codes.delay(batch.id)
        
        return Response({
            'batch_id': batch.id,
            'photos_uploaded': len(uploaded_photos),
            'analysis_started': True,
            'task_id': task.id
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get upload batch progress"""
        batch = self.get_object()
        
        return Response({
            'id': batch.id,
            'name': batch.name,
            'status': batch.status,
            'total_photos': batch.total_photos,
            'processed_photos': batch.processed_photos,
            'qr_codes_found': batch.qr_codes_found,
            'progress_percentage': batch.progress_percentage,
            'error_message': batch.error_message,
            'created_at': batch.created_at,
            'completed_at': batch.completed_at
        })
    
    @action(detail=True, methods=['get'])
    def photos(self, request, pk=None):
        """Get photos in the batch with their assignments"""
        batch = self.get_object()
        
        raw_photos = batch.raw_photos.select_related('assigned_qr_card').order_by('taken_at', 'uploaded_at')
        
        photos_data = []
        for photo in raw_photos:
            photos_data.append({
                'id': photo.id,
                'filename': photo.original_filename,
                'image_url': request.build_absolute_uri(photo.image.url),
                'taken_at': photo.taken_at,
                'file_size_mb': photo.file_size_mb,
                'has_qr_code': photo.has_qr_code,
                'qr_code_data': photo.qr_code_data,
                'assigned_qr_card': {
                    'id': photo.assigned_qr_card.id,
                    'short_code': photo.assigned_qr_card.short_code,
                    'access_pin': photo.assigned_qr_card.access_pin
                } if photo.assigned_qr_card else None,
                'is_processed': photo.is_processed,
                'processing_error': photo.processing_error
            })
        
        return Response({
            'batch': {
                'id': batch.id,
                'name': batch.name,
                'status': batch.status,
                'progress_percentage': batch.progress_percentage
            },
            'photos': photos_data
        })
