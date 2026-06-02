"""
Cart utility functions.
- Authenticated users: read/write from Cart/CartItem DB models.
- Anonymous users: read/write from request.session['cart'].
"""
from .models import Medicine, Cart, CartItem


# ── Read helpers ──────────────────────────────────────────────────────────────

def get_cart_items(request):
    """Return a list of dicts: [{ medicine, quantity, item_total }, …]"""
    if request.user.is_authenticated:
        return _db_cart_items(request.user)
    return _session_cart_items(request)


def get_cart_count(request):
    """Total number of units in the cart (for navbar badge)."""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            return cart.get_item_count()
        return 0
    session_cart = request.session.get('cart', {})
    return sum(item['quantity'] for item in session_cart.values())


# ── Write helpers ─────────────────────────────────────────────────────────────

def add_item(request, medicine, quantity=1):
    """Add *quantity* units of *medicine* to the cart. Returns (success, msg)."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, medicine=medicine, defaults={'quantity': 0})
        new_qty = item.quantity + quantity
        if new_qty > medicine.stock_quantity:
            return False, f'Sorry, only {medicine.stock_quantity} units available.'
        item.quantity = new_qty
        item.save()
        cart.save()  # bump updated_at
        return True, (f'{medicine.name} added to cart!' if created else f'Updated {medicine.name} quantity in cart.')
    else:
        return _session_add(request, medicine, quantity)


def update_item(request, medicine_pk, action):
    """Increase / decrease / remove an item. Returns a status message or None."""
    if request.user.is_authenticated:
        return _db_update(request.user, medicine_pk, action)
    return _session_update(request, medicine_pk, action)


def clear_cart(request):
    """Empty the cart entirely."""
    if request.user.is_authenticated:
        Cart.objects.filter(user=request.user).delete()
    else:
        request.session['cart'] = {}
        request.session.modified = True


def get_raw_cart_dict(request):
    """Return a dict {str(medicine_id): {'quantity': int}} for checkout logic."""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).prefetch_related('items__medicine').first()
        if not cart:
            return {}
        return {
            str(item.medicine_id): {'quantity': item.quantity, 'name': item.medicine.name, 'price': str(item.medicine.price)}
            for item in cart.items.select_related('medicine').all()
        }
    return request.session.get('cart', {})


# ── Merge session→DB on login ─────────────────────────────────────────────────

def merge_session_cart_to_db(request):
    """Called right after login. Moves any session-cart items into the DB cart."""
    session_cart = request.session.get('cart', {})
    if not session_cart or not request.user.is_authenticated:
        return

    cart, _ = Cart.objects.get_or_create(user=request.user)

    medicine_ids = [int(mid) for mid in session_cart.keys()]
    medicines = Medicine.objects.filter(pk__in=medicine_ids).in_bulk()

    for mid_str, data in session_cart.items():
        medicine = medicines.get(int(mid_str))
        if not medicine:
            continue
        item, created = CartItem.objects.get_or_create(cart=cart, medicine=medicine, defaults={'quantity': 0})
        # Take the larger quantity (don't lose items already in DB)
        item.quantity = max(item.quantity, data['quantity'])
        item.save()

    # Clear the session cart so it doesn't get double-counted
    request.session['cart'] = {}
    request.session.modified = True


# ── Internal: DB-backed helpers ───────────────────────────────────────────────

def _db_cart_items(user):
    cart = Cart.objects.filter(user=user).prefetch_related('items__medicine__category').first()
    if not cart:
        return []
    result = []
    for ci in cart.items.select_related('medicine', 'medicine__category').all():
        result.append({
            'medicine': ci.medicine,
            'quantity': ci.quantity,
            'item_total': ci.item_total(),
        })
    return result


def _db_update(user, medicine_pk, action):
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        return None
    try:
        item = CartItem.objects.select_related('medicine').get(cart=cart, medicine_id=medicine_pk)
    except CartItem.DoesNotExist:
        return None

    if action == 'increase':
        if item.quantity < item.medicine.stock_quantity:
            item.quantity += 1
            item.save()
    elif action == 'decrease':
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
            return 'Item removed from cart.'
        item.save()
    elif action == 'remove':
        item.delete()
        return 'Item removed from cart.'
    return None


# ── Internal: Session-backed helpers ──────────────────────────────────────────

def _session_cart_items(request):
    cart = request.session.get('cart', {})
    if not cart:
        return []
    medicine_ids = [int(mid) for mid in cart.keys()]
    medicines = Medicine.objects.filter(pk__in=medicine_ids).in_bulk()
    result = []
    for mid_str, data in cart.items():
        med = medicines.get(int(mid_str))
        if med:
            result.append({
                'medicine': med,
                'quantity': data['quantity'],
                'item_total': med.price * data['quantity'],
            })
    return result


def _session_add(request, medicine, quantity):
    cart = request.session.get('cart', {})
    mid = str(medicine.pk)
    if mid in cart:
        if cart[mid]['quantity'] + quantity > medicine.stock_quantity:
            return False, f'Sorry, only {medicine.stock_quantity} units available.'
        cart[mid]['quantity'] += quantity
        msg = f'Updated {medicine.name} quantity in cart.'
    else:
        cart[mid] = {'quantity': quantity, 'name': medicine.name, 'price': str(medicine.price)}
        msg = f'{medicine.name} added to cart!'
    request.session['cart'] = cart
    request.session.modified = True
    return True, msg


def _session_update(request, medicine_pk, action):
    cart = request.session.get('cart', {})
    mid = str(medicine_pk)
    msg = None
    if mid in cart:
        if action == 'increase':
            medicine = Medicine.objects.filter(pk=medicine_pk).first()
            if medicine and cart[mid]['quantity'] < medicine.stock_quantity:
                cart[mid]['quantity'] += 1
        elif action == 'decrease':
            cart[mid]['quantity'] -= 1
            if cart[mid]['quantity'] <= 0:
                del cart[mid]
                msg = 'Item removed from cart.'
        elif action == 'remove':
            del cart[mid]
            msg = 'Item removed from cart.'
    request.session['cart'] = cart
    request.session.modified = True
    return msg
