# ==============================================================================
# FJC-PIZZA SALES & INVENTORY MANAGEMENT SYSTEM
# File: accounts/views.py
# Purpose: Handles authentication, session management, and staff (User) administration.
# Contains:
#   - Authentication Views: login_view, logout_view
#   - Staff Administration Views: user_list, user_create, user_edit, user_archive, user_unarchive
#   - Security & Logging: is_admin, user_audit_trail
# How it fits: This file serves as the gatekeeper for user authentication and role-based
# access controls, providing secure views for staff registration, updates, audits, and
# status toggle operations, feeding logs into the central system's AuditTrail.
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User
from sales_inventory_system.system.models import AuditTrail

def login_view(request):
    """
    Handle user login and session establishment.
    
    Accepts:
        request (HttpRequest): Contains POST parameters 'username' and 'password'.
        
    Returns/Renders:
        HttpResponse: Renders 'accounts/login.html' template or redirects to the
        appropriate dashboard based on user role (Admin -> admin_dashboard,
        Cashier -> cashier_pos, other -> home).
    """
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
    """
    Handle user logout and clear current session.
    
    Accepts:
        request (HttpRequest): Current active user request session.
        
    Returns/Renders:
        HttpResponseRedirect: Redirects back to the login page.
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


def is_admin(user):
    """
    Check if the authenticated user has Admin permissions.
    
    Accepts:
        user (User): The user model instance to validate.
        
    Returns:
        bool: True if user is authenticated and possesses the ADMIN role, False otherwise.
    """
    return user.is_authenticated and user.is_admin


@login_required
@user_passes_test(is_admin)
def user_list(request):
    """
    List all system users with search, role filters, and pagination.
    Supports asynchronous AJAX filtering requests for enhanced UI responsiveness.
    
    Accepts:
        request (HttpRequest): Contains GET parameters:
            - 'role': Filtering criterion for roles (e.g. 'ADMIN', 'CASHIER').
            - 'search': Search query matched against name/username/email.
            - 'page': Active page number for pagination.
            
    Returns/Renders:
        HttpResponse/JsonResponse: Renders 'accounts/user_list.html' or returns a 
        JSON payload containing filtered paginated users if requested via AJAX.
    """
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('search', '')

    # Base query - exclude superuser
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')

    # Apply role filter
    if role_filter and role_filter != 'all':
        users = users.filter(role=role_filter)

    # Apply search filter (search in username and email)
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(users, 20)  # 20 users per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get available roles
    roles = User.objects.values_list('role', flat=True).distinct().order_by('role')

    # Handle AJAX requests for async filtering
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Prepare users data for JSON response
        users_data = []
        for user in page_obj:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.get_role_display(),
                'role_code': user.role,
                'is_archived': user.is_archived,
                'phone': user.phone or 'N/A',
                'date_joined': user.date_joined.isoformat()
            })

        return JsonResponse({
            'success': True,
            'filters': {
                'role': role_filter,
                'search': search_query
            },
            'pagination': {
                'page': page_obj.number,
                'total_pages': paginator.num_pages,
                'per_page': 20,
                'total_count': paginator.count,
                'start_index': page_obj.start_index() if page_obj else 0,
                'end_index': page_obj.end_index() if page_obj else 0,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
            },
            'users': users_data,
            'available_roles': list(roles)
        })

    # Regular page load
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'role_filter': role_filter,
        'search_query': search_query,
        'roles': roles,
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """
    Create a new system user with staff role permissions (admin only).
    
    Accepts:
        request (HttpRequest): Contains POST parameter details including username,
        email, passwords, role, first name, last name, and phone.
        
    Returns/Renders:
        HttpResponse: Renders the user form ('accounts/user_form.html') or redirects
        to 'accounts:user_list' upon successful user registration.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        role = request.POST.get('role', 'CASHIER')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Validation
        if not username or not password:
            messages.error(request, 'Username and password are required.')
        elif password != password_confirm:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role
            )
            messages.success(request, f'User {username} created successfully!')
            return redirect('accounts:user_list')

    # Explicitly pass user=None so the template does not use request.user defaults
    return render(request, 'accounts/user_form.html', {'action': 'Create', 'user': None})


@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    """
    Edit profile details and roles for an existing staff member (admin only).
    
    Accepts:
        request (HttpRequest): Contains POST updates for profile data and passwords.
        pk (int): Primary key of the staff user to edit.
        
    Returns/Renders:
        HttpResponse: Renders filled 'accounts/user_form.html' or redirects to
        'accounts:user_list' upon successful profile saving.
    """
    user = get_object_or_404(User, pk=pk)

    # Prevent editing superuser
    if user.is_superuser:
        messages.error(request, 'Cannot edit superuser account.')
        return redirect('accounts:user_list')

    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.role = request.POST.get('role', user.role)

        # Update password if provided
        password = request.POST.get('password')
        if password:
            password_confirm = request.POST.get('password_confirm')
            if password == password_confirm:
                user.set_password(password)
            else:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/user_form.html', {'user': user, 'action': 'Edit'})

        user.save()
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_form.html', {'user': user, 'action': 'Edit'})


@login_required
@user_passes_test(is_admin)
def user_archive(request, pk):
    """
    Archive a staff user to block login access, creating an audit log (admin only).
    
    Accepts:
        request (HttpRequest): Active session context.
        pk (int): Primary key of the staff user to archive.
        
    Returns/Renders:
        HttpResponseRedirect: Redirects back to the staff user list page.
    """
    user = get_object_or_404(User, pk=pk)

    # Prevent archiving superuser
    if user.is_superuser:
        messages.error(request, 'Cannot archive superuser account.')
        return redirect('accounts:user_list')

    # Prevent archiving yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot archive yourself!')
        return redirect('accounts:user_list')

    user.is_archived = True
    user.save()

    # Create audit log
    AuditTrail.objects.create(
        user=request.user,
        action='ARCHIVE',
        model_name='User',
        record_id=user.id,
        description=f'Archived user: {user.username}',
        data_snapshot={'username': user.username, 'email': user.email, 'role': user.get_role_display()}
    )

    messages.success(request, f'User "{user.username}" archived successfully!')
    return redirect('accounts:user_list')


@login_required
@user_passes_test(is_admin)
def user_unarchive(request, pk):
    """
    Restore an archived staff user, restoring login capabilities and creating an audit log (admin only).
    
    Accepts:
        request (HttpRequest): Active session context.
        pk (int): Primary key of the archived staff user to restore.
        
    Returns/Renders:
        HttpResponseRedirect: Redirects back to the staff user list page.
    """
    user = get_object_or_404(User, pk=pk, is_archived=True)

    user.is_archived = False
    user.save()

    # Create audit log
    AuditTrail.objects.create(
        user=request.user,
        action='RESTORE',
        model_name='User',
        record_id=user.id,
        description=f'Restored user: {user.username}',
        data_snapshot={'username': user.username, 'email': user.email, 'role': user.get_role_display()}
    )

    messages.success(request, f'User "{user.username}" restored successfully!')
    return redirect('accounts:user_list')


@login_required
@user_passes_test(is_admin)
def user_audit_trail(request, pk):
    """
    View paginated history logs (AuditTrail) for a specific user (admin only).
    
    Accepts:
        request (HttpRequest): Standard paginated request.
        pk (int): Primary key of the user whose logs are fetched.
        
    Returns/Renders:
        HttpResponse: Renders 'accounts/user_audit_trail.html' showing log list.
    """
    user = get_object_or_404(User, pk=pk)

    # Get audit logs for this user
    audit_logs = AuditTrail.objects.filter(user=user).select_related('user').order_by('-created_at')

    # Pagination
    paginator = Paginator(audit_logs, 50)  # 50 logs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'user': user,
        'audit_logs': page_obj,
        'total_actions': paginator.count,
    }
    return render(request, 'accounts/user_audit_trail.html', context)

