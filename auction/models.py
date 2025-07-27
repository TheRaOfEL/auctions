import uuid

from django.db import models
from django.utils import timezone

from user.models import Profile


# Create your models here.

class AuctionListing(models.Model):
    owner = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500, null=True, blank=True)
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)  # starting price
    image = models.ImageField(blank=False, null=True, default='images/default_background.jpg', upload_to='images/')
    category = models.CharField(max_length=100, null=True, blank=True)  # electronics etc
    created_at = models.DateTimeField(auto_now_add=True)
    start_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    end_at = models.DateTimeField(null=True, blank=True)  # optional
    completed = models.BooleanField(default=False)  # To mark if auction is completed
    is_ongoing = models.BooleanField(default=True)
    sold_to = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    watchers = models.ManyToManyField(Profile, related_name='watchlist', blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def is_active(self):
        now = timezone.now()
        return (self.start_at is None or self.start_at <= now) and \
            (self.end_at is None or now <= self.end_at)

    def is_auction_completed(self):
        return self.completed or (timezone.now() > self.end_at)

    def is_upcoming(self):
        return self.start_at and self.start_at > timezone.now()

    def __str__(self):
        return self.name


class Bid(models.Model):
    auction = models.ForeignKey("AuctionListing", on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(Profile, on_delete=models.CASCADE)  # User who placed the bid
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def highest_bid(self):
        return Bid.objects.filter(auction=self.auction).order_by('-amount').first()

    def __str__(self):
        return f"{self.bidder.user.username} - ${self.amount}"
