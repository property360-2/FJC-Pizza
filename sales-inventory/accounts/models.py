from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model with role-based access control.

    Roles:
    - ADMIN: Full system access (products, users, analytics, audit)
    - CASHIER: POS access (orders, payments, view products)
    """

    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CASHIER = "CASHIER", "Cashier"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CASHIER,
        help_text="User role determines access level"
    )

    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == self.Roles.ADMIN

    def is_cashier(self) -> bool:
        """Check if user has cashier role"""
        return self.role == self.Roles.CASHIER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]
