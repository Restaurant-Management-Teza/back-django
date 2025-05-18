# models.py
import uuid

from django.db import models


class MenuItem(models.Model):
    public_id      = models.UUIDField(null=True)
    cook_time_min  = models.PositiveIntegerField(null=True)   # <- changed
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    ingredients = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# models.py
class Zone(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    seats = models.PositiveIntegerField(default=4)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='tables', null=True, blank=True)

    def __str__(self):
        return f"Table {self.number}"


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="sessions")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Session {self.id} for Table {self.table.number}"

class Order(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.pk} for Session {self.session.id}"


class RequestType(models.TextChoices):
    INITIAL = 'initial', 'Initial'
    MENU_ITEM = 'menu_item', 'Menu Item'
    PAYMENT = 'payment', 'Payment'
    WAITER = 'waiter', 'Waiter'


class CustomerRequest(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="requests")
    request_type = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_handled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.request_type} request for Order {self.order.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

# backend/models.py  (new file or extend existing)
class KitchenEvent(models.Model):
    """
    One row per dish actually cooked.
    We’ll learn ETA from Δt = finished_at – started_at.
    """
    order_item  = models.OneToOneField('OrderItem', on_delete=models.CASCADE)
    started_at  = models.DateTimeField(auto_now_add=True)            # set when ticket prints
    finished_at = models.DateTimeField(null=True, blank=True)        # set when chef clicks "ready"

class KitchenEvents(models.Model):
    """
    One row per dish that the kitchen must prepare.
    """
    EVENT_CHOICES = [
        ("queued", "Queued"),          # just added
        ("cooking", "Cooking"),        # chef has started
        ("ready",   "Ready"),          # finished
    ]

    order_item        = models.ForeignKey("OrderItem", on_delete=models.CASCADE,
                                          related_name="kitchen_events")
    status            = models.CharField(max_length=10, choices=EVENT_CHOICES, default="queued")
    queued_at         = models.DateTimeField(auto_now_add=True)
    eta_finish_at     = models.DateTimeField()            # <- filled by estimator
    started_at        = models.DateTimeField(null=True, blank=True)
    finished_at       = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["eta_finish_at"]