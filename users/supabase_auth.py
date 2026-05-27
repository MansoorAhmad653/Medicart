import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def get_gmail_login_url(redirect_url: str = 'http://localhost:8000/users/auth-callback/'):
    """
    Get Gmail OAuth login redirect URL
    
    Args:
        redirect_url: Where to redirect after OAuth callback
        
    Returns:
        OAuth URL for Gmail login
    """
    try:
        response = supabase.auth.sign_in_with_oauth({
            'provider': 'google',
            'redirect_to': redirect_url
        })
        return response
    except Exception as e:
        print(f"Error getting Gmail login URL: {e}")
        return None

def get_user_from_token(access_token: str):
    """
    Get user info from Supabase access token
    
    Args:
        access_token: Supabase JWT token
        
    Returns:
        User data dict or None
    """
    try:
        # This will be handled by Supabase client automatically
        # when session is established
        return None
    except Exception as e:
        print(f"Error getting user from token: {e}")
        return None

def verify_supabase_connection():
    """Test Supabase connection"""
    try:
        # Try to get auth settings
        response = supabase.auth.get_session()
        return True
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return False
