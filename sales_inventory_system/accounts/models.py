# ==============================================================================
# FJC-PIZZA SALES & INVENTORY MANAGEMENT SYSTEM
# File: accounts/models.py
# Purpose: Defines the custom User model for authentication and security authorization.
# Contains:
#   - User model class: Extends AbstractUser to integrate role-based attributes.
# How it fits: Acts as the primary database entity representing system users, cashiers,
# and administrators, driving authentication verification, archiving status checks,
# and permission levels across all modules.
# ==============================================================================

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom extended User entity implementing Role-Based Access Control (RBAC).
    Includes flags and metadata fields tracking registration timestamp, archive toggles,
    and role classifications.
    """

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('CASHIER', 'Cashier'),
    ]

    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='CASHIER',
        help_text="Security authorization role designated to the staff member."
    )
    phone = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Primary contact details of the staff member."
    )
    is_archived = models.BooleanField(
        default=False,
        help_text="Flag indicating if the user account is soft-deleted or deactivated."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp indicating when the staff account was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp indicating when the staff account was last modified."
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        """
        Return string representation displaying user credentials and role.
        
        Returns:
            str: Username combined with formatted display role.
        """
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        """
        Check if the staff member holds Admin role permissions.
        
        Returns:
            bool: True if user role is ADMIN, otherwise False.
        """
        return self.role == 'ADMIN'

    @property
    def is_cashier(self):
        """
        Check if the staff member holds Cashier role permissions.
        
        Returns:
            bool: True if user role is CASHIER, otherwise False.
        """
        return self.role == 'CASHIER'
