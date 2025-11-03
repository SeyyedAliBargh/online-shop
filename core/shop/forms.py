from django import forms
from .models import *


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            "body": forms.Textarea(attrs={
                "class": "boddy_comment",
                "placeholder": "توضبحات"
            }),
        }

class SearchForm(forms.Form):
    query = forms.CharField(widget=forms.TextInput(attrs={'class':'header__search_input'}))


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score']
        widgets = {
            'score': forms.RadioSelect(choices=[(i, str(i)) for i in range(1,6)]),
            'comment': forms.Textarea(attrs={'rows':3, 'placeholder':'نظر شما (اختیاری)'}),
        }