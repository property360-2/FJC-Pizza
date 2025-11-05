from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.contrib import messages
from django.urls import reverse_lazy


class UserLoginView(LoginView):
    """
    Custom login view with role-based redirection.

    - ADMIN users redirected to /dashboard/
    - CASHIER users redirected to /pos/
    """
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        """Redirect based on user role"""
        user = self.request.user

        if user.is_admin():
            return reverse_lazy('dashboard:index')
        elif user.is_cashier():
            return reverse_lazy('orders:pos')
        else:
            # Default fallback
            return reverse_lazy('dashboard:index')

    def form_invalid(self, form):
        """Add custom error message"""
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)

    def form_valid(self, form):
        """Add success message"""
        user = form.get_user()
        messages.success(self.request, f"Welcome back, {user.username}!")
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        """Add logout message"""
        if request.user.is_authenticated:
            messages.info(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)


class AccessDeniedView(TemplateView):
    """
    View displayed when user tries to access a page without proper permissions.
    """
    template_name = "accounts/access_denied.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.get_role_display() if self.request.user.is_authenticated else 'Guest'
        return context
