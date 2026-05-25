"""Product catalog for orders and Google Sheets (keep in sync with frontend/lib/products.ts)."""

PRODUCT_CATALOG: dict[str, dict[str, str]] = {
    "jadr": {
        "sku": "RIADS-JDR-8841",
        "arabic_name": "جدر — زيت تطويل الشعر الفاخر لنمو أكثف وأقوى",
    },
    "nour": {
        "sku": "RIADS-NOR-3392",
        "arabic_name": "نور — كريم الرتينول لتجديد البشرة وتقليل التجاعيد",
    },
    "naqaa": {
        "sku": "RIADS-NAQ-7105",
        "arabic_name": "نقاء — كريم مزيل العرق الطبيعي للحماية اليومية من الروائح",
    },
}


def catalog_entry(product_id: str) -> dict[str, str] | None:
    return PRODUCT_CATALOG.get(product_id)
