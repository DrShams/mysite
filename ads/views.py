from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.uploadedfile import InMemoryUploadedFile
from ads.owner import OwnerListView, OwnerDetailView, OwnerDeleteView
from ads.models import Ad, Comment, Fav
from ads.forms import CreateForm, CommentForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError
from django.contrib.humanize.templatetags.humanize import naturaltime

from ads.utils import dump_queries

from django.db.models import Q
from django.contrib.auth import logout
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)
class AdListView(OwnerListView):
    model = Ad
    template_name = 'ads/ad_list.html'

    def get(self, request) :
        ad_list = Ad.objects.all()
        favorites = list()
        if request.user.is_authenticated:
            # rows = [{'id': 2}, {'id': 4} ... ]  (A list of rows)
            rows = request.user.favorite_ads.values('id')
            # favorites = [2, 4, ...] using list comprehension
            favorites = [ row['id'] for row in rows ]

        strval =  request.GET.get("search", False)
        if strval :
            # Simple title-only search
            # objects = Ad.objects.filter(title__contains=strval).select_related().order_by('-updated_at')[:10]

            # Multi-field search
            query = Q(title__contains=strval)
            query.add(Q(text__contains=strval), Q.OR)
            query.add(Q(tags__name__in=[strval]), Q.OR)  # Search by tag
            ad_list = Ad.objects.filter(query).select_related().distinct().order_by('-updated_at')[:10]
        else :
            # try both versions with > 4 ads and watch the queries that happen
            ad_list = Ad.objects.all().order_by('-updated_at')[:10]
            # objects = Ad.objects.select_related().all().order_by('-updated_at')[:10]

        # Augment the ad_list
        for ad in ad_list:
            ad.natural_updated = naturaltime(ad.updated_at)

        ctx = {'ad_list' : ad_list, 'favorites': favorites, 'search': strval}

        retval = render(request, self.template_name, ctx)
        dump_queries()

        return retval;



class AdDetailView(OwnerDetailView):
    model = Ad
    template_name = 'ads/ad_detail.html'
    def get(self, request, pk) :
        #x = Ad.objects.get(id=pk)
        x = get_object_or_404(Ad, id=pk)
        comments = Comment.objects.filter(ad=x).order_by('-updated_at')
        comment_form = CommentForm()
        context = { 'ad' : x, 'comments': comments, 'comment_form': comment_form }
        return render(request, self.template_name, context)


class AdCreateView(LoginRequiredMixin, View):
    template_name = 'ads/ad_form.html'
    success_url = reverse_lazy('ads:all')

    def get(self, request, pk=None):
        form = CreateForm()
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        form = CreateForm(request.POST, request.FILES or None)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        # Add owner to the model before saving
        ad = form.save(commit=False)
        ad.owner = self.request.user
        ad.save()
        form.save_m2m()  # Save tags
        return redirect(self.success_url)


class AdUpdateView(LoginRequiredMixin, View):
    template_name = 'ads/ad_form.html'
    success_url = reverse_lazy('ads:all')

    def get(self, request, pk):
        ad = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(instance=ad)
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        ad = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(request.POST, request.FILES or None, instance=ad)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        ad = form.save(commit=False)
        ad.save()
        form.save_m2m()  # Save tags
        return redirect(self.success_url)


class AdDeleteView(OwnerDeleteView):
    model = Ad


def stream_file(request, pk):
    ad = get_object_or_404(Ad, id=pk)
    response = HttpResponse()
    response['Content-Type'] = ad.content_type
    response['Content-Length'] = len(ad.picture)
    response.write(ad.picture)
    return response

class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        f = get_object_or_404(Ad, id=pk)
        comment = Comment(text=request.POST['comment'], owner=request.user, ad=f)
        comment.save()
        return redirect(reverse('ads:ad_detail', args=[pk]))

class CommentDeleteView(OwnerDeleteView):
    model = Comment
    template_name = "ads/ad_comment_delete.html"

    # https://stackoverflow.com/questions/26290415/deleteview-with-a-dynamic-success-url-dependent-on-id
    def get_success_url(self):
        ad = self.object.ad
        return reverse('ads:ad_detail', args=[ad.id])


@method_decorator(csrf_exempt, name='dispatch')
class AddFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Add PK",pk)
        a = get_object_or_404(Ad, id=pk)
        fav = Fav(user=request.user, ad=a)
        try:
            fav.save()  # In case of duplicate key
        except IntegrityError as e:
            pass
        return HttpResponse()

@method_decorator(csrf_exempt, name='dispatch')
class DeleteFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Delete PK",pk)
        a = get_object_or_404(Ad, id=pk)
        try:
            fav = Fav.objects.get(user=request.user, ad=a).delete()
        except Fav.DoesNotExist as e:
            pass

        return HttpResponse()
    
def custom_logout(request):
    logout(request)  # Logs out the user
    logger.info("User has logged out")  # Logs to the console
    return render(request, "registration/logout.html")  # Render the logout confirmation page

def stream_file(request, pk):
    ad = get_object_or_404(Ad, id=pk)
    
    # Check if the ad has a picture associated with it
    if not ad.picture:
        return HttpResponse("No picture available.", status=404)

    response = HttpResponse()
    
    # Set the Content-Type from the ad's content_type
    response['Content-Type'] = ad.content_type if ad.content_type else 'application/octet-stream'
    response['Content-Length'] = len(ad.picture)
    
    # Write the picture data to the response
    response.write(ad.picture)
    
    return response
