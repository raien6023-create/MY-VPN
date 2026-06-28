import os
from flask import Flask
import telebot
from telebot import types
from threading import Thread

# ۱. ساخت سرور وب برای رندر
app = Flask('')

@app.route('/')
def home():
    return "ربات با موفقیت روی وب‌سرویس رندر روشن است! 🚀"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ۲. تنظیمات ربات تلگرام
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# ⚠️ آیدی یا یوزرنیم کانال خودت رو اینجا وارد کن (حتما با @ شروع بشه)
CHANNEL_USERNAME = "@ConfigLand0" 

# تابع بررسی عضویت کاربر در کانال
def is_user_member(user_id):
    try:
        # وضعیت کاربر در کانال رو بررسی میکنه
        member_status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        # اگر وضعیت یکی از این‌ها باشه، یعنی عضو هست
        if member_status in ['member', 'creator', 'administrator']:
            return True
        return False
    except Exception as e:
        # اگر ربات ادمین کانال نباشه یا آیدی اشتباه باشه، این بخش اجرا میشه
        print(f"Error checking channel member: {e}")
        return False

# منوی اصلی ربات
def send_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("🛒 خرید کانفیگ")
    item2 = types.KeyboardButton("📞 پشتیبانی")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "به ربات فروش کانفیگ خوش آمدید! لطفا یک گزینه را انتخاب کنید:", reply_markup=markup)

# دستور /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # بررسی جوین اجباری
    if is_user_member(user_id):
        send_main_menu(message)
    else:
        # ساخت دکمه شیشه‌ای برای ورود به کانال و تایید عضویت
        markup = types.InlineKeyboardMarkup()
        btn_channel = types.InlineKeyboardButton("📢 ورود به کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
        btn_check = types.InlineKeyboardButton("✅ عضو شدم (تایید)", callback_data="check_join")
        markup.add(btn_channel)
        markup.add(btn_check)
        
        bot.send_message(message.chat.id, f"پیش از استفاده از ربات، باید در کانال ما عضو شوید:\n\n{CHANNEL_USERNAME}", reply_markup=markup)

# بررسی کلیک روی دکمه "عضو شدم"
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        # حذف پیام قبلی و فرستادن منوی اصلی
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_main_menu(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)

# پاسخ به دکمه‌های منوی اصلی (فقط در صورت عضویت)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    # اول مانیتور میکنه که وسط کار لفت نداده باشه
    if not is_user_member(user_id):
        send_welcome(message)
        return

    if message.text == "🛒 خرید کانفیگ":
        bot.send_message(message.chat.id, "جهت خرید کانفیگ و دریافت لیست قیمت‌ها به پشتیبانی پیام دهید.")
    elif message.text == "📞 پشتیبانی":
        bot.send_message(message.chat.id, "آیدی پشتیبانی: @Your_Support_ID")

def run_bot():
    bot.infinity_polling()

# ۳. اجرای هم‌زمان سرور وب و ربات
if __name__ == "__main__":
    t = Thread(target=run_web_server)
    t.start()
    run_bot()
