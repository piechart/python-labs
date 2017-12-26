from django.conf.urls import url
from .views import NoteList, NoteDetail, NoteCreate, NoteUpdate, NoteDelete

from . import views

urlpatterns = [
    url(r'^$', NoteList.as_view(), name='index'),
    url(r'^search/(.*?)$', NoteList.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', NoteDetail.as_view(), name='detail'),
    url(r'^new/$', NoteCreate.as_view(), name='create'),
    url(r'^(?P<pk>[0-9]+)/edit/$', NoteUpdate.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', NoteDelete.as_view(), name='delete'),
]
