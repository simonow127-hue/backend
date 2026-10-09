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

    country_code = (
        getattr(order, "phone_country", None)
        or getattr(order, "country", None)
        or "SA"
    )

    country = country_names.get(
        country_code,
        country_code or "Saudi Arabia",
    )

    currency = getattr(order, "currency", None) or "SAR"

    total_price = getattr(order, "total_price", None)
    if total_price is None:
        total_price = getattr(order, "total_mad", 0)

    return {
        "date": _format_sheet_date(order.created_at),
        "orderid": order.order_code or "",
        "country": country,
        "country_code": country_code,
        "name": order.customer_name or "",
        "phone": format_sheet_phone(
            order.phone_raw,
            order.phone_e164,
            country_code,
        ),
        "phone_e164": order.phone_e164 or "",
        "product": product,
        "sku": sku,
        "quantity": quantity,
        "total_price": format_sheet_price(
            total_price,
            currency,
        ),
        "currency": currency,
        "status": "",
    }
