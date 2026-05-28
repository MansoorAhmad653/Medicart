from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    path('upload/', views.upload_prescription, name='upload'),
    path('delete/<int:pk>/', views.delete_prescription, name='delete'),
    path('check/<int:medicine_id>/', views.user_can_buy_prescription_medicine, name='check'),
]
