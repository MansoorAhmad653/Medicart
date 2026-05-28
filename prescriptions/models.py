from django.db import models
from django.conf import settings


class Prescription(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions')
    medicines = models.ManyToManyField('shop.Medicine', blank=True, related_name='prescriptions', help_text='Medicines approved under this prescription')
    file = models.FileField(upload_to='prescriptions/')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Prescription by {self.user.email} - {self.status}'

    def is_image(self):
        name = self.file.name.lower()
        return name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    def get_approved_medicines(self):
        """Get medicines approved under this prescription"""
        if self.is_approved:
            return self.medicines.all()
        return self.medicines.none()
