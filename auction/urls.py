from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='homepage'),
    path('active_auctions/', views.active_auctions, name='active_auctions'),
    path('auction/<uuid:pk>/', views.auction_detail, name='auction_detail'),
    path('create_auction/', views.create_auction, name='create_auction'),
    path('place_bid/<uuid:pk>/', views.place_bid, name='place_bid'),
    path('watchlist/<uuid:auction_id>/toggle/', views.toggle_watchlist, name='toggle_watchlist'),
    path('my_watchlist/', views.my_watchlist, name='my_watchlist'),
    path('upcoming_auctions/', views.upcoming_auctions, name='upcoming_auctions'),
    path('upcoming_auction/<uuid:pk>/', views.upcoming_auction_detail, name='upcoming_auction_detail'),
]
