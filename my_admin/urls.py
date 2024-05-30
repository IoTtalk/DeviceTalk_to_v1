from django.urls import path

from .views import (
    IndexView,
    BasicFileView,
    LanguageView
)

app_name = 'my_admin'

urlpatterns = [
    path('', IndexView.as_view(), name='index_endpoint'),
    path('file', BasicFileView.as_view(), name='file_endpoint'),
    path('language', LanguageView.as_view(), name='language_endpoint'),
]
