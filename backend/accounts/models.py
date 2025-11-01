from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model that supports role-based access."""

    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CASHIER = "CASHIER", "Cashier"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CASHIER,
        help_text="Determines which sections of the system the user can access.",
    )

    def is_admin(self) -> bool:
        return self.role == self.Roles.ADMIN

    def is_cashier(self) -> bool:
        return self.role == self.Roles.CASHIER

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"{self.get_full_name() or self.username} ({self.role})"
