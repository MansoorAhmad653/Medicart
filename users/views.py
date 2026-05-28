from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from .forms import SignUpForm, LoginForm, ProfileUpdateForm
from .supabase_auth import supabase


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('shop:home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to MediCart, {user.name}! Your account has been created.')
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
            messages.success(request, f'Welcome back, {user.name or user.email}!')
            next_url = request.GET.get('next', 'shop:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


def otp_login_view(request):
    """OTP-based login page"""
    if request.user.is_authenticated:
        return redirect('shop:home')
    return render(request, 'users/otp_login.html')


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
        from .models import CustomUser
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
                is_active=True
            )
            is_new = True
        
        # Login the user
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        if is_new:
            if request.method == 'POST':
                return JsonResponse({'success': True, 'message': 'Account created successfully'})
            messages.success(request, f'Welcome to MediCart! Your account has been created.')
        else:
            if request.method == 'POST':
                return JsonResponse({'success': True, 'message': 'Logged in successfully'})
            messages.success(request, f'Welcome back, {user.name or user.email}!')
        
        if request.method == 'GET':
            return redirect('shop:home')
        return JsonResponse({'success': True})
        
    except Exception as e:
        print(f"Auth callback error: {e}")
        import traceback
        traceback.print_exc()
        if request.method == 'POST':
            return JsonResponse({'error': str(e)}, status=500)
        messages.error(request, 'An error occurred during authentication.')
        return redirect('users:login')


@require_http_methods(["POST"])
def send_otp_view(request):
    """Send OTP to email or phone number"""
    try:
        data = json.loads(request.body)
        contact = data.get('contact')  # email or phone
        contact_type = data.get('type')  # 'email' or 'phone'
        
        if not contact or not contact_type:
            return JsonResponse({'error': 'Missing contact or type'}, status=400)
        
        if contact_type == 'email':
            # Send email OTP via Supabase
            response = supabase.auth.sign_in_with_otp({
                'email': contact,
                'options': {
                    'email_redirect_to': f"{request.build_absolute_uri('/users/verify-otp/')}"
                }
            })
            return JsonResponse({
                'success': True,
                'message': f'OTP sent to {contact}. Check your email.',
                'session_id': response.session.id if response.session else None
            })
        
        elif contact_type == 'phone':
            # Send phone OTP via Supabase
            response = supabase.auth.sign_in_with_otp({
                'phone': contact,
            })
            return JsonResponse({
                'success': True,
                'message': f'OTP sent to {contact}. Check your SMS.',
                'session_id': response.session.id if response.session else None
            })
        
        else:
            return JsonResponse({'error': 'Invalid contact type'}, status=400)
    
    except Exception as e:
        print(f"OTP send error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def verify_otp_view(request):
    """Verify OTP and create/login user"""
    try:
        data = json.loads(request.body)
        contact = data.get('contact')  # email or phone
        otp = data.get('otp')
        contact_type = data.get('type')  # 'email' or 'phone'
        
        if not contact or not otp or not contact_type:
            return JsonResponse({'error': 'Missing contact, OTP, or type'}, status=400)
        
        # Verify OTP with Supabase
        try:
            response = supabase.auth.verify_otp({
                'email' if contact_type == 'email' else 'phone': contact,
                'token': otp,
                'type': 'sms' if contact_type == 'phone' else 'email'
            })
            
            if not response.user:
                return JsonResponse({'error': 'Invalid OTP'}, status=400)
            
            # Get user email or phone
            user_email = response.user.email or (contact if contact_type == 'email' else None)
            user_phone = response.user.phone or (contact if contact_type == 'phone' else None)
            
            # Create/get Django user
            from .models import CustomUser
            
            # Try to find user by email first, then by phone
            user = None
            if user_email:
                user = CustomUser.objects.filter(email=user_email).first()
            elif user_phone:
                user = CustomUser.objects.filter(phone=user_phone).first()
            
            is_new = False
            if not user:
                # Create new user
                username = user_email.split('@')[0] if user_email else f"user_{user_phone}"
                
                # Ensure unique username
                counter = 1
                original_username = username
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = CustomUser.objects.create(
                    email=user_email or '',
                    phone=user_phone or '',
                    username=username,
                    is_active=True
                )
                is_new = True
            
            # Login the user
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            return JsonResponse({
                'success': True,
                'message': 'Account created and logged in!' if is_new else 'Logged in successfully!',
                'redirect': '/shop/'
            })
        
        except Exception as otp_error:
            print(f"OTP verification error: {otp_error}")
            return JsonResponse({'error': 'Invalid OTP or expired'}, status=400)
    
    except Exception as e:
        print(f"OTP verify error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


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
