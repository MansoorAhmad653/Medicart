from django.db import models
from django.conf import settings
from django.utils.text import slugify
from .supabase_storage import SupabaseStorage


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
    requires_prescription = models.BooleanField(default=False)
    manufacturer = models.CharField(max_length=200, blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='medicines/', null=True, blank=True, storage=SupabaseStorage(bucket_name='medicines'))
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

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= 10

    def save(self, *args, **kwargs):
        # Delete the old image from Supabase when the image is being replaced
        if self.pk:
            try:
                old = Medicine.objects.get(pk=self.pk)
                if old.image and old.image.name != self.image.name if self.image else True:
                    # Old image exists and is different from the new one (or cleared)
                    try:
                        old.image.delete(save=False)
                    except Exception:
                        pass  # Don't block the save if delete fails
            except Medicine.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        # Verify Supabase storage and RLS policies only when a new file is uploaded
        if self.image and hasattr(self.image, 'file'):
            from django.core.files.uploadedfile import UploadedFile
            if isinstance(self.image.file, UploadedFile):
                from django.core.exceptions import ValidationError
                from .supabase_storage import SupabaseStorage
                if isinstance(self.image.storage, SupabaseStorage):
                    storage = self.image.storage
                    try:
                        # Test if bucket exists and is accessible using list() which doesn't require service_role key
                        storage.client.storage.from_(storage.bucket_name).list()
                    except Exception as e:
                        err_msg = str(e)
                        if "Bucket not found" in err_msg:
                            raise ValidationError({
                                'image': f"The Supabase storage bucket '{storage.bucket_name}' was not found. "
                                         f"Please create a public bucket named '{storage.bucket_name}' in your Supabase dashboard."
                            })
                        else:
                            raise ValidationError({
                                'image': f"Failed to verify access to Supabase storage bucket '{storage.bucket_name}'. "
                                         f"Please check that the SELECT policy is configured for public access. "
                                         f"Error detail: {err_msg}"
                            })


class Cart(models.Model):
    """Database-backed cart that persists across login/logout sessions."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='db_cart'
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart for {self.user.email}'

    def get_total(self):
        return sum(item.item_total() for item in self.items.select_related('medicine').all())

    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Individual item in a database-backed cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'medicine')

    def __str__(self):
        return f'{self.quantity}x {self.medicine.name}'

    def item_total(self):
        return self.medicine.price * self.quantity

