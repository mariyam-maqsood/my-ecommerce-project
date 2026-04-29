from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy

from .forms import SignupForm, LoginForm, UserProfileForm, UserForm
from .models import UserProfile


def signup(request):
    """
    Handle user registration and send email verification.
    """
    # print("Request data",request)
    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken")

            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered")

            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=True,
                )

                # Create associated empty profile
                UserProfile.objects.create(
                    user=user,
                    address="",
                    city="",
                    phone="",
                )

                # send_verification_email(user)

                messages.success(
                    request,
                    "Signup successful!",
                )
                return redirect("login")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})


def send_verification_email(user):
    """
    Send a basic email verification link to the user.
    """
    verification_link = (
        f"http://127.0.0.1:8000"
        f"{reverse('verify_account', args=[user.id])}"
    )

    message = (
        f"Hi {user.username},\n\n"
        f"Please click the link below to verify your account:\n"
        f"{verification_link}\n\n"
        f"Thanks!"
    )

    send_mail(
        subject="Verify your account",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def verify_account(request, user_id):
    """
    Activate user account when verification link is visited.
    """
    try:
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()

        messages.success(
            request,
            "Your account has been verified! You can now login.",
        )
        return redirect("login")

    except User.DoesNotExist:
        messages.error(request, "Invalid verification link.")
        return redirect("signup")


def user_login(request):
    """
    Authenticate and log in the user.
    """
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )

            if user:
                if user.is_active:
                    login(request, user)
                    return redirect("home")

                messages.error(
                    request,
                    "Account not verified. Please check your email.",
                )
            else:
                messages.error(request, "Invalid credentials")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def user_logout(request):
    """Log out the current user."""
    logout(request)
    return redirect("home")


@login_required
def edit_profile(request):
    """
    Allow users to update profile info or change password.
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        password_form = PasswordChangeForm(user, request.POST)

        # Handle profile update form
        if "update_profile" in request.POST:
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()

                messages.success(
                    request,
                    "Profile updated successfully!",
                )
                return redirect("edit_profile")

            messages.error(request, "Please fix the errors below.")

        elif "change_password" in request.POST:
            if password_form.is_valid():
                user = password_form.save()

                # Prevent logout after password change
                update_session_auth_hash(request, user)

                messages.success(
                    request,
                    "Password updated successfully!",
                )
                return redirect("edit_profile")

            messages.error(request, "Please correct the errors below.")

    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
        password_form = PasswordChangeForm(user)

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "password_form": password_form,
    }

    return render(request, "accounts/edit_profile.html", context)


class CustomPasswordResetView(auth_views.PasswordResetView):
    """Handle password reset request."""
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    """Display password reset email sent confirmation."""
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(
    auth_views.PasswordResetConfirmView
):
    """Handle setting a new password."""
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class CustomPasswordResetCompleteView(
    auth_views.PasswordResetCompleteView
):
    """Display password reset completion page."""
    template_name = "accounts/password_reset_complete.html"
