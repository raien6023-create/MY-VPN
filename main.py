import os
from flask import Flask
import telebot
from threading import Thread

# ۱. ساخت سرور وب برای رندر
app = Flask('')

@app.route('/')
def home():
    return "ربات با موفقیت روی وب‌سرویس رندر روشن است! 🚀"

def run_web_server():
    # رندر پورت رو در متغیر محیطی PORT قرار میده، اگر نبود روی ۸۰۸۰ اجرا میشه
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ۲. تنظیمات ربات تلگرام
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! ربات فروش کانفیگ شما روی وب‌سرویس رندر فعال است.")

def run_bot():
    bot.infinity_polling()

# ۳. اجرای هم‌زمان سرور وب و ربات
if __name__ == "__main__":
    # سرور وب رو در یک رشته (Thread) جداگانه روشن می‌کنیم
    t = Thread(target=run_web_server)
    t.start()
    
    # ربات رو روشن می‌کنیم
    run_bot()
