from django.urls import path

from . import views
from .views import security_information

urlpatterns = [
    path('', views.index, name='homepage'),
    path('active_auctions/', views.active_auctions, name='active_auctions'),
    path('auction/<uuid:pk>/', views.auction_detail, name='auction_detail'),
    path('create_auction/', views.create_auction, name='create_auction'),
    path('auction/<uuid:pk>/edit/', views.edit_auction, name='edit_auction'),
    path('auction/<uuid:pk>/delete/', views.delete_auction, name='delete_auction'),
    path('place_bid/<uuid:pk>/', views.place_bid, name='place_bid'),
    path('watchlist/<uuid:auction_id>/toggle/', views.toggle_watchlist, name='toggle_watchlist'),
    path('my_watchlist/', views.my_watchlist, name='my_watchlist'),
    path('upcoming_auctions/', views.upcoming_auctions, name='upcoming_auctions'),
    path('upcoming_auction/<uuid:pk>/', views.upcoming_auction_detail, name='upcoming_auction_detail'),
    path('terms_and_conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('how_it_works/', views.how_it_works, name='how_it_works'),
    path('about_company/', views.about_company, name='about_company'),
    path('our_news_feed/', views.our_news_feed, name='our_news_feed'),
    path('help_center/', views.help_center, name='help_center'),
    path('subscribe/', views.handle_newsletter, name='handle_newsletter'),
    path('customer_faqs/', views.customer_faqs, name='customer_faqs'),
    path('security_information', views.security_information, name='security_information'),
    path('merchant_policy', views.merchant_policy, name='merchant_policy'),
]
