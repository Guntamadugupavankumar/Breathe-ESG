from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from ingestion.views import (
    TenantViewSet, IngestionRunViewSet, EmissionRowViewSet,
    UploadView, DashboardStatsView
)

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'runs', IngestionRunViewSet, basename='run')
router.register(r'rows', EmissionRowViewSet, basename='row')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/upload/', UploadView.as_view()),
    path('api/dashboard/', DashboardStatsView.as_view()),
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)