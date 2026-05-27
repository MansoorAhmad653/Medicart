from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/<int:pk>/', views.medicine_detail, name='medicine_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
]
