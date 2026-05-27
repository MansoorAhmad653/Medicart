from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop.models import Category, Medicine

User = get_user_model()

CATEGORIES = [
    {'name': 'Pain Relief', 'icon': 'bi-bandaid'},
    {'name': 'Antibiotics', 'icon': 'bi-capsule'},
    {'name': 'Vitamins & Supplements', 'icon': 'bi-stars'},
    {'name': 'Allergy & Cold', 'icon': 'bi-thermometer-half'},
    {'name': 'Digestive Health', 'icon': 'bi-heart-pulse'},
    {'name': 'Skin Care', 'icon': 'bi-droplet'},
]

MEDICINES = [
    {
        'name': 'Panadol Extra 500mg',
        'category': 'Pain Relief',
        'price': 85.00,
        'stock_quantity': 150,
        'description': 'Panadol Extra provides effective relief from headaches, migraines, muscle aches, back pain, toothache, and cold & flu symptoms. Contains paracetamol 500mg.',
        'requires_prescription': False,
        'manufacturer': 'GSK Pakistan',
        'dosage': '1-2 tablets every 4-6 hours',
    },
    {
        'name': 'Augmentin 625mg',
        'category': 'Antibiotics',
        'price': 320.00,
        'stock_quantity': 60,
        'description': 'Augmentin is a broad-spectrum antibiotic containing amoxicillin and clavulanate potassium. Used to treat bacterial infections of the ear, lungs, skin, and urinary tract.',
        'requires_prescription': True,
        'manufacturer': 'GSK Pakistan',
        'dosage': '1 tablet twice daily for 7-10 days',
    },
    {
        'name': 'Centrum Multivitamin',
        'category': 'Vitamins & Supplements',
        'price': 1200.00,
        'stock_quantity': 80,
        'description': 'Centrum is a comprehensive daily multivitamin containing 23 essential vitamins and minerals to support overall health, energy, and immunity.',
        'requires_prescription': False,
        'manufacturer': 'Pfizer Pakistan',
        'dosage': '1 tablet daily with food',
    },
    {
        'name': 'Claritine 10mg',
        'category': 'Allergy & Cold',
        'price': 180.00,
        'stock_quantity': 45,
        'description': 'Claritine (loratadine) is a non-drowsy antihistamine that provides fast, effective relief from allergy symptoms including sneezing, itchy eyes, and runny nose.',
        'requires_prescription': False,
        'manufacturer': 'Bayer Pakistan',
        'dosage': '1 tablet once daily',
    },
    {
        'name': 'Brufen 400mg',
        'category': 'Pain Relief',
        'price': 95.00,
        'stock_quantity': 200,
        'description': 'Brufen (ibuprofen) is a non-steroidal anti-inflammatory drug (NSAID) used for the relief of mild to moderate pain, inflammation, and fever.',
        'requires_prescription': False,
        'manufacturer': 'Abbott Laboratories Pakistan',
        'dosage': '1-2 tablets three times daily with food',
    },
    {
        'name': 'Flagyl 400mg',
        'category': 'Antibiotics',
        'price': 140.00,
        'stock_quantity': 5,  # Low stock
        'description': 'Flagyl (metronidazole) is an antibiotic and antiprotozoal medication used to treat various bacterial and parasitic infections including stomach infections.',
        'requires_prescription': True,
        'manufacturer': 'Sanofi Pakistan',
        'dosage': '1 tablet three times daily for 7 days',
    },
    {
        'name': 'Vitamin D3 1000 IU',
        'category': 'Vitamins & Supplements',
        'price': 650.00,
        'stock_quantity': 120,
        'description': 'Vitamin D3 (cholecalciferol) supplement helps maintain healthy bones and teeth, supports immune function, and aids calcium absorption.',
        'requires_prescription': False,
        'manufacturer': 'Novartis Pakistan',
        'dosage': '1 capsule daily',
    },
    {
        'name': 'Gaviscon Advance',
        'category': 'Digestive Health',
        'price': 450.00,
        'stock_quantity': 90,
        'description': 'Gaviscon Advance provides fast, effective, and long-lasting relief from heartburn, acid reflux, and indigestion. Forms a raft to keep stomach acid in place.',
        'requires_prescription': False,
        'manufacturer': 'Reckitt Pakistan',
        'dosage': '2-4 tablets after meals and at bedtime',
    },
    {
        'name': 'Clarifoam EF Gel',
        'category': 'Skin Care',
        'price': 380.00,
        'stock_quantity': 35,
        'description': 'Clarifoam is a topical antibacterial gel for the treatment of acne vulgaris. Contains clindamycin phosphate which fights acne-causing bacteria.',
        'requires_prescription': True,
        'manufacturer': 'Ferozsons Laboratories',
        'dosage': 'Apply thin layer to affected area twice daily',
    },
    {
        'name': 'Nasivion Nasal Drops',
        'category': 'Allergy & Cold',
        'price': 120.00,
        'stock_quantity': 0,  # Out of stock
        'description': 'Nasivion nasal drops contain oxymetazoline hydrochloride, providing rapid relief from nasal congestion due to colds, sinusitis, and hay fever.',
        'requires_prescription': False,
        'manufacturer': 'Merck Pakistan',
        'dosage': '2-3 drops in each nostril, twice daily',
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample medicines, categories, and admin user'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n🌱 Seeding MediCart database...\n'))

        # Create Categories
        self.stdout.write('Creating categories...')
        category_map = {}
        for cat_data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data['icon']}
            )
            category_map[cat.name] = cat
            if created:
                self.stdout.write(f'  ✓ Created category: {cat.name}')
            else:
                self.stdout.write(f'  → Already exists: {cat.name}')

        # Create Medicines
        self.stdout.write('\nCreating medicines...')
        for med_data in MEDICINES:
            cat_name = med_data.pop('category')
            category = category_map.get(cat_name)
            med, created = Medicine.objects.get_or_create(
                name=med_data['name'],
                defaults={**med_data, 'category': category}
            )
            if created:
                self.stdout.write(f'  ✓ Created medicine: {med.name} (Rs. {med.price})')
            else:
                self.stdout.write(f'  → Already exists: {med.name}')

        # Create Admin User
        self.stdout.write('\nCreating admin user...')
        admin_email = 'admin@medicart.pk'
        if not User.objects.filter(email=admin_email).exists():
            admin = User.objects.create_superuser(
                username='admin',
                email=admin_email,
                password='admin123',
                name='MediCart Admin',
                role='admin',
                phone='+92 300 0000000',
                address='Rawalpindi, Punjab, Pakistan',
            )
            self.stdout.write(f'  ✓ Created admin user: {admin_email}')
        else:
            self.stdout.write(f'  → Admin already exists: {admin_email}')

        # Summary
        self.stdout.write(self.style.SUCCESS('\n✅ Seed completed successfully!\n'))
        self.stdout.write(self.style.WARNING('Admin credentials:'))
        self.stdout.write(f'  Email:    admin@medicart.pk')
        self.stdout.write(f'  Password: admin123')
        self.stdout.write(f'\n  Categories: {Category.objects.count()}')
        self.stdout.write(f'  Medicines:  {Medicine.objects.count()}')
        self.stdout.write('\nRun: python manage.py runserver\n')
