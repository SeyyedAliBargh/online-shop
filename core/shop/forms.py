from django import forms
from .models import Comment, Rating


class CommentForm(forms.ModelForm):
    """
    Form for submitting product comments.
    Contains only the 'body' field for user input.
    """
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            "body": forms.Textarea(attrs={
                "rows": 4,
            }),
        }


class SearchForm(forms.Form):
    """
    Simple search form used for querying products.
    """
    query = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Search for products...',
            }
        )
    )


class RatingForm(forms.ModelForm):
    """
    Form for submitting a rating for a product (1–5 stars).
    Uses radio buttons for rating selection.
    """
    class Meta:
        model = Rating
        fields = ['score']
        widgets = {
            'score': forms.RadioSelect(
                choices=[(i, str(i)) for i in range(1, 6)]
            ),
        }
