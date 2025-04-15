import random
from django.core.management.base import BaseCommand

from ...models import *

class Command(BaseCommand):
    help = 'Seeds the database with mock data for testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting DB seeding..."))

        items_data = [
            {"name": "Burger", "description": "Classic beef burger", "price": 9.99},
            {"name": "Margherita Pizza", "description": "Cheese and tomato sauce", "price": 12.50},
            {"name": "Caesar Salad", "description": "Crispy lettuce, croutons, dressing", "price": 8.25},
            {"name": "French Fries", "description": "Golden fried potatoes", "price": 3.00},
            {"name": "Spaghetti Carbonara", "description": "Creamy sauce with bacon", "price": 10.75},
        ]

        menu_items = []
        for data in items_data:
            item, created = MenuItem.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'price': data['price'],
                    'is_available': True
                }
            )
            menu_items.append(item)
        self.stdout.write(self.style.SUCCESS(f"Created/updated {len(menu_items)} MenuItem objects."))

        for i in range(1, 6):
            Table.objects.get_or_create(number=i, defaults={'seats': 4})
        tables = Table.objects.all()
        self.stdout.write(self.style.SUCCESS(f"Created/updated {tables.count()} Table objects."))

        sessions = []
        for table in tables:
            session, _ = Session.objects.get_or_create(
                id=uuid.uuid4(),  # random UUID
                defaults={
                    'table': table,
                    'is_active': True,
                }
            )
            sessions.append(session)
        self.stdout.write(self.style.SUCCESS(f"Created {len(sessions)} Session objects."))


        orders = []
        for session in sessions:
            order, _ = Order.objects.get_or_create(
                session=session,
                defaults={
                    'is_approved': random.choice([True, False]),
                    'is_completed': False
                }
            )
            orders.append(order)
        self.stdout.write(self.style.SUCCESS(f"Created {len(orders)} Order objects."))


        requests_created = 0
        for order in orders:
            for _ in range(random.randint(1, 2)):
                req_type = random.choice([RequestType.INITIAL, RequestType.MENU_ITEM, RequestType.WAITER])
                CustomerRequest.objects.create(
                    order=order,
                    request_type=req_type,
                    note=f"Auto-generated request: {req_type}",
                    is_handled=random.choice([True, False])
                )
                requests_created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {requests_created} CustomerRequest objects."))


        items_created = 0
        all_items = list(MenuItem.objects.all())
        for order in orders:
            for _ in range(random.randint(1, 3)):
                menu_item = random.choice(all_items)
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=random.randint(1, 3)
                )
                items_created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {items_created} OrderItem objects."))

        self.stdout.write(self.style.SUCCESS("Seeding completed!"))