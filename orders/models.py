from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Order(models.Model):
    STATUS_CHOICES = (
        ('confirmed', 'Confirmed'),
        ('packed', 'Packed'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    delivery_address = models.TextField()
    phone = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} by {self.user.email}'

    def can_cancel(self):
        if self.status in ('delivered', 'cancelled'):
            return False
        return timezone.now() - self.created_at < timedelta(hours=24)

    def get_subtotal(self):
        return self.total_price - self.delivery_fee

    def status_step(self):
        steps = ['confirmed', 'packed', 'dispatched', 'delivered']
        try:
            return steps.index(self.status) + 1
        except ValueError:
            return 0


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey('shop.Medicine', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity}x {self.medicine.name if self.medicine else "Deleted"}'

    def item_total(self):
        return self.price * self.quantity
