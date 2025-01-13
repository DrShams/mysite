from django.http import HttpResponse
from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'hello/main.html'

    def get(self, request, *args, **kwargs):
        # Set cookies here
        oldval = request.COOKIES.get('zap', None)
        response = super().get(request, *args, **kwargs)
        
        if oldval:
            response.set_cookie('zap', int(oldval) + 1)  # No expired date = until browser close
        else:
            response.set_cookie('zap', 42)  # No expired date = until browser close
        response.set_cookie('sakaicar', 42, max_age=1000)  # seconds until expire
        response.set_cookie('dj4e_cookie', 'baa67ffe', max_age=1000)  # Additional cookie

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the number of visits from session
        num_visits = self.request.session.get('num_visits', 0) + 1
        
        self.request.session['num_visits'] = num_visits
        if num_visits > 3 : del(self.request.session['num_visits'])
        context['num_visits'] = num_visits
        
        return context
