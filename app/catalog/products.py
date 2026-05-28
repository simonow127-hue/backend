"""Product catalog for orders and Google Sheets (keep in sync with frontend/lib/products.ts)."""

PRODUCT_CATALOG: dict[str, dict[str, str]] = {
    "jadr": {
        "sku": "growth-hair",
        "arabic_name": "جدر — زيت تطويل الشعر الفاخر لنمو أكثف وأقوى",
    },
    "nour": {
        "sku": "creme-retanoltube",
        "arabic_name": "نور — كريم الرتينول لتجديد البشرة وتقليل التجاعيد",
    },
    "naqaa": {
        "sku": "deodorant",
        "arabic_name": "نقاء — كريم مزيل العرق الطبيعي للحماية اليومية من الروائح",
    },
}


def catalog_entry(product_id: str) -> dict[str, str] | None:
    return PRODUCT_CATALOG.get(product_id)
