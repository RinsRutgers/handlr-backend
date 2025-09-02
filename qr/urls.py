from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QRCardViewSet, QRCardBatchViewSet, QRCardClientViewSet, 
    PhotoUploadBatchViewSet, PhotoUploadSignedURLViewSet
)

router = DefaultRouter()
router.register(r'qrcards', QRCardViewSet, basename='qrcard')
router.register(r'qrcard-batches', QRCardBatchViewSet, basename='qrcardbatch')
router.register(r'client', QRCardClientViewSet, basename='qrcard-client')
router.register(r'photo-batches', PhotoUploadBatchViewSet, basename='photo-batch')
router.register(r'upload', PhotoUploadSignedURLViewSet, basename='photo-upload')

urlpatterns = [
    path('', include(router.urls)),
]
