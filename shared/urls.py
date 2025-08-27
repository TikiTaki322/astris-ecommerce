from django.views.generic import TemplateView
from django.urls import path

from .views import delete_session_keys


app_name = 'shared'

urlpatterns = [
    path('delete-session', delete_session_keys, name='delete_session_keys'),
    path('permission-denied', TemplateView.as_view(template_name='shared/permission_denied.html'), name='permission_denied'),
]