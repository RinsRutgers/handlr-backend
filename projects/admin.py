from django.contrib import admin
from django.utils.html import format_html
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'qr_batches_count', 'photo_batches_count', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('name', 'description', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Project Info', {
            'fields': ('name', 'description', 'user')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    
    def qr_batches_count(self, obj):
        return obj.qr_cards.count()
    qr_batches_count.short_description = 'QR Cards'
    
    def photo_batches_count(self, obj):
        return obj.photo_batches.count()
    photo_batches_count.short_description = 'Photo Batches'
