from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
import json
from orders.models import Order
from shop.models import Medicine
from prescriptions.models import Prescription
from users.models import CustomUser


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not (request.user.is_staff or request.user.role == 'admin'):
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('shop:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def admin_dashboard(request):
    total_orders = Order.objects.count()
    total_revenue = Order.objects.exclude(status='cancelled').aggregate(total=Sum('total_price'))['total'] or 0
    pending_prescriptions = Prescription.objects.filter(status='pending').count()
    low_stock = Medicine.objects.filter(stock_quantity__lte=10, is_active=True).count()

    # Weekly orders for chart
    today = timezone.now().date()
    week_labels = []
    week_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Order.objects.filter(created_at__date=day).count()
        week_labels.append(day.strftime('%a'))
        week_data.append(count)

    recent_orders = Order.objects.select_related('user').prefetch_related('items')[:20]
    medicines = Medicine.objects.select_related('category').order_by('stock_quantity')[:20]
    total_users = CustomUser.objects.filter(role='customer').count()

    # Handle status update
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        if order_id and new_status:
            order = get_object_or_404(Order, pk=order_id)
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.order_number} status updated to {new_status}.')
            return redirect('dashboard:admin_dashboard')

    return render(request, 'dashboard/admin_dashboard.html', {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_prescriptions': pending_prescriptions,
        'low_stock': low_stock,
        'total_users': total_users,
        'recent_orders': recent_orders,
        'medicines': medicines,
        'week_labels': json.dumps(week_labels),
        'week_data': json.dumps(week_data),
        'status_choices': Order.STATUS_CHOICES,
    })
