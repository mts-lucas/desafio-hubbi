from django.urls import path
from django.views.generic import RedirectView
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)

from .views import *

urlpatterns = [
    path('', RedirectView.as_view(url='schema/swagger/')),
    path('parts/', PartListView.as_view(), name='part_list'),
    path('parts/<int:pk>/', PartDetailView.as_view(), name='part_detail'),
    path('parts/import-csv/', PartImportView.as_view(), name='part-import-csv'),
]

#  Swagger e Redoc
urlpatterns += [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]