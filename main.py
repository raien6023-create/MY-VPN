import os
import json
from flask import Flask
import telebot
from telebot import types
from threading import Thread

# ۱. ساخت سرور وب برای رندر (Keep-Alive)
app = Flask('')

@app.route('/')
def home():
    return "ربات فروش کانفیگ با موفقیت روی رندر روشن است! 🚀"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ۲. تنظیمات ربات تلگرام
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# ⚠️ اطلاعات خودت رو اینجا ست کن
CHANNEL_USERNAME = "@ConfigLand0"  # یوزرنیم کانال با @
ADMIN_ID = 7267007753  # آیدی عددی تلگرام خودت (به صورت عدد)
CARD_NUMBER = "6037997275603489"
CARD_NAME = "رایین ایمانی"

# فایل‌های ذخیره اطلاعات کاربران (دیتابیس ساده JSON)
DB_USERS = "users_db.json"

def load_db():
    if os.path.exists(DB_USERS):
        try:
            with open(DB_USERS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    else:
        with open(DB_USERS, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}

def save_db(data):
    with open(DB_USERS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# مقداردهی اولیه دیتابیس برای کاربر جدید
def init_user(user_id, referrer_id=None):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "days_left": 0,
            "referrals": 0,
            "referred_by": referrer_id,
            "claimed_rewards": 0
        }
        if referrer_id and str(referrer_id) in db:
            db[str(referrer_id)]["referrals"] += 1
            try:
                bot.send_message(referrer_id, "🎉 یک نفر با لینک شما وارد ربات و کانال شد! به تعداد دعوت‌های شما اضافه شد.")
            except:
                pass
        save_db(db)

# تابع بررسی عضویت اجباری در کانال
def is_user_member(user_id):
    try:
        member_status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        if member_status in ['member', 'creator', 'administrator']:
            return True
        return False
    except Exception as e:
        print(f"Error checking channel member: {e}")
        return False

# ساخت کیبورد منوی اصلی
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🛒 خرید کانفیگ"), types.KeyboardButton("🎁 تست ۱ روزه"))
    markup.add(types.KeyboardButton("📊 وضعیت کانفیگ"), types.KeyboardButton("👥 زیرمجموعه‌گیری"))
    markup.add(types.KeyboardButton("📞 پشتیبانی"))
    return markup

# ساخت کیبورد دکمه بازگشت
def get_back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    return markup

# دستور /start (پشتیبانی از لینک رفرال)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id == user_id:
            referrer_id = None

    if is_user_member(user_id):
        init_user(user_id, referrer_id)
        bot.send_message(message.chat.id, "به ربات فروش کانفیگ خوش آمدید! لطفا یک گزینه را انتخاب کنید:", reply_markup=get_main_menu())
    else:
        markup = types.InlineKeyboardMarkup()
        btn_channel = types.InlineKeyboardButton("📢 ورود به کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
        ref_data = f"check_{referrer_id}" if referrer_id else "check_none"
        btn_check = types.InlineKeyboardButton("✅ عضو شدم (تایید)", callback_data=ref_data)
        markup.add(btn_channel)
        markup.add(btn_check)
        
        bot.send_message(message.chat.id, f"پیش از استفاده از ربات، باید در کانال ما عضو شوید:\n\n{CHANNEL_USERNAME}", reply_markup=markup)

# بررسی کلیک روی دکمه "عضو شدم"
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def check_join_callback(call):
    user_id = call.from_user.id
    ref_part = call.data.split("_")[1]
    referrer_id = int(ref_part) if ref_part != "none" else None
    
    if is_user_member(user_id):
        init_user(user_id, referrer_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "عضویت شما تایید شد! به منوی اصلی خوش آمدید:", reply_markup=get_main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)

# پاسخ به پیام‌های متنی و دکمه‌ها
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def handle_all_messages(message):
    user_id = message.from_user.id
    
    # ادمین ممکن است بخواهد روی پیامی ریپلای کند، در این صورت عضویت اجباری برای ادمین نادیده گرفته می‌شود
    if message.from_user.id != ADMIN_ID and not is_user_member(user_id):
        send_welcome(message)
        return

    db = load_db()
    uid = str(user_id)
    if uid not in db:
        init_user(user_id)
        db = load_db()

    # سیستم پاسخ هوشمند ادمین (ریپلای روی پیام‌های اعلان خرید، تست یا هدیه رفرال)
    if message.from_user.id == ADMIN_ID and message.reply_to_message:
        reply_text = message.reply_to_message.text
        # اگر ادمین روی عکس فیش ریپلای کند، پیام متنی ندارد؛ پس متن پیام قبلی (کپشن یا مسیج بالای عکس) را چک می‌کنیم
        if not reply_text and message.reply_to_message.caption:
            reply_text = message.reply_to_message.caption
            
        if reply_text and "🆔 آیدی عددی:" in reply_text:
            try:
                # استخراج آیدی عددی کاربر از متن اعلان
                target_user_id = int(reply_text.split("🆔 آیدی عددی:")[1].split("\n")[0].strip().replace('`', ''))
                
                # ارسال کانفیگ فرستاده شده توسط ادمین برای کاربر
                bot.send_message(target_user_id, f"🚀 **کانفیگ شما توسط مدیریت صادر شد:**\n\n`{message.text}`", parse_mode="Markdown")
                bot.reply_to(message, f"✅ کانفیگ با موفقیت برای کاربر `{target_user_id}` ارسال شد.")
            except Exception as e:
                bot.reply_to(message, f"❌ خطا در ارسال پیام به کاربر: {e}")
        return

    if message.text == "🔙 بازگشت به منوی اصلی":
        bot.send_message(message.chat.id, "به منوی اصلی برگشتید:", reply_markup=get_main_menu())
        return

    if message.text == "🛒 خرید کانفیگ":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("20 گیگ - 100 هزار تومان", callback_data="buy_20gb"),
            types.InlineKeyboardButton("40 گیگ - 200 هزار تومان", callback_data="buy_40gb"),
            types.InlineKeyboardButton("60 گیگ - 300 هزار تومان", callback_data="buy_60gb"),
            types.InlineKeyboardButton("80 گیگ - 400 هزار تومان", callback_data="buy_80gb"),
            types.InlineKeyboardButton("نامحدود - 600 هزار تومان", callback_data="buy_unlimited")
        )
        bot.send_message(message.chat.id, "لطفا تعرفه مورد نظر خود را انتخاب کنید:", reply_markup=markup)
        return

    if message.text == "🎁 تست ۱ روزه":
        bot.send_message(message.chat.id, "⏳ درخواست تست شما ثبت شد و برای ادمین ارسال گردید. به زودی کانفیگ برای شما ارسال می‌شود.")
        bot.send_message(ADMIN_ID, f"🔔 **درخواست تست رایگان**\n\n👤 کاربر: {message.from_user.first_name}\n🆔 آیدی عددی: `{user_id}`\nیوزرنیم: @{message.from_user.username or 'ندارد'}\n\n👉 جهت ارسال کانفیگ به این کاربر، روی همین پیام ریپلای کنید.")
        return

    if message.text == "📊 وضعیت کانفیگ":
        days = db[uid].get("days_left", 0)
        if days > 0:
            bot.send_message(message.chat.id, f"✅ اشتراک شما فعال است.\n⏳ مدت زمان باقی‌مانده: {days} روز")
        else:
            bot.send_message(message.chat.id, "❌ شما در حال حاضر اکانت یا اشتراک فعالی ندارید.")
        return

    if message.text == "👥 زیرمجموعه‌گیری":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        refs = db[uid].get("referrals", 0)
        
        markup = types.InlineKeyboardMarkup()
        if refs >= 5:
            markup.add(types.InlineKeyboardButton("🎁 دریافت هدیه (۱۰ گیگ)", callback_data="claim_reward"))
            
        msg = f"👥 **سیستم زیرمجموعه‌گیری**\n\nبا دعوت هر ۵ نفر به ربات، ۱۰ گیگابایت کانفیگ هدیه بگیرید!\n\n🔗 لینک اختصاصی شما:\n`{ref_link}`\n\n📊 تعداد دعوت‌های شما تاکنون: {refs} نفر"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)
        return

    if message.text == "📞 پشتیبانی":
        bot.send_message(message.chat.id, f"جهت ارتباط با پشتیبانی، پاسخ به سوالات یا پیگیری خرید با آیدی زیر در ارتباط باشید:\n\n➡️ @AmirTA28")
        return

    # دریافت فیش واریزی (عکس)
    if message.content_type == 'photo':
        bot.send_message(message.chat.id, "✅ فیش واریزی شما دریافت
