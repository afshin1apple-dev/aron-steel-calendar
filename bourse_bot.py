import os
import requests

# =========================================================
# تنظیمات
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


# =========================================================
# ارسال پیام به کانال
# =========================================================

def send_message(text):

    try:

        response = requests.post(
            f"{TELEGRAM_URL}/sendMessage",
            data={
                "chat_id": CHANNEL_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            },
            timeout=30
        )

        print("Telegram:", response.status_code)

        if not response.ok:
            print(response.text)

        return response.ok

    except Exception as e:

        print("Telegram error:", e)

        return False


# =========================================================
# تست ربات
# =========================================================

def main():

    print("========================================")
    print("Starting Arvand Aron Steel Bourse Bot...")
    print("========================================")

    test_message = """
🏭 <b>ربات بورس کالا</b>

✅ ربات با موفقیت اجرا شد.

📊 سیستم دریافت اطلاعات عرضه و معاملات بورس کالا در حال آماده‌سازی است.

━━━━━━━━━━━━━━
🏭 آروند آرون استیل
👤 مدیریت: افشین آورزمانی
📞 021-22122239
🆔 @arvand_aron_steel
"""

    send_message(test_message)

    print("Bot finished.")


if __name__ == "__main__":
    main()