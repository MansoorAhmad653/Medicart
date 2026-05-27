# 🏥 MediCart — Online Pharmacy & Medicine Delivery

A full-stack Django web application for online pharmacy and medicine delivery with prescription management, order tracking, and admin dashboard.

---

## 🛠️ Tech Stack

| Layer       | Technology          |
|-------------|---------------------|
| Backend     | Django 4.2 (Python) |
| Frontend    | Bootstrap 5.3       |
| Database    | SQLite              |
| Templates   | Django Templates    |
| Styling     | Custom CSS + Bootstrap Icons |
| Charts      | Chart.js            |

---

## 📁 Project Structure

```
medicart/
├── manage.py
├── requirements.txt
├── medicart/           # Project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/              # Auth, profiles
├── shop/               # Medicines, cart, checkout
├── orders/             # Order management & tracking
├── prescriptions/      # Prescription upload & verification
├── feedback/           # Reviews & ratings
├── dashboard/          # Admin analytics dashboard
├── templates/          # Shared base template
└── static/             # CSS, JS, images
```

---

## 🚀 Quick Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd medicart
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Seed sample data (medicines, categories, admin user)

```bash
python manage.py seed_data
```

This creates:
- 6 medicine categories
- 10 sample medicines (with varied stock levels)
- 1 admin user

**Admin credentials:**
- Email: `admin@medicart.pk`
- Password: `admin123`

### 6. Run the development server

```bash
python manage.py runserver
```

Open your browser at: **http://127.0.0.1:8000**

---

## 🔗 URL Routes

| URL | Description |
|-----|-------------|
| `/` | Home page |
| `/shop/medicines/` | Browse all medicines |
| `/shop/medicines/<id>/` | Medicine detail |
| `/shop/cart/` | Shopping cart |
| `/shop/checkout/` | Checkout |
| `/users/signup/` | Create account |
| `/users/login/` | Login |
| `/users/profile/` | Profile management |
| `/orders/` | My orders |
| `/orders/<id>/` | Order detail |
| `/orders/<id>/track/` | Track order |
| `/prescriptions/upload/` | Upload prescription |
| `/feedback/submit/` | Submit review |
| `/dashboard/` | Admin dashboard |
| `/admin/` | Django admin panel |

---

## ✨ Features

### 🛍️ Shopping
- Browse medicines with search, category filter, price range filter
- Prescription-required badge on Rx medicines
- Cart stored in session (no login required to browse)
- Delivery fee: Rs. 150 flat

### 📦 Orders
- Order confirmation with unique ID
- Visual 4-stage status stepper: Confirmed → Packed → Dispatched → Delivered
- Order cancellation within 24 hours
- Per-order detailed receipt

### 💊 Prescriptions
- Upload image (JPG/PNG) or PDF prescriptions
- Admin reviews and approves/rejects via Django admin
- Status tracking: Pending → Approved/Rejected
- Pharmacist notes displayed to user

### ⭐ Reviews
- Star rating (1–5) with comment
- Reviews visible on medicine detail page
- Triggered after order delivery

### 📊 Admin Dashboard
- Total orders, revenue, pending Rx, low stock summary cards
- Weekly orders bar chart (Chart.js)
- Real-time order status update from dashboard
- Inventory table with stock level indicators
- Links to Django admin for full CRUD

---

## 👤 User Roles

| Role | Capabilities |
|------|-------------|
| **Customer** | Browse, add to cart, checkout, track orders, upload prescriptions, leave reviews |
| **Admin** | All customer features + admin dashboard + manage all data via Django admin |

---

## 🎨 Design System

| Token | Value |
|-------|-------|
| Primary Teal | `#0F6E56` |
| Accent Coral | `#D85A30` |
| Light Mint | `#E1F5EE` |
| Heading Font | Playfair Display |
| Body Font | Plus Jakarta Sans |

---

## 🔧 Django Admin

Access at `/admin/` with admin credentials.

Manage:
- Users & roles
- Categories & medicines (stock, pricing)
- Orders (status updates)
- Prescriptions (approve/reject)
- Feedback & reviews

---

## 📦 Creating a Superuser Manually

```bash
python manage.py createsuperuser
```

---

## 🌱 Re-seeding Data

The seed command is idempotent — running it again won't duplicate data:

```bash
python manage.py seed_data
```

---

## 📸 Media Files

Uploaded files (prescriptions, medicine images) are stored in `/media/`.

In development, Django serves these automatically when `DEBUG=True`.

---

## ⚙️ Environment Notes

For production deployment:
1. Set `DEBUG = False` in `settings.py`
2. Change `SECRET_KEY` to a random value
3. Configure `ALLOWED_HOSTS`
4. Set up a proper web server (Nginx + Gunicorn)
5. Use PostgreSQL instead of SQLite
6. Configure media file serving via Nginx or cloud storage (S3)

---

## 📄 License

MIT License — free to use and modify.
