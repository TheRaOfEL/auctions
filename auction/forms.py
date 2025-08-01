from django import forms


from .models import Bid, AuctionListing, NewsletterSubscriber


class AuctionForm(forms.ModelForm):
    class Meta:
        model = AuctionListing
        fields = ['name', 'description', 'starting_bid', 'image', 'category', 'start_at', 'end_at']
        widgets = {
            'start_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'step': '1'}),
            'end_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'step': '1'}),
        }


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['auction', 'amount']


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your email',
                'required': True,
            }),
        }
