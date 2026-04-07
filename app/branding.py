"""Product name, studio metadata, version (non-translatable constants). UI strings: app/i18n."""

APP_NAME = "Autoclicker"
APP_VERSION = "1.0.0"

STUDIO_AUTHOR = "Flowaxy Solutions"
STUDIO_EMAIL = "contact@flowaxy.com"
STUDIO_URL = "https://flowaxy.com"

BRAND_TELEGRAM_URL = "https://t.me/iteffa"
BRAND_WHATSAPP_URL = "https://wa.me/380966349498"

# Заголовок вікна: «назва продукту — бренд» (тире U+2014)
WINDOW_TITLE_SUFFIX = "Flowaxy Software"


def format_window_title(product_subtitle: str) -> str:
    return f"{product_subtitle} — {WINDOW_TITLE_SUFFIX}"
