from .models import UserProfile

def create_user_profile(backend, user, response, *args, **kwargs):
    """Create UserProfile for social auth users if it doesn't exist."""
    UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'address': '',
            'city': '',
            'phone': '',
        }
    )