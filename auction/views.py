from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from user.models import Profile
from .forms import BidForm, AuctionForm
from .models import AuctionListing, Bid


# Create your views here.

def index(request):
    now = timezone.now()
    active_auctions = AuctionListing.objects.filter(start_at__lte=now, end_at__gte=now)
    coming_soon = (AuctionListing.objects.filter(start_at__gt=now).order_by('start_at'))

    context = {
        'active_auctions': active_auctions,
        'coming_soon': coming_soon,
    }

    return render(request, 'homepage.html', context)


@login_required(login_url='login')
def upcoming_auctions(request):
    upcoming_auctions = AuctionListing.objects.filter(start_at__gt=timezone.now()).order_by('start_at')
    for auction in upcoming_auctions:
        # Use timezone.now() to get the current time in the correct timezone
        time_left = auction.start_at - timezone.now()
        if time_left > timedelta(0):  # If auction start date is in the future
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds // 60) % 60
            auction.time_left_display = f"{days} days {hours} hours {minutes} minutes"
        else:
            auction.time_left_display = "The auction is live now!"

    return render(request, 'auction/upcoming_auctions.html', {
        'upcoming_auctions': upcoming_auctions
    })


def upcoming_auction_detail(request, pk):
    auction = get_object_or_404(AuctionListing, id=pk)

    # Calculate time left
    time_left = auction.start_at - timezone.now()

    # Prepare the time components
    if time_left > timedelta(0):  # Auction is not yet live
        days = time_left.days
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds // 60) % 60
    else:
        days, hours, minutes = 0, 0, 0

    context = {
        'auction': auction,
        'time_left_days': days,
        'time_left_hours': hours,
        'time_left_minutes': minutes,
    }

    return render(request, 'auction/upcoming_auction_details.html', context)


@login_required(login_url='login')
def active_auctions(request):
    # Get the current time
    now = timezone.now()

    # Fetch active auctions (auction where the end date is greater than now)
    active_auctions = AuctionListing.objects.filter(start_at__lte=now,end_at__gte=now)

    # Calculate the time left for each auction
    for auction in active_auctions:
        time_left = auction.end_at - now
        auction.time_left = time_left  # Add the timedelta to the auction object
        auction.hours_left = time_left.seconds // 3600  # Calculate hours
        auction.minutes_left = (time_left.seconds // 60) % 60  # Calculate minutes

    # Context to pass to the template
    context = {
        'auctions': active_auctions,
        'now': now,
    }

    return render(request, 'auction/all_auction.html', context)


@login_required(login_url='login')
def auction_detail(request, pk):
    auction = AuctionListing.objects.get(id=pk)

    # Check if auction has ended and mark it as completed
    if auction.end_at <= timezone.now() and not auction.completed:
        highest_bid = auction.bids.order_by('-amount').first()
        if highest_bid:
            auction.completed = True
            auction.is_ongoing = False
            # Assign the auction to the highest bidder
            auction.sold_to = highest_bid.bidder
            auction.save()  # Save auction with the buyer info
            print(f"Auction completed: {auction.name} sold to {highest_bid.bidder.user.username}.")

    highest_bid = auction.bids.order_by('-amount').first()

    if request.method == 'POST':
        form = BidForm(request.POST, request.FILES)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.auction = auction  # Assign the auction to the bid
            bid.save()  # Save the bid, not the auction
            return redirect('auction_detail', pk=pk)
        else:
            print(form.errors)  # Print errors to debug
    else:
        form = BidForm()

        # Calculate time left for the auction
    if auction.start_at > timezone.now():  # Upcoming Auction
        time_left = auction.start_at - timezone.now()
        auction_status = "upcoming"
    elif auction.end_at > timezone.now():  # Live Auction
        time_left = auction.end_at - timezone.now()
        auction_status = "live"
    else:  # Auction has ended
        time_left = timedelta(0)
        auction_status = "ended"

        # Prepare the time components
    days = time_left.days
    hours = time_left.seconds // 3600
    minutes = (time_left.seconds // 60) % 60

    context = {
        'auction': auction,
        'time_left_days': days,
        'time_left_hours': hours,
        'time_left_minutes': minutes,
        'auction_status': auction_status,
        'highest_bid': highest_bid,
        'form': form,
    }

    return render(request, 'auction/auction_detail.html', context)


@login_required(login_url='login')
def create_auction(request):
    if request.method == "POST":
        form = AuctionForm(request.POST, request.FILES)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.owner = request.user.profile  # assign the owner
            auction.save()
            if auction is upcoming_auctions:
                return redirect('upcoming_auctions_detail', pk=auction.id)
            else:
                return redirect("auction_detail", auction.pk)  # Redirect to the auction details page
    else:
        form = AuctionForm()
    return render(request, "auction/auction_form.html", {"form": form})


@login_required(login_url='login')
def place_bid(request, pk):
    auction = get_object_or_404(AuctionListing, id=pk)
    highest_bid = auction.bids.order_by('-amount').first()

    if auction.owner == request.user.profile:
        messages.error(request, "You can't bid on your own auction.")
        return redirect('auction_detail', pk=auction.id)

    # Check if the auction has ended
    if not auction.is_ongoing:
        messages.error(request, "This auction has ended and no further bids can be placed.")
        return redirect('auction_detail', pk=auction.id)

    if request.method == 'POST':
        bid_amount = request.POST.get('amount')

        if not bid_amount:
            messages.error(request, "Bid amount is required.")
            return redirect('auction_detail', pk=auction.id)

        try:
            bid_amount = float(bid_amount)
        except ValueError:
            messages.error(request, "Invalid bid amount.")
            return redirect('auction_detail', pk=auction.id)

        # Validate the bid amount
        min_valid_bid = highest_bid.amount if highest_bid else auction.starting_bid
        if bid_amount < min_valid_bid:
            messages.error(request, f"Your bid must be at least ${min_valid_bid}.")
            return redirect('auction_detail', pk=auction.id)

        # Save new bid
        Bid.objects.create(
            auction=auction,
            bidder=request.user.profile,
            amount=bid_amount
        )

        messages.success(request, "Your bid was placed successfully.")
        return redirect('auction_detail', pk=auction.id)

    # For GET requests, show the form
    context = {
        'auction': auction,
        'highest_bid': highest_bid
    }
    return render(request, 'auction/create_bid.html', context)


@login_required(login_url='login')
def toggle_watchlist(request, auction_id):
    auction = get_object_or_404(AuctionListing, id=auction_id)
    if request.user.profile in auction.watchers.all():
        auction.watchers.remove(request.user.profile)
        messages.success(request, "Removed from your watchlist.")
    else:
        auction.watchers.add(request.user.profile)
        messages.success(request, "Added to your watchlist.")
    return redirect('auction_detail', pk=auction_id)


@login_required(login_url='login')
def my_watchlist(request):
    profile = Profile.objects.get(user=request.user)
    watchlist_items = AuctionListing.objects.filter(watchers=profile)
    return render(request, 'auction/watchlist.html', {'watchlist': watchlist_items})
