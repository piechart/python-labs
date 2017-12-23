from .models import Note

class NoteMixin(object):
    def get_context_data(self, **kwargs):
       context = super(NoteMixin, self).get_context_data(**kwargs)

       context.update({
          'notes': Note.objects.filter(owner=self.request.user).order_by('-pub_date'),
       })

       return context

    def check_user_or_403(self, user):
        if self.request.user != user:
            raise PermissionDenied
