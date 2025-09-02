from rest_framework import serializers
from .models import QRCard, QRCardBatch, QRCardPhoto, PhotoUploadBatch, RawPhotoUpload, PhotoUploadBatch, RawPhotoUpload

class QRCardPhotoSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.ReadOnlyField()
    
    class Meta:
        model = QRCardPhoto
        fields = ['id', 'image', 'original_filename', 'taken_at', 'uploaded_at', 'file_size', 'file_size_mb', 'is_processed']
        read_only_fields = ['id', 'uploaded_at', 'file_size', 'file_size_mb']

class QRCardSerializer(serializers.ModelSerializer):
    short_code = serializers.ReadOnlyField()
    has_client_info = serializers.ReadOnlyField()
    photo_count = serializers.ReadOnlyField()
    photos = QRCardPhotoSerializer(many=True, read_only=True)
    
    class Meta:
        model = QRCard
        fields = [
            'id', 'batch', 'project', 'code', 'short_code', 'pdf', 'qr_url',
            'access_pin', 'client_email', 'client_name', 'client_phone',
            'session_notes', 'location_name', 'status', 
            'created_at', 'scanned_at', 'info_provided_at', 'photos_uploaded_at', 'completed_at',
            'has_client_info', 'photo_count', 'photos'
        ]
        read_only_fields = ['id', 'pdf', 'qr_url', 'created_at', 'short_code', 'has_client_info', 'photo_count']

class QRCardDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for QR card management by photographers"""
    short_code = serializers.ReadOnlyField()
    has_client_info = serializers.ReadOnlyField()
    photo_count = serializers.ReadOnlyField()
    photos = QRCardPhotoSerializer(many=True, read_only=True)
    
    class Meta:
        model = QRCard
        fields = [
            'id', 'batch', 'project', 'code', 'short_code', 'pdf', 'qr_url',
            'access_pin', 'client_email', 'client_name', 'client_phone',
            'session_notes', 'location_name', 'status', 
            'created_at', 'scanned_at', 'info_provided_at', 'photos_uploaded_at', 'completed_at',
            'has_client_info', 'photo_count', 'photos'
        ]
        read_only_fields = ['id', 'pdf', 'qr_url', 'created_at', 'short_code', 'has_client_info', 'photo_count', 'scanned_at', 'info_provided_at', 'photos_uploaded_at', 'completed_at']

class QRCardClientSerializer(serializers.ModelSerializer):
    """Serializer for client (tourist) interaction with QR codes"""
    short_code = serializers.ReadOnlyField()
    photo_count = serializers.ReadOnlyField()
    photos = QRCardPhotoSerializer(many=True, read_only=True)
    project = serializers.SerializerMethodField()
    
    class Meta:
        model = QRCard
        fields = [
            'id', 'short_code', 'client_email', 'client_name', 'client_phone',
            'location_name', 'status', 'photo_count', 'photos', 'project'
        ]
        read_only_fields = ['id', 'short_code', 'status', 'photo_count', 'location_name', 'project']
    
    def get_project(self, obj):
        """Return project information for the client"""
        return {
            'id': obj.project.id,
            'name': obj.project.name,
            'description': obj.project.description
        }

class QRCardBatchSerializer(serializers.ModelSerializer):
    qrcards_count = serializers.SerializerMethodField()
    
    class Meta:
        model = QRCardBatch
        fields = ['id', 'project', 'name', 'pdf', 'amount', 'size', 'per_page', 'created_at', 'qrcards_count']
        read_only_fields = ['id', 'pdf', 'created_at', 'qrcards_count']
    
    def get_qrcards_count(self, obj):
        return obj.qrcards.count()

class QRCardGenerationOptionsSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1, max_value=1000, default=100)
    size = serializers.ChoiceField(choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], default='medium')
    per_page = serializers.IntegerField(min_value=1, max_value=48, default=12)
    project = serializers.IntegerField()
    name = serializers.CharField(max_length=255, required=False, default="QR Card Batch")

class PhotoUploadBatchSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = PhotoUploadBatch
        fields = [
            'id', 'project', 'name', 'status', 'total_photos', 'processed_photos', 
            'qr_codes_found', 'progress_percentage', 'created_at', 'processing_started_at', 
            'completed_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'status', 'total_photos', 'processed_photos', 'qr_codes_found', 
            'progress_percentage', 'created_at', 'processing_started_at', 'completed_at', 'error_message'
        ]

class RawPhotoUploadSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.ReadOnlyField()
    
    class Meta:
        model = RawPhotoUpload
        fields = [
            'id', 'batch', 'image', 'original_filename', 'taken_at', 'camera_make', 
            'camera_model', 'file_size', 'file_size_mb', 'is_processed', 'has_qr_code', 
            'qr_code_data', 'assigned_qr_card', 'processing_error', 'uploaded_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'file_size_mb', 'is_processed', 'has_qr_code', 
            'qr_code_data', 'assigned_qr_card', 'processing_error', 'uploaded_at', 'processed_at'
        ]
