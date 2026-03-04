from django.conf import settings
from django.db import models


class Order(models.Model):
    """
    Order placed by a customer with a business (offer owner).
    Snapshot fields store offer-detail data at order time.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders_as_customer',
    )
    business_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders_as_business',
    )
    title = models.CharField(max_length=255)
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
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} – {self.title}"
