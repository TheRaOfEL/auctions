from django import forms


from .models import Bid, AuctionListing


class AuctionForm(forms.ModelForm):
    class Meta:
        model = AuctionListing
        fields = ['name', 'description', 'starting_bid', 'image', 'category', 'start_at', 'end_at']
        widgets = {
            'start_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['auction', 'amount']
