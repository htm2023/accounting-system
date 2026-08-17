from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/fiscal/', include('apps.fiscal.urls')),
    path('api/sequences/', include('apps.sequences.urls')),
    path('api/currencies/', include('apps.currencies.urls')),
    path('api/cost-centers/', include('apps.cost_centers.urls')),
    path('api/chart-of-accounts/', include('apps.chart_of_accounts.urls')),
    path('api/journal-entries/', include('apps.journal_entries.urls')),
    path('api/parties/', include('apps.parties.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/invoicing/', include('apps.invoicing.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/payroll/', include('apps.payroll.urls')),
    path('api/fixed-assets/', include('apps.fixed_assets.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
