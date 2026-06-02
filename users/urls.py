from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('otp-login/', views.otp_login_view, name='otp_login'),
    path('logout/', views.logout_view, name='logout'),
    path('auth-callback/', views.auth_callback, name='auth_callback'),
    path('profile/', views.profile_view, name='profile'),
    path('send-otp/', views.send_otp_view, name='send_otp'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('verify-registration-otp/', views.verify_registration_otp_view, name='verify_registration_otp'),
    path('verify-registration-otp-submit/', views.verify_registration_otp_submit, name='verify_registration_otp_submit'),
    path('resend-registration-otp/', views.resend_registration_otp_view, name='resend_registration_otp'),
]
