```python
def build_sheet_payload(order) -> dict:
    items = (
        order.items
        if isinstance(order.items, list)
        else []
    )

    product, sku, quantity = _line_fields(items)

    country_names = {
        "SA": "Saudi Arabia",
        "AE": "United Arab Emirates",
        "MA": "Morocco",
    }

    country = country_names.get(
        order.phone_country,
        order.phone_country or "Saudi Arabia",
    )

    currency = order.currency or "SAR"

    return {
        "date": _format_sheet_date(order.created_at),
        "orderid": order.order_code or "",

        # Dynamic country
        "country": country,

        "name": order.customer_name or "",

        "phone": format_sheet_phone(
            order.phone_raw,
            order.phone_e164,
        ),

        "phone_e164": order.phone_e164 or "",

        "product": product,
        "sku": sku,
        "quantity": quantity,

        "total_price": format_sheet_price(
            order.total_mad,
            currency,
        ),

        "currency": currency,
        "status": "",
    }
```
