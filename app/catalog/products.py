"""Product catalog for orders and Google Sheets (keep in sync with frontend/lib/products.ts)."""

PRODUCT_CATALOG: dict[str, dict[str, str]] = {
    "car-gap-filler": {
        "sku": "MP-Z3SJMALO3RPR",
        "arabic_name": "حاجز فجوة المقعد — ودّع ضياع أغراضك",
    },
    "car-phone-holder": {
        "sku": "MP-D2FTXP9LUJ7Y",
        "arabic_name": "حامل جوال مغناطيسي للسيارة — ثبات ووضوح",
    },
    "neck-fan": {
        "sku": "MP-UFVILGUCUBKG",
        "arabic_name": "مروحة الرقبة المحمولة — برودة وين ما كنت",
    },
    "quran-speaker": {
        "sku": "MP-GTW9WHZOJ3NL",
        "arabic_name": "مكبر قرآن للحائط — أجواء إيمانية في بيتك",
    },
    "desk-lamp": {
        "sku": "MP-ZSWU29NOQK1F",
        "arabic_name": "مصباح مكتب ذكي — إضاءة وشحن لاسلكي",
    },
    "electric-chopper": {
        "sku": "MP-WH8QUFVD3TEY",
        "arabic_name": "فرامة خضار كهربائية — تجهيز سريع بدون تعب",
    },
    "perfume-intense": {
        "sku": "MP-KVJEQYF3EWOC",
        "arabic_name": "عطر قصة Pink & Rose — أنوثة وفخامة في رشّة",
    },
    "black-sheila": {
        "sku": "MP-FMER4W5JZBAG",
        "arabic_name": "شيلة سوداء فاخرة — إطلالة أنيقة كل يوم",
    },
}


def catalog_entry(product_id: str) -> dict[str, str] | None:
    return PRODUCT_CATALOG.get(product_id)
