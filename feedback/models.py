from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedbacks')
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
    medicine = models.ForeignKey('shop.Medicine', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Feedback by {self.user.email} - {self.rating}/5'

    def star_range(self):
        return range(1, 6)
