"""
Filter and ordering logic for offer list (GET /api/offers/).
"""

from django.db.models import Q
from rest_framework.exceptions import ValidationError


VALID_ORDERING = ('updated_at', 'min_price', '-updated_at', '-min_price')
DEFAULT_ORDERING = 'updated_at'


def apply_creator_filter(queryset, value):
    """Filter by creator_id; value must be non-empty string. Raises ValidationError if invalid."""
    if not value:
        return queryset
    try:
        return queryset.filter(user_id=int(value))
    except ValueError:
        raise ValidationError({'creator_id': 'Must be an integer.'})


def apply_min_price_filter(queryset, value):
    """Filter by min_price (annotated min_p). Raises ValidationError if invalid."""
    if not value:
        return queryset
    try:
        return queryset.filter(min_p__gte=float(value))
    except ValueError:
        raise ValidationError({'min_price': 'Must be a number.'})


def apply_max_delivery_time_filter(queryset, value):
    """Filter by max_delivery_time (annotated min_delivery). Raises ValidationError if invalid."""
    if not value:
        return queryset
    try:
        return queryset.filter(min_delivery__lte=int(value))
    except ValueError:
        raise ValidationError({'max_delivery_time': 'Must be an integer.'})


def apply_search_filter(queryset, value):
    """Filter by search term in title or description."""
    if not value:
        return queryset
    return queryset.filter(
        Q(title__icontains=value) | Q(description__icontains=value),
    )


def apply_ordering(queryset, value):
    """Apply ordering; falls back to DEFAULT_ORDERING if invalid."""
    ordering = (value or '').strip() or DEFAULT_ORDERING
    if ordering not in VALID_ORDERING:
        ordering = DEFAULT_ORDERING
    if ordering == 'min_price':
        return queryset.order_by('min_p')
    if ordering == '-min_price':
        return queryset.order_by('-min_p')
    return queryset.order_by(ordering)


def apply_offer_list_filters(queryset, query_params):
    """
    Apply all list filters and ordering to an annotated offer queryset.
    query_params: request.query_params or equivalent dict-like.
    Returns filtered queryset; raises ValidationError on invalid param values.
    """
    params = query_params
    qs = apply_creator_filter(queryset, (params.get('creator_id') or '').strip())
    qs = apply_min_price_filter(qs, (params.get('min_price') or '').strip())
    qs = apply_max_delivery_time_filter(
        qs, (params.get('max_delivery_time') or '').strip(),
    )
    qs = apply_search_filter(qs, (params.get('search') or '').strip())
    qs = apply_ordering(qs, (params.get('ordering') or '').strip())
    return qs
