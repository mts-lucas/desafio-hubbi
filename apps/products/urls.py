from django.urls import path

from .views import *

urlpatterns = [
    path('parts/', PartListView.as_view(), name='part_list'),
    path('parts/<int:pk>/', PartDetailView.as_view(), name='part_detail'),
    path('parts/import-csv/', PartImportView.as_view(), name='part-import-csv'),
]