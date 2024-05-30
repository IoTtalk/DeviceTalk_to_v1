from django.urls import path
from .views import (
    UploadSetupView,
    FileView
)

app_name = 'file_handle'

urlpatterns = [
    path('', UploadSetupView.as_view(), name='upload_setup_endpoint'),
    path('<str:uuid>', FileView.as_view(), name='file_endpoint')
]
