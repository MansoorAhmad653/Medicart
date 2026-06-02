from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
import os
from .forms import SignUpForm, LoginForm, ProfileUpdateForm
from .supabase_auth import supabase
from .models import CustomUser
from .otp_service import generate_otp, send_otp_email, store_otp_in_session, verify_otp_from_session
from shop.cart_utils import merge_session_cart_to_db


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('shop:home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Store the registration data in the session instead of the database
            signup_data = {
                'email': form.cleaned_data['email'],
                'name': form.cleaned_data['name'],
                'phone': form.cleaned_data.get('phone', ''),
                'address': form.cleaned_data.get('address', ''),
                'password': form.cleaned_data['password1'],
            }
            request.session['pending_signup_data'] = signup_data

            # Generate and send OTP via Brevo/Console
            otp = generate_otp()
            store_otp_in_session(request, signup_data['email'], otp, purpose='registration')
            success, error = send_otp_email(signup_data['email'], otp, purpose='registration')

            if not success:
                print(f"Failed to send OTP email: {error}")
                messages.warning(request, f"Unable to send verification email: {error}. However, you can retrieve your verification OTP code from the 'latest_otp.txt' file in your project directory.")

            # Store email in session for verification page
            request.session['pending_otp_email'] = signup_data['email']
            request.session['pending_otp_source'] = 'signup'
            messages.info(request, f'A verification code has been sent to {signup_data["email"]}.')
            return redirect('users:verify_registration_otp')
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
                is_active=False,
                is_email_verified=False
            )
            is_new = True
        
        # If new user, require OTP verification first
        if is_new:
            # Generate and send OTP via Resend
            otp = generate_otp()
            store_otp_in_session(request, email, otp, purpose='registration')
            success, error_msg = send_otp_email(email, otp, purpose='registration')

            if not success:
                print(f"Failed to send OTP email: {error_msg}")
                messages.warning(request, f"Unable to send verification email: {error_msg}. However, you can retrieve your verification OTP code from the 'latest_otp.txt' file in your project directory.")
            
            # Store email in session for verification page
            request.session['pending_otp_email'] = email
            request.session['pending_otp_source'] = 'google'
            
            if request.method == 'POST':
                return JsonResponse({
                    'requires_otp': True,
                    'message': 'OTP verification required',
                    'redirect': '/users/verify-registration-otp/'
                })
            messages.info(request, f'A verification code has been sent to {email}.')
            return redirect('users:verify_registration_otp')
        
        # Existing user - login directly
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        merge_session_cart_to_db(request)
        
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
    """Send OTP to email or phone number (for OTP login page)"""
    try:
        data = json.loads(request.body)
        contact = data.get('contact')  # email or phone
        contact_type = data.get('type')  # 'email' or 'phone'
        
        if not contact or not contact_type:
            return JsonResponse({'error': 'Missing contact or type'}, status=400)
        
        if contact_type == 'email':
            # Generate and send OTP via Resend
            otp = generate_otp()
            store_otp_in_session(request, contact, otp, purpose='otp_login')
            success, error = send_otp_email(contact, otp, purpose='otp_login')

            if not success:
                return JsonResponse({'error': f'Failed to send OTP email: {error}. However, for development, you can find the login OTP in the "latest_otp.txt" file in the project directory.'}, status=500)

            return JsonResponse({
                'success': True,
                'message': f'OTP sent to {contact}. Check your email.',
            })
        
        elif contact_type == 'phone':
            # Phone OTP still uses Supabase (Resend is email-only)
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
    """Verify OTP and create/login user (for OTP login page)"""
    try:
        data = json.loads(request.body)
        contact = data.get('contact')  # email or phone
        otp = data.get('otp')
        contact_type = data.get('type')  # 'email' or 'phone'
        
        if not contact or not otp or not contact_type:
            return JsonResponse({'error': 'Missing contact, OTP, or type'}, status=400)
        
        if contact_type == 'email':
            # Verify OTP from session (Resend-based)
            valid, error_msg = verify_otp_from_session(request, contact, otp, purpose='otp_login')
            if not valid:
                return JsonResponse({'error': error_msg}, status=400)

            # Create/get Django user
            user = CustomUser.objects.filter(email=contact).first()
            is_new = False

            if not user:
                username = contact.split('@')[0]
                counter = 1
                original_username = username
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1

                user = CustomUser.objects.create(
                    email=contact,
                    username=username,
                    is_active=True,
                    is_email_verified=True
                )
                is_new = True

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            merge_session_cart_to_db(request)

            return JsonResponse({
                'success': True,
                'message': 'Account created and logged in!' if is_new else 'Logged in successfully!',
                'redirect': '/shop/'
            })

        elif contact_type == 'phone':
            # Phone OTP still uses Supabase
            try:
                response = supabase.auth.verify_otp({
                    'phone': contact,
                    'token': otp,
                    'type': 'sms'
                })
                
                if not response.user:
                    return JsonResponse({'error': 'Invalid OTP'}, status=400)
                
                user_phone = response.user.phone or contact
                user = CustomUser.objects.filter(phone=user_phone).first()
                
                is_new = False
                if not user:
                    username = f"user_{user_phone}"
                    counter = 1
                    original_username = username
                    while CustomUser.objects.filter(username=username).exists():
                        username = f"{original_username}{counter}"
                        counter += 1
                    
                    user = CustomUser.objects.create(
                        phone=user_phone,
                        username=username,
                        is_active=True,
                        is_email_verified=True
                    )
                    is_new = True
                
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                merge_session_cart_to_db(request)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Account created and logged in!' if is_new else 'Logged in successfully!',
                    'redirect': '/shop/'
                })
            
            except Exception as otp_error:
                print(f"Phone OTP verification error: {otp_error}")
                return JsonResponse({'error': 'Invalid OTP or expired'}, status=400)
        else:
            return JsonResponse({'error': 'Invalid contact type'}, status=400)
    
    except Exception as e:
        print(f"OTP verify error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ─── Registration OTP Verification ───────────────────────────────────────────

def verify_registration_otp_view(request):
    """OTP verification page for new registrations"""
    pending_email = request.session.get('pending_otp_email')
    if not pending_email:
        messages.error(request, 'No pending verification. Please sign up first.')
        return redirect('users:signup')
    
    # Mask email for display (e.g. m***r@gmail.com)
    parts = pending_email.split('@')
    if len(parts[0]) > 2:
        masked = parts[0][0] + '***' + parts[0][-1] + '@' + parts[1]
    else:
        masked = parts[0][0] + '***@' + parts[1]
    
    return render(request, 'users/verify_registration_otp.html', {
        'masked_email': masked,
        'email': pending_email,
    })


@require_http_methods(["POST"])
def verify_registration_otp_submit(request):
    """AJAX endpoint to verify the registration OTP"""
    try:
        data = json.loads(request.body)
        otp = data.get('otp', '').strip()
        email = request.session.get('pending_otp_email')

        if not email:
            return JsonResponse({'error': 'No pending verification session.'}, status=400)

        if not otp or len(otp) != 6:
            return JsonResponse({'error': 'Please enter a valid 6-digit OTP.'}, status=400)

        # Verify OTP from session (Resend/Brevo-based)
        valid, error_msg = verify_otp_from_session(request, email, otp, purpose='registration')
        if not valid:
            return JsonResponse({'error': error_msg}, status=400)

        source = request.session.get('pending_otp_source', 'signup')

        if source == 'signup':
            signup_data = request.session.get('pending_signup_data')
            if not signup_data:
                return JsonResponse({'error': 'Registration session data not found. Please sign up again.'}, status=400)

            try:
                # Double-check email uniqueness right before database write
                if CustomUser.objects.filter(email=email).exists():
                    return JsonResponse({'error': 'This email has already been registered.'}, status=400)

                # Create the user in the database now that OTP is verified
                user = CustomUser(
                    email=signup_data['email'],
                    username=signup_data['email'],
                    name=signup_data['name'],
                    phone=signup_data['phone'],
                    address=signup_data['address'],
                    is_active=True,
                    is_email_verified=True
                )
                user.set_password(signup_data['password'])
                user.save()

            except Exception as db_err:
                print(f"Error creating user in DB: {db_err}")
                return JsonResponse({'error': f'Failed to create your profile: {db_err}'}, status=500)
        else:
            # Google OAuth registration - inactive user is already in the database
            try:
                user = CustomUser.objects.get(email=email)
                user.is_active = True
                user.is_email_verified = True
                user.save()
            except CustomUser.DoesNotExist:
                return JsonResponse({'error': 'User account not found.'}, status=400)

        # Log them in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        merge_session_cart_to_db(request)

        # Clean up session
        request.session.pop('pending_otp_email', None)
        request.session.pop('pending_otp_source', None)
        request.session.pop('pending_signup_data', None)

        return JsonResponse({
            'success': True,
            'message': 'Email verified successfully! Welcome to MediCart.',
            'redirect': '/shop/'
        })

    except Exception as e:
        print(f"verify_registration_otp_submit error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def resend_registration_otp_view(request):
    """Resend OTP for registration verification"""
    try:
        email = request.session.get('pending_otp_email')
        if not email:
            return JsonResponse({'error': 'No pending verification session.'}, status=400)

        # Generate new OTP and send via Resend
        otp = generate_otp()
        store_otp_in_session(request, email, otp, purpose='registration')
        success, error = send_otp_email(email, otp, purpose='registration')

        if not success:
            return JsonResponse({'error': f'Failed to send OTP email: {error}. However, you can find the verification OTP in the "latest_otp.txt" file in the project directory.'}, status=500)

        return JsonResponse({
            'success': True,
            'message': f'A new OTP has been sent to {email}.'
        })

    except Exception as e:
        print(f"Resend OTP error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ─── Forgot Password ─────────────────────────────────────────────────────────

def forgot_password_view(request):
    """Forgot password page — 3-step flow in one page"""
    if request.user.is_authenticated:
        return redirect('shop:home')
    return render(request, 'users/forgot_password.html')


@require_http_methods(["POST"])
def forgot_password_send_otp(request):
    """Send OTP for password reset"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()

        if not email:
            return JsonResponse({'error': 'Please enter your email address.'}, status=400)

        # Check if user exists
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'No account found with this email address.'}, status=404)

        # Generate and send OTP
        otp = generate_otp()
        store_otp_in_session(request, email, otp, purpose='password_reset')
        success, error = send_otp_email(email, otp, purpose='password_reset')

        if not success:
            return JsonResponse({'error': f'Failed to send OTP email: {error}. However, you can find the password reset OTP in the "latest_otp.txt" file in the project directory.'}, status=500)

        # Store email in session
        request.session['reset_password_email'] = email

        # Mask email for response
        parts = email.split('@')
        if len(parts[0]) > 2:
            masked = parts[0][0] + '***' + parts[0][-1] + '@' + parts[1]
        else:
            masked = parts[0][0] + '***@' + parts[1]

        return JsonResponse({
            'success': True,
            'message': f'OTP sent to {masked}.',
            'masked_email': masked,
        })

    except Exception as e:
        print(f"Forgot password send OTP error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def forgot_password_verify_otp(request):
    """Verify OTP for password reset"""
    try:
        data = json.loads(request.body)
        otp = data.get('otp', '').strip()
        email = request.session.get('reset_password_email')

        if not email:
            return JsonResponse({'error': 'No password reset session found.'}, status=400)

        if not otp or len(otp) != 6:
            return JsonResponse({'error': 'Please enter a valid 6-digit OTP.'}, status=400)

        # Verify OTP from session
        valid, error_msg = verify_otp_from_session(request, email, otp, purpose='password_reset')
        if not valid:
            return JsonResponse({'error': error_msg}, status=400)

        # Mark session as OTP-verified for password reset
        request.session['reset_password_verified'] = True

        return JsonResponse({
            'success': True,
            'message': 'OTP verified. You can now set a new password.'
        })

    except Exception as e:
        print(f"Forgot password verify OTP error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def forgot_password_reset(request):
    """Set new password after OTP verification"""
    try:
        data = json.loads(request.body)
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        email = request.session.get('reset_password_email')
        verified = request.session.get('reset_password_verified', False)

        if not email or not verified:
            return JsonResponse({'error': 'Please verify your OTP first.'}, status=400)

        if not password or len(password) < 6:
            return JsonResponse({'error': 'Password must be at least 6 characters.'}, status=400)

        if password != confirm_password:
            return JsonResponse({'error': 'Passwords do not match.'}, status=400)

        # Update password
        try:
            user = CustomUser.objects.get(email=email)
            user.set_password(password)
            user.save()

            # Clean up session
            request.session.pop('reset_password_email', None)
            request.session.pop('reset_password_verified', None)

            return JsonResponse({
                'success': True,
                'message': 'Password reset successfully! You can now login.',
                'redirect': '/users/login/'
            })

        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User account not found.'}, status=400)

    except Exception as e:
        print(f"Forgot password reset error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def forgot_password_resend_otp(request):
    """Resend OTP for password reset"""
    try:
        email = request.session.get('reset_password_email')
        if not email:
            return JsonResponse({'error': 'No password reset session found.'}, status=400)

        otp = generate_otp()
        store_otp_in_session(request, email, otp, purpose='password_reset')
        success, error = send_otp_email(email, otp, purpose='password_reset')

        if not success:
            return JsonResponse({'error': f'Failed to send OTP email: {error}. However, you can find the password reset OTP in the "latest_otp.txt" file in the project directory.'}, status=500)

        return JsonResponse({
            'success': True,
            'message': f'A new OTP has been sent to {email}.'
        })

    except Exception as e:
        print(f"Forgot password resend OTP error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ─── Profile ─────────────────────────────────────────────────────────────────

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
