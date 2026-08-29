from django.shortcuts import get_object_or_404
from django.shortcuts import render

from apps.accounts.models import User


def home(request):
    return render(request, "core/home.html")


def register(request):
    return render(request, "core/register.html")


def profile(request):
    return render(request, "core/profile.html")


def feed(request):
    return render(request, "core/feed.html")

def people(request):
    return render(request, "core/people.html")

def public_profile(request, user_id):
    return render(
        request,
        "core/public_profile.html",
        {
            "user_id": user_id,
        },
    )

def chat(request):
    return render(
        request,
        "core/chat.html",
    )

def public_user_profile(request, user_id):
    user = get_object_or_404(
        User,
        id=user_id,
        is_active=True,
    )

    return render(
        request,
        "core/user_profile.html",
        {
            "profile_user": user,
        },
    )

def notifications(request):
    return render(
        request,
        "core/notifications.html",
    )

def settings_page(request):
    return render(
        request,
        "core/settings.html",
    )