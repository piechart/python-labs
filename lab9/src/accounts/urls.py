from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.core.urlresolvers import reverse_lazy

from .views import RegisterView

urlpatterns = [
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, {"next_page" : reverse_lazy('accounts:login')}, name='logout'),
    url('^register/', RegisterView.as_view(), name='register'),
]
