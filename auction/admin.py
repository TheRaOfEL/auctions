from django.contrib import admin

from .models import AuctionListing, Bid

# Register your models here.

admin.site.register(AuctionListing)
admin.site.register(Bid)
