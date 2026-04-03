from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """
    Extended profile information linked to the default User model.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    address = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )
    city = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    def __str__(self):
        """Return the username associated with the profile."""
        return self.user.username
