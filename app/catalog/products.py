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
    "car-seat-cushion": {
        "sku": "MP-CSCUSH7K2M9Q",
        "arabic_name": "مسند ظهر شبكي — راحة ووضعية صحيحة",
    },
    "prostration-chair": {
        "sku": "MP-5W1QBKIWM4SA",
        "arabic_name": "كرسي السجود — راحة في الصلاة بدون مشقة",
    },
    "car-comfort-set": {
        "sku": "MP-CCSET9P3L7VR",
        "arabic_name": "طقم راحة السيارة — مخدة رقبة + مسند قطني",
    },
    "mens-hair-styler": {
        "sku": "MP-MHSTYLE5Q8KD",
        "arabic_name": "فرشاة تمليس للرجال — شعر ولحية بضغطة",
    },
    "wireless-car-charger": {
        "sku": "MP-E33HQGSNW2SK",
        "arabic_name": "شاحن سيارة لاسلكي — تثبيت وشحن بيد واحدة",
    },
    "indoor-wall-night-light": {
        "sku": "MP-NVBT8SWPQKG7",
        "arabic_name": "مصباح حائط ليلي خشبي — إضاءة دافئة وأنيقة",
    },
    "automatic-foam-dispenser": {
        "sku": "MP-XPFILYWFPJI5",
        "arabic_name": "موزع الصابون الرغوي الأوتوماتيكي — نظافة بدون لمس",
    },
    "disposable-toilet-brush-set": {
    "sku": "MP-UGE66ZRAZOCG",
    "arabic_name": "فرشاة تنظيف الحمام الكهربائية",
},
}


def catalog_entry(product_id: str) -> dict[str, str] | None:
    return PRODUCT_CATALOG.get(product_id)
