from django.conf import settings
from django.db import models


class Offer(models.Model):
    """Offer header; min_price and min_delivery_time derived from details."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers',
    )
    title = models.CharField(max_length=255)
    image = models.CharField(max_length=500, blank=True, default='')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class OfferDetail(models.Model):
    """Single option within an offer (price, delivery time, features, etc.)."""

    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='details',
    )
    title = models.CharField(max_length=255, default='')
    revisions = models.PositiveIntegerField(default=0)
    delivery_time = models.PositiveIntegerField(
        help_text='Delivery time in days',
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(
        default=list,
        help_text='List of feature strings',
    )
    offer_type = models.CharField(max_length=50, default='')

    class Meta:
        verbose_name = 'Offer detail'
        verbose_name_plural = 'Offer details'
        ordering = ['price']

    def __str__(self):
        return f"{self.offer.title} – {self.title}"
