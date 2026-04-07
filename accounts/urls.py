from django.urls import path

from . import views

urlpatterns = [
    # Authentication
    path("signup/", views.signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),

    # SSO
    # path('accounts/', include('allauth.urls')),
    # path('auth/', include('social_django.urls', namespace='social')),

    # Profile
    path("edit-profile/", views.edit_profile, name="edit_profile"),

    # Email verification
    path(
        "verify/<int:user_id>/",
        views.verify_account,
        name="verify_account",
    ),

    # Password reset
    path(
        "password-reset/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        views.CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
