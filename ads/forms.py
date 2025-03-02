from django import forms
from ads.models import Ad
from django.core.files.uploadedfile import InMemoryUploadedFile
from ads.humanize import naturalsize
from taggit.forms import TagField


# Create the form class.
class CreateForm(forms.ModelForm):
    max_upload_limit = 2 * 1024 * 1024
    max_upload_limit_text = naturalsize(max_upload_limit)
    tags = TagField(required=False)

    class Meta:
        model = Ad
        fields = ['title', 'text', 'price', 'picture', 'tags']

    def clean_picture(self):
        pic = self.cleaned_data.get('picture')
        if pic and pic.size > self.max_upload_limit:
            raise forms.ValidationError(f"File size must be < {self.max_upload_limit / (1024 * 1024)} MB")
        return pic

    # Convert uploaded File object to a picture
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()  # Ensure many-to-many fields like tags are saved
        return instance

class CommentForm(forms.Form):
    comment = forms.CharField(required=True, max_length=500, min_length=3, strip=True)

# https://docs.djangoproject.com/en/3.0/toads/http/file-uploads/
# https://stackoverflow.com/questions/2472422/django-file-upload-size-limit
# https://stackoverflow.com/questions/32007311/how-to-change-data-in-django-modelform
# https://docs.djangoproject.com/en/3.0/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
