from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('shared/', include('shared.urls')),
    path('payments/', include('payments.urls')),
]

# exclude in production
if settings.DEBUG:

    # urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
    # urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
