from celery import shared_task
from django.utils import timezone
from .models import KitchenEvents


@shared_task
def refresh_etas():
    from backend.utils.eta import simple_eta
    qs = KitchenEvents.objects.filter(status="queued")
    for ke in qs.select_related("order_item__menu_item"):
        new_eta = simple_eta(ke.order_item.menu_item)
        if abs((new_eta - ke.eta_finish_at).total_seconds()) > 30:
            ke.eta_finish_at = new_eta
            ke.save(update_fields=["eta_finish_at"])