from django.conf.urls import url
from .views import NoteList, NoteDetail, NoteCreate

from . import views

urlpatterns = [
    url(r'^$', NoteList.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', NoteDetail.as_view(), name='detail'),
    url(r'^new/$', NoteCreate.as_view(), name='create'),
]
