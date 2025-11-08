from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_archived:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')

                # Redirect based on role
                if user.is_admin:
                    return redirect('admin_dashboard')
                elif user.is_cashier:
                    return redirect('cashier_pos')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Your account has been archived. Please contact an administrator.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')
