import uuid

from django.db import models
from django.utils import timezone
from datetime import timedelta
from user.models import Profile


# Create your models here.

# Define a named function
def default_auction_end_time():
    return timezone.now() + timedelta(days=7)

class AuctionListing(models.Model):
    CATEGORY_CHOICES = [
        ('AR', 'Art'),
        ('AU', 'Automotive'),
        ('BK', 'Books'),
        ('CL', 'Collectibles'),
        ('EL', 'Electronics'),
        ('FA', 'Fashion'),
        ('FT', 'Food & Drink'),
        ('HE', 'Health & Beauty'),
        ('HM', 'Home & Garden'),
        ('IN', 'Industrial Equipment'),
        ('JL', 'Jewelry'),
        ('MU', 'Music Instruments'),
        ('OF', 'Office Supplies'),
        ('PE', 'Pet Supplies'),
        ('RE', 'Real Estate'),
        ('SE', 'Services'),
        ('SP', 'Sports'),
        ('TG', 'Toys & Games'),
        ('TR', 'Travel'),
        ('OT', 'Other'),
    ]


    owner = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=False, null=True)
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)  # starting price
    image = models.ImageField(blank=False, null=True, upload_to='auction_images/')
    category = models.CharField(max_length=100, null=True, blank=False, choices=CATEGORY_CHOICES, default='OT')  # electronics etc
    created_at = models.DateTimeField(auto_now_add=True)
    start_at = models.DateTimeField(null=False, blank=False, default=timezone.now)
    end_at = models.DateTimeField(
        null=False,
        blank=False,
        default=default_auction_end_time
    )
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



class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email