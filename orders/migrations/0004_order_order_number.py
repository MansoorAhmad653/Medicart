# Generated migration for adding order_number field

from django.db import migrations, models


def populate_order_numbers(apps, schema_editor):
    """Populate order_number for existing orders based on user and created_at"""
    Order = apps.get_model('orders', 'Order')
    
    # Get all users who have orders
    users_with_orders = Order.objects.values_list('user_id', flat=True).distinct().order_by('user_id')
    
    for user_id in users_with_orders:
        # Get all orders for this user, ordered by creation date
        user_orders = Order.objects.filter(user_id=user_id).order_by('created_at')
        
        # Assign sequential order numbers
        for index, order in enumerate(user_orders, start=1):
            order.order_number = index
            order.save(update_fields=['order_number'])


def reverse_populate_order_numbers(apps, schema_editor):
    """Reverse: set all order_number back to 0"""
    Order = apps.get_model('orders', 'Order')
    Order.objects.all().update(order_number=0)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_prescription_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_number',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(populate_order_numbers, reverse_populate_order_numbers),
        migrations.AlterUniqueTogether(
            name='order',
            unique_together={('user', 'order_number')},
        ),
    ]
