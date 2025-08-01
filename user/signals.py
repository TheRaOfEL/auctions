from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete

from .models import Profile
from django.core.mail import send_mail
from django.conf import settings

def create_profile(sender, instance, created, **kwargs):
    if created:
        user = instance
        Profile.objects.create(user=user,
                               username=user.username,
                               email=user.email,
                               name=user.first_name,
                               )

        subject = "Welcome to Sieg's Auction site"
        message = "Enjoy the Ultimate Bidding SPREEE!!!!"

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )


def update_user(sender, instance, created, **kwargs):
    profile = instance
    user = profile.user

    if created == False:
        user.first_name = profile.name
        user.username = profile.username
        user.email = profile.email
        user.save()


def delete_user(sender, instance, **kwargs):
    user = instance.user
    user.delete()


post_save.connect(create_profile, sender=User)
post_save.connect(update_user, sender=Profile)
post_delete.connect(delete_user, sender=Profile)
