from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include
from django.http import HttpResponseRedirect

urlpatterns = [
    url(r'^$', lambda r: HttpResponseRedirect('notes/')),
    url(r'^admin/', admin.site.urls),
    # apps
    url(r'^accounts/', include('accounts.urls', namespace="accounts")),
    url(r'^notes/', include('notes.urls', namespace="notes")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
