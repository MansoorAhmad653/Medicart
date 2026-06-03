from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from .forms import SignUpForm, LoginForm, ProfileUpdateForm
from .models import CustomUser
from shop.cart_utils import merge_session_cart_to_db


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('shop:home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            merge_session_cart_to_db(request)
            messages.success(request, f'Welcome to MediCart, {user.name or user.email}!')
            return redirect('shop:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('shop:home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            merge_session_cart_to_db(request)
            messages.success(request, f'Welcome back, {user.name or user.email}!')
            next_url = request.GET.get('next', 'shop:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    # Render a page that clears Supabase session from browser
    return render(request, 'users/logout.html')


@require_http_methods(["GET", "POST"])
def auth_callback(request):
    """Handle Supabase OAuth callback - works with POST data from frontend"""
    try:
        if request.method == 'POST':
            # Frontend sends the email after Supabase auth
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({'error': 'No email received'}, status=400)
        else:
            # GET method - try to extract from query params
            email = request.GET.get('email')
            error = request.GET.get('error')
            
            if error:
                messages.error(request, f'Authentication failed: {error}')
                return redirect('users:login')
            
            if not email:
                messages.error(request, 'Authentication failed: No email received.')
                return redirect('users:login')
        
        # Get or create Django user
        try:
            user = CustomUser.objects.get(email=email)
            is_new = False
        except CustomUser.DoesNotExist:
            # Create new user from Google account
            username = email.split('@')[0]
            # Ensure unique username
            counter = 1
            original_username = username
            while CustomUser.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            user = CustomUser.objects.create(
                email=email,
                username=username,
                is_active=True,
                is_email_verified=True
            )
            is_new = True
        
        # Log in user directly (both new and existing)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        merge_session_cart_to_db(request)
        
        if request.method == 'POST':
            return JsonResponse({
                'success': True,
                'message': 'Logged in successfully',
                'redirect': '/shop/'
            })
        
        messages.success(request, f'Welcome back, {user.name or user.email}!')
        return redirect('shop:home')
        
    except Exception as e:
        print(f"Auth callback error: {e}")
        import traceback
        traceback.print_exc()
        if request.method == 'POST':
            return JsonResponse({'error': str(e)}, status=500)
        messages.error(request, 'An error occurred during authentication.')
        return redirect('users:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'users/profile.html', {'form': form})
