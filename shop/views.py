from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.core.cache import cache
from .models import Medicine, Category
from .forms import CheckoutForm
from .cart_utils import get_cart_items, add_item, update_item, clear_cart, get_raw_cart_dict
from feedback.models import Feedback

DELIVERY_FEE = 150


def home(request):
    # Use select_related to avoid N+1 queries and cache the result
    featured = cache.get('home_featured_medicines')
    if featured is None:
        featured = list(Medicine.objects.filter(
            is_active=True, 
            stock_quantity__gt=0
        ).select_related('category')[:8])
        cache.set('home_featured_medicines', featured, 60 * 5)  # Cache for 5 minutes
    
    categories = cache.get('shop_categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('shop_categories', categories, 60 * 5)  # Cache for 5 minutes

    return render(request, 'shop/home.html', {
        'featured': featured,
        'categories': categories,
    })


def medicine_list(request):
    medicines = Medicine.objects.filter(is_active=True).select_related('category')
    
    categories = cache.get('shop_categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('shop_categories', categories, 60 * 5)

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
        # Search category in memory from already fetched categories list
        selected_category = next((c for c in categories if c.slug == category_slug), None)

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
    reviews = list(Feedback.objects.filter(medicine=medicine).select_related('user').order_by('-created_at'))
    num_reviews = len(reviews)
    avg_rating = 0
    if num_reviews > 0:
        avg_rating = sum(r.rating for r in reviews) / num_reviews
    
    # Check prescription status if medicine requires prescription
    prescription_status = None
    can_buy = True
    if medicine.requires_prescription:
        can_buy = False
        if request.user.is_authenticated:
            from prescriptions.models import Prescription
            # Consolidate approved, pending, rejected queries into a single query
            user_prescriptions = list(Prescription.objects.filter(
                user=request.user,
                medicines=medicine
            ).order_by('-uploaded_at'))
            
            approved = next((p for p in user_prescriptions if p.status == 'approved'), None)
            pending = next((p for p in user_prescriptions if p.status == 'pending'), None)
            rejected = next((p for p in user_prescriptions if p.status == 'rejected'), None)
            
            if approved:
                can_buy = True
                prescription_status = {'status': 'approved', 'message': 'Prescription approved! You can add this to cart.'}
            elif pending:
                prescription_status = {'status': 'pending', 'message': 'Your prescription is pending approval. Please wait.'}
            elif rejected:
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
    cart_items = get_cart_items(request)
    subtotal = sum(item['item_total'] for item in cart_items)
    total = subtotal + DELIVERY_FEE if cart_items else 0

    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': DELIVERY_FEE,
        'total': total,
    })


def add_to_cart(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk, is_active=True)

    # Check if medicine requires prescription
    if medicine.requires_prescription:
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to add prescription medicines to cart.')
            return redirect('users:login')
        
        from prescriptions.models import Prescription
        approved_prescription = Prescription.objects.filter(
            user=request.user,
            medicines=medicine,
            status='approved'
        ).first()
        
        if not approved_prescription:
            messages.warning(request, f"{medicine.name} requires a prescription. You can add it to your cart, but you must upload a prescription and wait for pharmacist approval before checking out.")

    success, msg = add_item(request, medicine)
    if success:
        messages.success(request, msg)
    else:
        messages.warning(request, msg)

    return redirect(request.META.get('HTTP_REFERER', 'shop:cart'))


def update_cart(request, pk):
    action = request.POST.get('action')
    msg = update_item(request, pk, action)
    if msg:
        messages.info(request, msg)
    return redirect('shop:cart')


def checkout_view(request):
    cart_dict = get_raw_cart_dict(request)
    if not cart_dict:
        messages.warning(request, 'Your cart is empty.')
        return redirect('shop:cart')

    if not request.user.is_authenticated:
        messages.info(request, 'Please login to proceed with checkout.')
        return redirect('users:login')

    from prescriptions.models import Prescription
    from orders.models import Order, OrderItem

    cart_items = []
    subtotal = 0
    requires_prescription = False
    has_approved_prescriptions = True
    
    # Batch load all medicines instead of individual queries
    medicine_ids = [int(med_id) for med_id in cart_dict.keys()]
    medicines = Medicine.objects.filter(pk__in=medicine_ids).in_bulk() if medicine_ids else {}
    
    for med_id, item in cart_dict.items():
        medicine = medicines.get(int(med_id))
        if medicine:
            item_total = medicine.price * item['quantity']
            subtotal += item_total
            
            # Check prescription status for this item
            item_prescription_status = None
            if medicine.requires_prescription:
                requires_prescription = True
                
                # Check for approved prescription
                approved = Prescription.objects.filter(
                    user=request.user,
                    status='approved',
                    medicines=medicine
                ).exists()
                
                if approved:
                    item_prescription_status = {'status': 'approved', 'message': 'Approved'}
                else:
                    has_approved_prescriptions = False
                    # Check for pending prescription
                    pending = Prescription.objects.filter(
                        user=request.user,
                        status='pending'
                    ).first()
                    
                    if pending:
                        item_prescription_status = {'status': 'pending', 'message': 'Pending review'}
                    else:
                        # Check for rejected prescription
                        rejected = Prescription.objects.filter(
                            user=request.user,
                            status='rejected'
                        ).first()
                        
                        if rejected:
                            item_prescription_status = {
                                'status': 'rejected', 
                                'message': f'Rejected. Notes: {rejected.admin_notes}'
                            }
                        else:
                            item_prescription_status = {'status': 'missing', 'message': 'Prescription required'}
            
            cart_items.append({
                'medicine': medicine, 
                'quantity': item['quantity'], 
                'item_total': item_total,
                'prescription_status': item_prescription_status
            })

    total = subtotal + DELIVERY_FEE

    if request.method == 'POST':
        form = CheckoutForm(request.POST, request.FILES, user=request.user)
        
        # Enforce prescription file upload if unapproved items exist
        prescription_file = request.FILES.get('prescription_file')
        if requires_prescription and not has_approved_prescriptions and not prescription_file:
            form.add_error('prescription_file', 'Please upload a scanned image or PDF of your valid prescription.')
            messages.error(request, 'Please upload a prescription to complete your order.')
        
        if form.is_valid():
            uploaded_prescription = None
            order_status = 'confirmed'
            
            # 1. Handle prescription upload if required and not already approved
            if requires_prescription and not has_approved_prescriptions:
                try:
                    uploaded_prescription = Prescription.objects.create(
                        user=request.user,
                        file=prescription_file,
                        notes=form.cleaned_data.get('notes', ''),
                        status='pending'
                    )
                    
                    # Associate all prescription-required medicines in the cart with this prescription
                    rx_medicines = [item['medicine'] for item in cart_items if item['medicine'].requires_prescription]
                    uploaded_prescription.medicines.add(*rx_medicines)
                    
                    order_status = 'pending_prescription'
                    print(f"Prescription uploaded and associated with medicines: {rx_medicines}")
                except Exception as e:
                    messages.error(request, f'Failed to process prescription upload: {e}')
                    return redirect('shop:checkout')
            
            # 2. Create the order
            order = Order.objects.create(
                user=request.user,
                delivery_address=form.cleaned_data['delivery_address'],
                phone=form.cleaned_data['phone'],
                total_price=total,
                delivery_fee=DELIVERY_FEE,
                status=order_status,
                prescription=uploaded_prescription,
                notes=form.cleaned_data.get('notes', '')
            )
            
            # 3. Create OrderItems and update stock
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

            # 4. Clear the cart (both DB and session)
            clear_cart(request)
            
            if order_status == 'pending_prescription':
                messages.success(
                    request, 
                    f'Order #{order.order_number} placed successfully! It is currently pending prescription approval. '
                    f'Once our pharmacist approves your uploaded prescription, we will dispatch it!'
                )
            else:
                messages.success(request, f'Order #{order.order_number} placed successfully! We will deliver it soon.')
                
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
        'requires_prescription': requires_prescription,
        'has_approved_prescriptions': has_approved_prescriptions,
    })
