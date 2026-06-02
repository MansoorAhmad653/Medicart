from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, default='bi-capsule')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Medicine(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='medicines')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    description = models.TextField()
    image = models.URLField(max_length=500, blank=True, null=True, help_text="Supabase image URL")
    requires_prescription = models.BooleanField(default=False)
    manufacturer = models.CharField(max_length=200, blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'stock_quantity']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['requires_prescription']),
            models.Index(fields=['name', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock_quantity > 0

    def is_low_stock(self):
        return 0 < self.stock_quantity <= 10
