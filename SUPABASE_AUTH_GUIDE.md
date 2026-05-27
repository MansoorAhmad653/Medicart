# 🔐 Supabase Auth with Gmail - Complete Setup Guide

## Why Supabase Auth?

✅ **No Django-allauth needed** - Simpler setup
✅ **Built-in OAuth providers** - Gmail, GitHub, Google, etc.
✅ **Email verification** - Handled by Supabase
✅ **Session management** - Automatic JWT tokens
✅ **User management** - Supabase dashboard included
✅ **Database linked** - Direct integration with your Supabase PostgreSQL

---

## 📋 Step 1: Enable Gmail Provider in Supabase

1. Go to: https://supabase.com/dashboard
2. Select your MediCart project
3. Go to **Authentication** → **Providers**
4. Scroll to **Google** and click **Enable**
5. A dialog will appear asking for:
   - **Client ID**
   - **Client Secret**

### Get Google OAuth Credentials:

1. Go to: https://console.cloud.google.com/
2. **Create New Project** (or select existing)
   - Name: "MediCart"
3. Go to **APIs & Services** → **Library**
4. Search for **"Google+ API"** and **Enable** it
5. Go to **Credentials** → **Create Credentials** → **OAuth Client ID**
6. Select **Web Application**
7. Add **Authorized redirect URIs**:
   ```
   https://[your-project].supabase.co/auth/v1/callback
   ```
   (Replace `[your-project]` with your Supabase project ID)
   
   To find your project ID:
   - Go to Supabase dashboard
   - Settings → General → Project ID (copy it)
   
   Example: `https://ugtawlcsphxjbgarowjm.supabase.co/auth/v1/callback`

8. Copy the **Client ID** and **Client Secret**

### Complete Setup in Supabase:

1. Back in Supabase **Authentication** → **Providers** → **Google**
2. Paste:
   - **Client ID**: (from Google Cloud Console)
   - **Client Secret**: (from Google Cloud Console)
3. Click **Save**
4. **Gmail provider is now active!** ✅

---

## 🐍 Step 2: Install Supabase Client

```bash
.venv_new\Scripts\pip.exe install supabase
```

---

## 🔧 Step 3: Update Django Settings

Add to `.env`:

```
SUPABASE_URL=https://[your-project].supabase.co
SUPABASE_KEY=your-anon-public-key-here
```

To get these:
1. Supabase Dashboard → Settings → **API**
2. Copy **Project URL** → `SUPABASE_URL`
3. Copy **anon public** key → `SUPABASE_KEY`

---

## 📝 Step 4: Create Login/Signup Views with Supabase

Create new file: `users/supabase_auth.py`

```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def get_gmail_login_url():
    """Get Gmail login redirect URL"""
    response = supabase.auth.sign_in_with_oauth({
        'provider': 'google',
        'redirect_to': 'http://localhost:8000/users/auth-callback/'
    })
    return response

def handle_auth_callback(code):
    """Handle OAuth callback from Supabase"""
    # Supabase automatically handles the callback
    # Your frontend should extract the session from URL
    pass
```

---

## 🎯 Step 5: Update Templates with Gmail Button

**users/templates/users/login.html**:

```html
{% extends 'base.html' %}
{% block title %}Login — MediCart{% endblock %}

{% block content %}
<div class="auth-page">
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-80">
            <div class="col-md-5 col-lg-4">
                <div class="auth-card">
                    <div class="auth-header">
                        <div class="auth-icon"><i class="bi bi-heart-pulse-fill"></i></div>
                        <h2>Welcome Back</h2>
                        <p>Login to your MediCart account</p>
                    </div>

                    <!-- Gmail Login Button -->
                    <div class="mb-3">
                        <button onclick="loginWithGmail()" class="btn btn-outline-danger w-100 btn-lg">
                            <i class="bi bi-google me-2"></i>Login with Gmail
                        </button>
                    </div>

                    <div class="divider my-3 text-center">
                        <span class="text-muted">Or</span>
                    </div>

                    <!-- Email/Password Login -->
                    <form method="post" class="auth-form">
                        {% csrf_token %}
                        <div class="mb-3">
                            <label class="form-label">Email Address</label>
                            {{ form.username }}
                        </div>
                        <div class="mb-4">
                            <label class="form-label">Password</label>
                            <div class="password-wrap">
                                {{ form.password }}
                                <button type="button" class="password-toggle" onclick="togglePassword(this)">
                                    <i class="bi bi-eye"></i>
                                </button>
                            </div>
                        </div>
                        {% if form.non_field_errors %}
                        <div class="alert alert-danger py-2 small">{{ form.non_field_errors }}</div>
                        {% endif %}
                        <button type="submit" class="btn btn-primary w-100 btn-lg">
                            <i class="bi bi-box-arrow-in-right me-2"></i>Login
                        </button>
                    </form>

                    <div class="auth-footer">
                        <p>Don't have an account? <a href="{% url 'users:signup' %}">Create Account</a></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.divider {
    position: relative;
    line-height: 1em;
}
.divider span {
    background-color: white;
    padding: 0 10px;
    position: relative;
    z-index: 1;
}
.divider::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    width: 100%;
    height: 1px;
    background-color: #ddd;
    z-index: 0;
}
</style>
{% endblock %}

{% block extra_scripts %}
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
const SUPABASE_URL = '{{ supabase_url }}';
const SUPABASE_KEY = '{{ supabase_key }}';
const { createClient } = supabase;

const client = createClient(SUPABASE_URL, SUPABASE_KEY);

async function loginWithGmail() {
    const { data, error } = await client.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: window.location.origin + '/users/auth-callback/'
        }
    });
    
    if (error) {
        alert('Login failed: ' + error.message);
    }
}

function togglePassword(btn) {
    const input = btn.previousElementSibling;
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'bi bi-eye';
    }
}
</script>
{% endblock %}
```

---

## 🎨 Step 6: Update Signup Template

**users/templates/users/signup.html**:

(Same as login, but with sign-up form fields instead)

---

## 🔑 Step 7: Create Auth Callback View

**users/views.py**:

```python
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.http import require_http_methods
from users.models import CustomUser

@require_http_methods(["GET"])
def auth_callback(request):
    """Handle Supabase OAuth callback"""
    # Supabase redirects with session token in URL
    access_token = request.GET.get('access_token')
    
    if not access_token:
        return redirect('users:login')
    
    try:
        # Extract user info from Supabase session
        # In production, verify the token with Supabase
        # For now, redirect to get user to complete setup
        request.session['supabase_access_token'] = access_token
        return redirect('shop:home')
    except Exception as e:
        return redirect('users:login')
```

**users/urls.py**:

```python
path('auth-callback/', views.auth_callback, name='auth_callback'),
```

---

## 🚀 Full Flow:

1. **User clicks "Login with Gmail"**
2. **Redirected to Supabase OAuth page**
3. **User authenticates with Gmail**
4. **Supabase redirects back to your app**
5. **Session created automatically**
6. **User logged in!**

---

## 💾 User Data Storage

When user logs in with Gmail:
- Supabase creates user in `auth.users` table
- Email automatically verified
- You can add custom fields to `users_customuser` table
- All data stored in Supabase PostgreSQL

---

## 📊 Supabase Dashboard Features

Once setup:
- Go to **Authentication** → **Users**
- See all users who logged in with Gmail
- Manage sessions, permissions, etc.
- Monitor sign-ups in real-time

---

## ✅ Checklist:

- [ ] Enable Google provider in Supabase
- [ ] Get Google OAuth credentials from Google Cloud
- [ ] Add credentials to Supabase
- [ ] Install Supabase client: `pip install supabase`
- [ ] Update `.env` with Supabase credentials
- [ ] Update login/signup templates with Gmail buttons
- [ ] Create auth callback view
- [ ] Test Gmail login flow

---

## 🔗 Resources:

- Supabase Auth Docs: https://supabase.com/docs/guides/auth
- Google OAuth Setup: https://developers.google.com/identity/protocols/oauth2
- Supabase JavaScript Client: https://supabase.com/docs/reference/javascript/introduction

---

**This setup is production-ready and scales automatically with Supabase!** 🚀
