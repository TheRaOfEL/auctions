from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from django.shortcuts import render, redirect, get_object_or_404

from auction.models import AuctionListing, Bid
from .forms import UserRegistrationForm, ProfileForm
from .models import Profile
from django.utils import timezone


# Create your views here.


def login_user(request):
    form = UserRegistrationForm()

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        username = request.POST['username'].lower()
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "Username does not exist")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "User logged in")
            return redirect(request.GET['next'] if 'next' in request.GET else 'dashboard')
        else:
            messages.error(request, "Username or Password is incorrect")

    context = {'form': form}

    return render(request, 'users/login.html', context)


def logout_user(request):
    logout(request)
    messages.info(request, "User was logged out!")
    return redirect('login')


def register_user(request):
    form = UserRegistrationForm()

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            login(request, user)
            return redirect('edit_profile')
        else:
            messages.success(request, 'An error occurred. Please try again!')

    context = {'form': form}
    return render(request, 'users/sign_up.html', context)


@login_required(login_url='login')
def edit_profile(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()

            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    context = {'form': form}
    return render(request, 'users/edit_profile.html', context)


@login_required(login_url='login')
def dashboard(request):
    profiles = Profile.objects.all()
    context = {'profiles': profiles}
    return render(request, 'users/dashboard.html', context)


@login_required(login_url='login')
def profile(request):
    profiles = request.user.profile
    context = {'profiles': profiles}
    return render(request, 'users/user_profile.html', context)


@login_required(login_url='login')
def created_auction(request):
    profile = request.user.profile
    auctions = AuctionListing.objects.filter(owner=profile)

    context = {
        'auctions': auctions
    }
    return render(request, 'users/created_auctions.html', context)


@login_required
def purchases(request):
    profile = request.user.profile

    latest_timestamps = (
        Bid.objects
        .filter(bidder=profile)
        .values('auction')
        .annotate(latest=Max('timestamp'))
        .values_list('latest', flat=True)
    )

    latest_bids = (
        Bid.objects
        .filter(bidder=profile, timestamp__in=latest_timestamps)
        .select_related('auction')
    )

    # Add status per bid
    bids_with_status = []
    for bid in latest_bids:
        auction = bid.auction
        highest_bid = auction.bids.order_by('-amount').first()

        if auction.is_ongoing:
            status = "Ongoing"
        elif auction.sold_to == profile:
            status = "Won"
        else:
            status = "Lost"

        bids_with_status.append({
            'bid': bid,
            'status': status,
        })

    return render(request, 'users/purchase.html', {'bids_with_status': bids_with_status})


def seller_profile(request, pk):
    seller = get_object_or_404(Profile, pk=pk)  # pk is int
    now = timezone.now()
    seller_auctions = AuctionListing.objects.filter(owner=seller)

    current_auctions = seller_auctions.filter(start_at__lte=now, end_at__gte=now)
    upcoming_auctions = seller_auctions.filter(start_at__gt=now)

    context = {
        'seller': seller,
        'current_auctions': current_auctions,
        'upcoming_auctions': upcoming_auctions,
    }
    return render(request, 'users/seller_profile.html', context)
