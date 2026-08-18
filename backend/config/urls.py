from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic import TemplateView
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
    path('api/audit/', include('apps.audit_logs.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# عند التشغيل من عملية واحدة (مثل Replit) تخدم Django واجهة React المبنية
# مباشرة؛ على Render الواجهة خدمة static منفصلة فلا يُستخدم هذا المسار إطلاقًا.
if getattr(settings, 'SERVE_FRONTEND', False):
    urlpatterns += [
        re_path(r'^(?!api/|admin/|static/).*$', TemplateView.as_view(template_name='index.html')),
    ]
