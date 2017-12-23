from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import Note
from .forms import NoteForm
from .mixins import NoteMixin

@login_required
def index(request):
    # latest_note_list = Note.objects.order_by('-pub_date')[:5]
    latest_note_list = Note.objects.filter(owner=request.user).order_by('-pub_date')[:5]
    context = {
        'latest_note_list': latest_note_list,
    }
    return render(request, 'notes/index.html', context)

@login_required
def detail(request, note_id):
     note = get_object_or_404(Note, pk=note_id)
     return render(request, 'notes/detail.html', {'note': note})

class NoteList(ListView):
    paginate_by = 5
    template_name = 'notes/index.html'
    context_object_name = 'latest_note_list'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(NoteList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user).order_by('-pub_date')


class NoteDetail(DetailView):
    model = Note
    template_name = 'notes/detail.html'
    context_object_name = 'note'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(NoteDetail, self).dispatch(*args, **kwargs)

class NoteCreate(LoginRequiredMixin, NoteMixin, CreateView):
    form_class = NoteForm
    template_name = 'notes/form.html'
    success_url = reverse_lazy('notes:index')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.pub_date = timezone.now()
        return super(NoteCreate, self).form_valid(form)

class NoteUpdate(LoginRequiredMixin, NoteMixin, UpdateView):
    model = Note
    form_class = NoteForm
    template_name = 'notes/form.html'
    success_url = reverse_lazy('notes:index')

    def form_valid(self, form):
       form.instance.pub_date = timezone.now()
       return super(NoteUpdate, self).form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.owner != self.request.user:
            raise PermissionDenied

        return super(NoteUpdate, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.owner != self.request.user:
            raise PermissionDenied

        return super(NoteUpdate, self).post(request, *args, **kwargs)

class NoteDelete(LoginRequiredMixin, NoteMixin, DeleteView):
    model = Note
    success_url = reverse_lazy('notes:index')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.check_user_or_403(self.object.owner)
        return super(NoteDelete, self).post(request, *args, **kwargs)

def get(self, request, *args, **kwargs):
    self.object = self.get_object()

    if self.object.owner != self.request.user:
        raise PermissionDenied

    context = self.get_context_data(object=self.object)
    return self.render_to_response(context)

def get_success_url(self):
    return reverse('notes:update', kwargs={
        'pk': self.object.pk
    })
