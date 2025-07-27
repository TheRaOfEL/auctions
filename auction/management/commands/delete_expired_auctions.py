from auction.models import AuctionListing
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help =  'Marks expired auctions as completed instead of deleting them.'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired_auctions = AuctionListing.objects.filter(end_at__lt=now, is_ongoing=True)

        count = 0

        for auction in expired_auctions:
            highest_bid = auction.bids.order_by('-amount').first()

            if highest_bid:
                auction.sold_to = highest_bid.bidder  # ✅ Assign winner

            auction.completed = True
            auction.is_ongoing = False
            auction.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Marked {count} auctions as completed and assigned winners (if any)."))
