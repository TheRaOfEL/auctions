from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from user.models import Profile
from .forms import BidForm, AuctionForm, NewsletterForm
from .models import AuctionListing, Bid, NewsletterSubscriber
from django.core.mail import send_mail



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

@login_required(login_url='login')
def upcoming_auction_detail(request, pk):
    auction = get_object_or_404(AuctionListing, id=pk)

    # Time left until auction starts
    time_left = auction.start_at - timezone.now()
    if time_left > timedelta(0):
        days = time_left.days
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds // 60) % 60
    else:
        days, hours, minutes = 0, 0, 0

    # Ownership and bid checks
    is_owner = auction.owner == request.user.profile  # or request.user if no profile model
    has_bids = auction.bids.exists()  # Assumes related_name='bids' in your Bid model
    is_upcoming = timezone.now() < auction.start_at

    context = {
        'auction': auction,
        'time_left_days': days,
        'time_left_hours': hours,
        'time_left_minutes': minutes,
        'is_owner': is_owner,
        'has_bids': has_bids,
        'is_upcoming': is_upcoming,
    }

    return render(request, 'auction/upcoming_auction_details.html', context)


@login_required(login_url='login')
def active_auctions(request):
    # Get the current time
    now = timezone.now()

    # Fetch active auctions (auction where the end date is greater than now)
    active_auctions = AuctionListing.objects.filter(start_at__lte=now, end_at__gte=now)

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

    # Determine if current user is watching this auction
    is_watching = request.user.profile in auction.watchers.all()

    # Check if auction has ended and mark it as completed
    if auction.end_at is not None and auction.end_at <= timezone.now() and not auction.completed:
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
        'is_watching': is_watching,
        'form': form,
    }

    return render(request, 'auction/auction_detail.html', context)


@login_required(login_url='login')
def create_auction(request):
    if request.method == "POST":
        form = AuctionForm(request.POST, request.FILES)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.owner = request.user.profile

            # Handle custom category
            selected_category = form.cleaned_data['category']
            custom_category = request.POST.get('custom_category', '').strip()
            if selected_category == 'OT' and custom_category:
                auction.category = custom_category

            auction.save()

            # Redirect based on whether auction is upcoming
            if auction.start_at and auction.start_at > timezone.now():
                return redirect('upcoming_auction_detail', pk=auction.id)
            else:
                return redirect('auction_detail', auction.pk)
    else:
        form = AuctionForm()

    return render(request, "auction/auction_form.html", {"form": form})


@login_required(login_url='login')
def edit_auction(request, pk):
    auction = get_object_or_404(AuctionListing, pk=pk, owner=request.user.profile)

    if auction.bids.exists():
        messages.error(request, "You can't edit this auction because a bid has already been placed.")
        return redirect('auction_detail', pk=pk)

    form = AuctionForm(request.POST or None, request.FILES or None, instance=auction)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Auction updated successfully.")
        # Redirect based on whether auction is upcoming
        if auction.start_at and auction.start_at > timezone.now():
            return redirect('upcoming_auction_detail', pk=auction.id)
        else:
            return redirect('auction_detail', auction.pk)

    return render(request, 'auction/edit_auction.html', {'form': form, 'auction': auction})


login_required(login_url='login')
def delete_auction(request, pk):
    auction = get_object_or_404(AuctionListing, pk=pk, owner=request.user.profile)

    if auction.bids.exists():
        messages.error(request, "You can't delete this auction because a bid has already been placed.")
        return redirect('auction_detail', pk=pk)

    if request.method == "POST":
        auction.delete()
        messages.success(request, "Auction deleted successfully!")
        return redirect('homepage')

    return render(request, 'auction/delete_auction.html', {'auction': auction})


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
            return redirect('place_bid', pk=auction.id)

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
    if request.method == 'POST':
        auction = get_object_or_404(AuctionListing, id=auction_id)
        user_profile = request.user.profile  # Assuming you have a Profile model

        if user_profile in auction.watchers.all():
            auction.watchers.remove(user_profile)
            return JsonResponse({
                'success': True,
                'in_watchlist': False,
                'message': "Removed from your watchlist."
            })
        else:
            auction.watchers.add(user_profile)
            return JsonResponse({
                'success': True,
                'in_watchlist': True,
                'message': "Added to your watchlist."
            })

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def my_watchlist(request):
    profile = Profile.objects.get(user=request.user)
    watchlist_items = AuctionListing.objects.filter(watchers=profile)
    return render(request, 'auction/watchlist.html', {'watchlist': watchlist_items})


def handle_newsletter(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if not NewsletterSubscriber.objects.filter(email=email).exists():
                form.save()
                messages.success(request, "Subscribed to newsletter successfully!")

                # Auto-send welcome email
                send_mail(
                    subject='Welcome to Siegs Auction Newsletter!',
                    message='Thank you for subscribing to our newsletter. Stay tuned for exclusive auction updates and deals!',
                    from_email=None,  # Uses DEFAULT_FROM_EMAIL
                    recipient_list=[email],
                    fail_silently=False,
                )
            else:
                messages.info(request, "You're already subscribed.")
        else:
            messages.error(request, "Invalid email address.")
    return redirect(request.META.get('HTTP_REFERER', '/'))

def terms_and_conditions(request):
    return render(request, 'terms_and_condition.html')


def how_it_works(request):
    return render(request, 'how_it_works.html')


def about_company(request):
    return render(request, 'about_company.html')


def our_news_feed(request):
    return render(request, 'our_news_feed.html')

def customer_faqs(request):
    customer_faqs = [
        ("How do I create an account?", "Click on 'Sign Up' at the top-right corner and fill in your details."),
        ("Is it free to list an item?",
         "Yes, listing items is free. We charge only a small fee upon successful auction."),
        ("How do I place a bid?", "Once an auction is live, you can place bids from the item’s detail page."),
        ("What happens if I win?", "You’ll receive an email with payment and delivery instructions."),
        ("Can I cancel my bid?", "No, all bids are final. Please bid responsibly."),
        ("How can I edit or delete my auction?",
         "You can edit or delete your auction before any bids are placed from your dashboard."),
        ("What types of items can I list?", "You can list anything legal that complies with our listing guidelines."),
        ("How do I upload photos of my item?", "During listing, use the image upload section to add clear photos."),
        ("When will my auction start?", "You can set the start time when creating your auction."),
        ("How long can my auction run?", "You can choose a duration between 1 hour and 30 days."),
        ("How do I receive payment after an auction?",
         "Buyers are instructed to pay you directly through your preferred payment method."),
        ("Can I relist unsold items?", "Yes, items that don’t sell can be relisted for free."),
        ("How do I report a fraudulent buyer?",
         "Go to the buyer’s profile and click 'Report User' or contact support."),
        ("Is my personal information safe?", "Yes, we use secure encryption to protect your data."),
        ("Can I view upcoming auctions?", "Yes, the ‘Upcoming Auctions’ page lists all scheduled items."),
        ("Do you have a mobile app?", "We’re working on one! For now, the website is mobile-optimized."),
        ("How do I change my password?", "Go to Account Settings > Security to update your password."),
        ("What happens if I miss a bidding deadline?",
         "Unfortunately, late bids are not accepted. Set reminders to avoid missing deadlines."),
        ("How do I unsubscribe from newsletters?", "Click the unsubscribe link in any newsletter email."),
        ("Can I contact the seller before bidding?", "Yes, use the ‘Contact Seller’ button on the listing page."),
    ]
    return render(request, 'customer_faqs.html', {'customer_faqs': customer_faqs})

def help_center(request):
    return render(request, 'help_center.html')

def security_information(request):
    return render(request, 'security_information.html')

def merchant_policy(request):
    return render(request, 'merchant_policy.html')
