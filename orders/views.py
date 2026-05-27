from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__medicine')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def track_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'orders/track_order.html', {'order': order})


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if not order.can_cancel():
        messages.error(request, 'This order cannot be cancelled. Orders can only be cancelled within 24 hours of placement.')
        return redirect('orders:order_detail', pk=pk)
    if request.method == 'POST':
        order.status = 'cancelled'
        order.save()
        # Restore stock
        for item in order.items.all():
            if item.medicine:
                item.medicine.stock_quantity += item.quantity
                item.medicine.save()
        messages.success(request, f'Order #{order.id} has been cancelled successfully.')
        return redirect('orders:order_list')
    return render(request, 'orders/order_detail.html', {'order': order, 'confirm_cancel': True})
