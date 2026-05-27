from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import FeedbackForm
from .models import Feedback
from orders.models import Order
from shop.models import Medicine


@login_required
def submit_feedback(request):
    order_id = request.GET.get('order')
    medicine_id = request.GET.get('medicine')
    order = None
    medicine = None

    if order_id:
        order = get_object_or_404(Order, pk=order_id, user=request.user, status='delivered')
    if medicine_id:
        medicine = get_object_or_404(Medicine, pk=medicine_id)

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.order = order
            feedback.medicine = medicine
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            if order:
                return redirect('orders:order_detail', pk=order.pk)
            return redirect('shop:home')
        else:
            messages.error(request, 'Please correct the errors.')
    else:
        form = FeedbackForm()

    return render(request, 'feedback/feedback.html', {
        'form': form,
        'order': order,
        'medicine': medicine,
    })
