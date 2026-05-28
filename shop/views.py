from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from .models import Medicine, Category
from .forms import CheckoutForm
from feedback.models import Feedback

DELIVERY_FEE = 150


def home(request):
    # Use select_related to avoid N+1 queries
    featured = Medicine.objects.filter(
        is_active=True, 
        stock_quantity__gt=0
    ).select_related('category')[:8]
    
    categories = Category.objects.all()
    return render(request, 'shop/home.html', {
        'featured': featured,
        'categories': categories,
    })


def medicine_list(request):
    medicines = Medicine.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.all()

    query = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    prescription = request.GET.get('prescription', '')

    if query:
        medicines = medicines.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_slug:
        medicines = medicines.filter(category__slug=category_slug)
    if min_price:
        try:
            medicines = medicines.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            medicines = medicines.filter(price__lte=float(max_price))
        except ValueError:
            pass
    if prescription == 'yes':
        medicines = medicines.filter(requires_prescription=True)
    elif prescription == 'no':
        medicines = medicines.filter(requires_prescription=False)

    # Add pagination (12 items per page)
    paginator = Paginator(medicines, 12)
    page_number = request.GET.get('page', 1)
    medicines_page = paginator.get_page(page_number)

    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()

    return render(request, 'shop/medicine_list.html', {
        'medicines': medicines_page,
        'categories': categories,
        'query': query,
        'category_slug': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'prescription': prescription,
        'selected_category': selected_category,
        'paginator': paginator,
        'page_obj': medicines_page,
    })


def medicine_detail(request, pk):
    medicine = get_object_or_404(Medicine.objects.select_related('category'), pk=pk, is_active=True)
    reviews = Feedback.objects.filter(medicine=medicine).select_related('user').order_by('-created_at')
    avg_rating = 0
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()
    
    # Check prescription status if medicine requires prescription
    prescription_status = None
    can_buy = True
    if medicine.requires_prescription:
        can_buy = False
        if request.user.is_authenticated:
            from prescriptions.models import Prescription
            prescription = Prescription.objects.filter(
                user=request.user,
                medicines=medicine,
                status='approved'
            ).first()
            
            if prescription:
                can_buy = True
                prescription_status = {'status': 'approved', 'message': 'Prescription approved! You can add this to cart.'}
            else:
                # Check if user has any prescription for this medicine (pending/rejected)
                pending = Prescription.objects.filter(
                    user=request.user,
                    medicines=medicine,
                    status='pending'
                ).first()
                
                if pending:
                    prescription_status = {'status': 'pending', 'message': 'Your prescription is pending approval. Please wait.'}
                else:
                    rejected = Prescription.objects.filter(
                        user=request.user,
                        medicines=medicine,
                        status='rejected'
                    ).first()
                    
                    if rejected:
                        prescription_status = {'status': 'rejected', 'message': f'Prescription rejected. Admin notes: {rejected.admin_notes}', 'prescription_id': rejected.id}
                    else:
                        prescription_status = {'status': 'no_prescription', 'message': 'Please upload a valid prescription to buy this medicine.'}
    
    return render(request, 'shop/medicine_detail.html', {
        'medicine': medicine,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'prescription_status': prescription_status,
        'can_buy': can_buy,
    })


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = 0

    # Batch load all medicines at once instead of individual queries
    if cart:
        medicine_ids = [int(med_id) for med_id in cart.keys()]
        medicines = Medicine.objects.filter(pk__in=medicine_ids).in_bulk()
        
        for med_id, item in cart.items():
            medicine = medicines.get(int(med_id))
            if medicine:
                item_total = medicine.price * item['quantity']
                subtotal += item_total
                cart_items.append({
                    'medicine': medicine,
                    'quantity': item['quantity'],
                    'item_total': item_total,
                })

    total = subtotal + DELIVERY_FEE if cart_items else 0
    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': DELIVERY_FEE,
        'total': total,
    })


def add_to_cart(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk, is_active=True)
    cart = request.session.get('cart', {})
    med_id = str(pk)

    # Check if medicine requires prescription
    if medicine.requires_prescription:
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to add prescription medicines to cart.')
            return redirect('users:login')
        
        # Check if user has approved prescription for this medicine
        from prescriptions.models import Prescription
        approved_prescription = Prescription.objects.filter(
            user=request.user,
            medicines=medicine,
            status='approved'
        ).first()
        
        if not approved_prescription:
            messages.error(request, 'You do not have an approved prescription for this medicine. Please upload your prescription and wait for approval.')
            return redirect('shop:medicine_detail', pk=pk)

    if med_id in cart:
        if cart[med_id]['quantity'] < medicine.stock_quantity:
            cart[med_id]['quantity'] += 1
            messages.success(request, f'Updated {medicine.name} quantity in cart.')
        else:
            messages.warning(request, f'Sorry, only {medicine.stock_quantity} units available.')
    else:
        cart[med_id] = {'quantity': 1, 'name': medicine.name, 'price': str(medicine.price)}
        messages.success(request, f'{medicine.name} added to cart!')

    request.session['cart'] = cart
    request.session.modified = True
    return redirect(request.META.get('HTTP_REFERER', 'shop:cart'))


def update_cart(request, pk):
    med_id = str(pk)
    cart = request.session.get('cart', {})
    action = request.POST.get('action')

    if med_id in cart:
        if action == 'increase':
            medicine = get_object_or_404(Medicine, pk=pk)
            if cart[med_id]['quantity'] < medicine.stock_quantity:
                cart[med_id]['quantity'] += 1
        elif action == 'decrease':
            cart[med_id]['quantity'] -= 1
            if cart[med_id]['quantity'] <= 0:
                del cart[med_id]
                messages.info(request, 'Item removed from cart.')
        elif action == 'remove':
            del cart[med_id]
            messages.info(request, 'Item removed from cart.')

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('shop:cart')


def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('shop:cart')

    if not request.user.is_authenticated:
        messages.info(request, 'Please login to proceed with checkout.')
        return redirect('users:login')

    cart_items = []
    subtotal = 0
    
    # Batch load all medicines instead of individual queries
    medicine_ids = [int(med_id) for med_id in cart.keys()]
    medicines = Medicine.objects.filter(pk__in=medicine_ids).in_bulk() if medicine_ids else {}
    
    for med_id, item in cart.items():
        medicine = medicines.get(int(med_id))
        if medicine:
            item_total = medicine.price * item['quantity']
            subtotal += item_total
            cart_items.append({'medicine': medicine, 'quantity': item['quantity'], 'item_total': item_total})

    total = subtotal + DELIVERY_FEE

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            from orders.models import Order, OrderItem
            order = Order.objects.create(
                user=request.user,
                delivery_address=form.cleaned_data['delivery_address'],
                phone=form.cleaned_data['phone'],
                total_price=total,
                delivery_fee=DELIVERY_FEE,
            )
            # Batch update medicines
            bulk_update_items = []
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    medicine=item['medicine'],
                    quantity=item['quantity'],
                    price=item['medicine'].price,
                )
                item['medicine'].stock_quantity -= item['quantity']
                bulk_update_items.append(item['medicine'])
            
            # Batch update all medicines at once
            Medicine.objects.bulk_update(bulk_update_items, ['stock_quantity'], batch_size=100)

            request.session['cart'] = {}
            request.session.modified = True
            messages.success(request, f'Order #{order.id} placed successfully! We will deliver it soon.')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {'delivery_address': request.user.address, 'phone': request.user.phone}
        form = CheckoutForm(user=request.user, initial=initial)

    return render(request, 'shop/checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': DELIVERY_FEE,
        'total': total,
    })
