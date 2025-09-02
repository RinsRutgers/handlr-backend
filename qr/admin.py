from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import QRCard, QRCardBatch, QRCardPhoto, PhotoUploadBatch, RawPhotoUpload


@admin.register(QRCardBatch)
class QRCardBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_at', 'qr_cards_count')
    list_filter = ('created_at', 'project')
    search_fields = ('name', 'project__name')
    readonly_fields = ('created_at',)
    
    def qr_cards_count(self, obj):
        return obj.qrcards.count()
    qr_cards_count.short_description = 'QR Cards'


@admin.register(QRCard)
class QRCardAdmin(admin.ModelAdmin):
    list_display = ('short_code', 'status', 'client_name', 'client_email', 'photo_count', 'qr_code_thumbnail', 'project', 'created_at')
    list_filter = ('status', 'created_at', 'project')
    search_fields = ('code', 'short_code', 'client_name', 'client_email')
    readonly_fields = ('code', 'short_code', 'access_pin', 'qr_code_display', 'qr_url_display', 'created_at', 'scanned_at', 'info_provided_at', 'photos_uploaded_at', 'completed_at')
    
    fieldsets = (
        ('QR Code Info', {
            'fields': ('code', 'short_code', 'access_pin', 'batch', 'project')
        }),
        ('QR Code Display', {
            'fields': ('qr_code_display', 'qr_url_display')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'scanned_at', 'info_provided_at', 'photos_uploaded_at', 'completed_at')
        }),
        ('Client Information', {
            'fields': ('client_name', 'client_email', 'client_phone')
        }),
        ('Session Details', {
            'fields': ('location_name', 'session_notes')
        })
    )
    
    def photo_count(self, obj):
        return obj.photos.count()
    photo_count.short_description = 'Photos'
    
    def qr_code_thumbnail(self, obj):
        """Display a small QR code thumbnail in the list view"""
        if obj.qr_url:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px;" />',
                obj.qr_url
            )
        return 'No QR'
    qr_code_thumbnail.short_description = 'QR Code'
    
    def qr_code_display(self, obj):
        """Display the QR code as an image"""
        if obj.qr_url:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" /><br>'
                '<a href="{}" target="_blank">Download QR Code</a>',
                obj.qr_url,
                obj.qr_url
            )
        return 'No QR code generated'
    qr_code_display.short_description = 'QR Code'
    
    def qr_url_display(self, obj):
        """Display the QR code URL as a clickable link"""
        if obj.qr_url:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.qr_url,
                obj.qr_url
            )
        return 'No QR code URL'
    qr_url_display.short_description = 'QR Code URL'


@admin.register(QRCardPhoto)
class QRCardPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'qr_card_info', 'original_filename', 'file_size_mb', 'uploaded_at', 'image_preview')
    list_filter = ('uploaded_at', 'qr_card__project')
    search_fields = ('original_filename', 'qr_card__short_code', 'qr_card__client_name')
    readonly_fields = ('file_size', 'file_size_mb', 'uploaded_at', 'image_preview')
    
    def qr_card_info(self, obj):
        if obj.qr_card:
            return format_html(
                '<a href="{}">{}</a> ({})', 
                reverse('admin:qr_qrcard_change', args=[obj.qr_card.pk]),
                obj.qr_card.short_code,
                obj.qr_card.client_name or 'No name'
            )
        return 'No QR Card'
    qr_card_info.short_description = 'QR Card'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url
            )
        return 'No image'
    image_preview.short_description = 'Preview'


@admin.register(PhotoUploadBatch)
class PhotoUploadBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'status', 'total_photos', 'processed_photos', 'qr_codes_found', 'progress_percentage', 'created_at')
    list_filter = ('status', 'created_at', 'project')
    search_fields = ('name', 'project__name')
    readonly_fields = ('created_at', 'completed_at', 'progress_percentage')
    
    fieldsets = (
        ('Batch Info', {
            'fields': ('name', 'project', 'created_at', 'completed_at')
        }),
        ('Progress', {
            'fields': ('status', 'total_photos', 'processed_photos', 'qr_codes_found', 'progress_percentage', 'error_message')
        })
    )


@admin.register(RawPhotoUpload)
class RawPhotoUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch_info', 'original_filename', 'file_size_mb', 'has_qr_code', 'assigned_qr_card_info', 'is_processed', 'uploaded_at', 'image_preview')
    list_filter = ('has_qr_code', 'is_processed', 'uploaded_at', 'batch__project')
    search_fields = ('original_filename', 'batch__name', 'assigned_qr_card__short_code')
    readonly_fields = ('file_size', 'file_size_mb', 'uploaded_at', 'image_preview')
    
    def batch_info(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:qr_photouploadbatch_change', args=[obj.batch.pk]),
            obj.batch.name
        )
    batch_info.short_description = 'Batch'
    
    def assigned_qr_card_info(self, obj):
        if obj.assigned_qr_card:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:qr_qrcard_change', args=[obj.assigned_qr_card.pk]),
                obj.assigned_qr_card.short_code
            )
        return 'Not assigned'
    assigned_qr_card_info.short_description = 'Assigned QR Card'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url
            )
        return 'No image'
    image_preview.short_description = 'Preview'


# Customize admin site headers
admin.site.site_header = 'SpotShoot Admin'
admin.site.site_title = 'SpotShoot'
admin.site.index_title = 'Welcome to SpotShoot Administration'
