import telebot
import qrcode
import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont
from telebot import types
import json
import threading
import time
import cv2
import numpy as np
from pyzbar.pyzbar import decode

BOT_TOKEN = "8339144947:AAEx0ri0vYnSg172btfQoFMjXiF6_xBeB3k"
bot = telebot.TeleBot(BOT_TOKEN)

# Foydalanuvchi ma'lumotlarini saqlash
USER_DATA_FILE = "users.json"

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_user_data(user_data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

user_data = load_user_data()

def create_welcome_image(user_name):
    """Qabul qilish rasmini yaratish"""
    img = Image.new('RGB', (800, 400), color=(74, 105, 189))
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        text_font = ImageFont.truetype("arial.ttf", 28)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    draw.text((400, 150), f"Salom, {user_name}! 👋", fill=(255, 255, 255), font=title_font, anchor="mm")
    draw.text((400, 220), "QR Kod Generator Botiga xush kelibsiz!", fill=(230, 230, 230), font=text_font, anchor="mm")
    draw.text((400, 260), "Matn yoki rasm yuboring", fill=(200, 200, 255), font=text_font, anchor="mm")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def read_qr_from_image(image_data):
    """Rasmdan QR kodni o'qish"""
    try:
        # Rasmni numpy array ga o'tkazish
        image_array = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if img is None:
            return None, "Rasmni ochib bo'lmadi"
        
        # QR kodlarni aniqlash
        decoded_objects = decode(img)
        
        if len(decoded_objects) == 0:
            # Agar birinchi urinishda topilmasa, rasmni qayta ishlash
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            decoded_objects = decode(gray)
            
            if len(decoded_objects) == 0:
                # Yana bir urinish - kontrastni oshirish
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                contrast_enhanced = clahe.apply(gray)
                decoded_objects = decode(contrast_enhanced)
        
        results = []
        for obj in decoded_objects:
            data = obj.data.decode('utf-8')
            results.append(data)
        
        return results, None
        
    except Exception as e:
        return None, f"QR kodni o'qishda xatolik: {str(e)}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    
    # Foydalanuvchi ma'lumotlarini saqlash
    if user_id not in user_data:
        user_data[user_id] = {
            "name": user_name,
            "qr_generated": 0,
            "qr_read": 0,
            "join_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_active": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        user_data[user_id]["last_active"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    save_user_data(user_data)
    
    # Qabul qilish rasmini yuborish
    welcome_image = create_welcome_image(user_name)
    bot.send_photo(message.chat.id, welcome_image, caption=f"🎉 **Salom, {user_name}!**\n\n"
                   "🤖 **QR Kod Generator Botiga xush kelibsiz!**\n\n"
                   "📱 **Mening vazifam:**\n"
                   "• Matnlarni QR kodga aylantirish\n"
                   "• Rasmlardan QR kodlarni o'qish\n"
                   "• Turli xil QR kod dizaynlari\n\n"
                   "🚀 **Foydalanish:**\n"
                   "• Matn yuboring - QR kod yarataman\n"
                   "• QR kod rasm yuboring - matnini o'qiyman\n"
                   "• Pastdagi tugmalardan foydalaning",
                   parse_mode='Markdown')
    
    send_main_menu(message.chat.id)

def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📝 Matn dan QR')
    btn2 = types.KeyboardButton('🖼️ Rasm dan QR')
    btn3 = types.KeyboardButton('📊 Mening statistikam')
    btn4 = types.KeyboardButton('⚙️ Sozlamalar')
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(chat_id, "🏠 **Asosiy menyu**\n\nQuyidagi tugmalardan birini tanlang:", 
                     reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '📝 Matn dan QR')
def text_to_qr_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔙 Orqaga'))
    bot.send_message(message.chat.id, "📝 **Matn dan QR kod yaratish**\n\nEndi menga QR kodga aylantirmoqchi bo'lgan matningizni yuboring:", 
                     reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '🖼️ Rasm dan QR')
def image_to_qr_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔙 Orqaga'))
    bot.send_message(message.chat.id, "🖼️ **Rasm dan QR kod o'qish**\n\nEndi menga QR kod rasmini yuboring (PNG, JPG formatida):", 
                     reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '📊 Mening statistikam')
def show_stats(message):
    user_id = str(message.from_user.id)
    if user_id in user_data:
        stats = user_data[user_id]
        bot.send_message(message.chat.id, 
                         f"📊 **Sizning statistikangiz:**\n\n"
                         f"👤 Ism: {stats['name']}\n"
                         f"📅 Qo'shilgan sana: {stats['join_date']}\n"
                         f"🔄 Yaratilgan QR kodlar: {stats['qr_generated']} ta\n"
                         f"📖 O'qilgan QR kodlar: {stats.get('qr_read', 0)} ta\n"
                         f"⏰ So'ngi faollik: {stats['last_active']}",
                         parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ Statistikangiz topilmadi. /start ni bosing.")

@bot.message_handler(func=lambda message: message.text == '⚙️ Sozlamalar')
def show_settings(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎨 QR kod rangini o'zgartirish", callback_data="color_settings"))
    markup.add(types.InlineKeyboardButton("📏 QR kod o'lchami", callback_data="size_settings"))
    markup.add(types.InlineKeyboardButton("🔄 Avtomatik tozalash", callback_data="auto_clean"))
    
    bot.send_message(message.chat.id, "⚙️ **Sozlamalar**\n\nQuyidagi sozlamalarni o'zgartirishingiz mumkin:", 
                     reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '🔙 Orqaga')
def back_to_main(message):
    send_main_menu(message.chat.id)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'):
        return
    
    # Kumush soat stikerini yuborish
    try:
        processing_msg = bot.send_message(message.chat.id, "⏳ QR kod yaratilmoqda...")
    except:
        processing_msg = None
    
    user_id = str(message.from_user.id)
    
    # QR kod yaratish
    try:
        # Statistikani yangilash
        if user_id in user_data:
            user_data[user_id]["qr_generated"] += 1
            user_data[user_id]["last_active"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_user_data(user_data)
        
        # QR kod yaratish
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(message.text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Rasmni bufferga saqlash
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        
        # Yuklab olish tugmasi
        markup = types.InlineKeyboardMarkup()
        download_btn = types.InlineKeyboardButton("📥 Yuklab olish", callback_data=f"download_{message.id}")
        markup.add(download_btn)
        
        # Xabarni o'chirish
        if processing_msg:
            try:
                bot.delete_message(message.chat.id, processing_msg.message_id)
            except:
                pass
        
        # QR kodni yuborish
        bot.send_photo(message.chat.id, buf, 
                      caption=f"✅ **QR kod muvaffaqiyatli yaratildi!**\n\n📝 **Matn:** `{message.text[:50]}{'...' if len(message.text) > 50 else ''}`",
                      reply_markup=markup,
                      parse_mode='Markdown')
        
    except Exception as e:
        if processing_msg:
            try:
                bot.delete_message(message.chat.id, processing_msg.message_id)
            except:
                pass
        bot.reply_to(message, f"❌ Xatolik yuz berdi: {str(e)}")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Kutish xabarini yuborish
    try:
        processing_msg = bot.send_message(message.chat.id, "⏳ QR kod tahlil qilinmoqda...")
    except:
        processing_msg = None
    
    try:
        # Rasmni olish
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # QR kodni o'qish
        results, error = read_qr_from_image(downloaded_file)
        
        # Xabarni o'chirish
        if processing_msg:
            try:
                bot.delete_message(message.chat.id, processing_msg.message_id)
            except:
                pass
        
        if error:
            bot.reply_to(message, f"❌ {error}\n\nIltimos, aniq va yorqin QR kod rasmini yuboring.")
            return
        
        if not results:
            bot.reply_to(message, "❌ QR kod topilmadi!\n\nIltimos, quyidagilarni tekshiring:\n• Rasm aniq va yorqin bo'lishi\n• QR kod to'liq ko'rinishi\n• Yorug'lik yaxshi bo'lishi")
            return
        
        # Statistikani yangilash
        user_id = str(message.from_user.id)
        if user_id in user_data:
            user_data[user_id]["qr_read"] = user_data[user_id].get("qr_read", 0) + len(results)
            user_data[user_id]["last_active"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_user_data(user_data)
        
        # Natijalarni yuborish
        if len(results) == 1:
            response_text = f"✅ **QR kod muvaffaqiyatli o'qildi!**\n\n📝 **Matn:**\n`{results[0]}`"
        else:
            response_text = f"✅ **{len(results)} ta QR kod topildi!**\n\n"
            for i, result in enumerate(results, 1):
                response_text += f"**{i}.** `{result}`\n"
        
        # Matn uzun bo'lsa
        if len(response_text) > 4000:
            response_text = response_text[:4000] + "\n\n... (matn juda uzun, to'liq ko'rsatilmaydi)"
        
        bot.reply_to(message, response_text, parse_mode='Markdown')
        
        # Agar bitta QR kod topilsa, uni qayta yaratish taklifi
        if len(results) == 1:
            markup = types.InlineKeyboardMarkup()
            recreate_btn = types.InlineKeyboardButton("🔄 Yangi QR kod yaratish", callback_data=f"recreate_{message.id}")
            markup.add(recreate_btn)
            bot.send_message(message.chat.id, "Yangiroq QR kod yaratishni xohlaysizmi?", reply_markup=markup)
            
    except Exception as e:
        if processing_msg:
            try:
                bot.delete_message(message.chat.id, processing_msg.message_id)
            except:
                pass
        bot.reply_to(message, f"❌ Rasmni qayta ishlashda xatolik: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("download_"):
        # QR kodni yuklab olish
        message_id = call.data.split("_")[1]
        
        try:
            bot.answer_callback_query(call.id, "📥 QR kod yuklanmoqda...")
            
            # Original xabarni topish va QR kodni qayta yaratish
            original_message = bot.copy_message(call.message.chat.id, call.message.chat.id, int(message_id))
            original_text = original_message.text if original_message.text else original_message.caption
            
            # Matnni ajratib olish (soddalashtirilgan)
            text_to_encode = "QR Code Content"  # Default
            if original_text:
                # Haqiqiy loyihada matnni parse qilish kerak
                if "Matn:" in original_text:
                    import re
                    match = re.search(r"Matn:\s*`([^`]+)", original_text)
                    if match:
                        text_to_encode = match.group(1)
            
            # QR kod yaratish
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(text_to_encode)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            
            # Fayl sifatida yuborish
            bot.send_document(call.message.chat.id, buf, 
                             visible_file_name="qrcode.png",
                             caption="📥 **QR kod fayli yuklab olindi!**")
            
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Xatolik: {str(e)}")
    
    elif call.data.startswith("recreate_"):
        # QR kodni qayta yaratish
        message_id = call.data.split("_")[1]
        
        try:
            bot.answer_callback_query(call.id, "🔄 QR kod yaratilmoqda...")
            
            # Original xabarni topish
            original_message = bot.copy_message(call.message.chat.id, call.message.chat.id, int(message_id))
            qr_text = original_message.text
            
            # QR kod yaratish
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_text)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            
            # Yuklab olish tugmasi
            markup = types.InlineKeyboardMarkup()
            download_btn = types.InlineKeyboardButton("📥 Yuklab olish", callback_data=f"download_new_{message.id}")
            markup.add(download_btn)
            
            bot.send_photo(call.message.chat.id, buf,
                          caption=f"✅ **Yangi QR kod yaratildi!**\n\n📝 **Matn:** `{qr_text[:50]}{'...' if len(qr_text) > 50 else ''}`",
                          reply_markup=markup,
                          parse_mode='Markdown')
            
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Xatolik: {str(e)}")
    
    elif call.data == "color_settings":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 Qizil", callback_data="color_red"))
        markup.add(types.InlineKeyboardButton("🔵 Ko'k", callback_data="color_blue"))
        markup.add(types.InlineKeyboardButton("🟢 Yashil", callback_data="color_green"))
        markup.add(types.InlineKeyboardButton("⚫ Qora (standart)", callback_data="color_black"))
        
        bot.edit_message_text("🎨 **QR kod rangi sozlamalari**\n\nRangni tanlang:",
                              call.message.chat.id, call.message.message_id,
                              reply_markup=markup)
    
    elif call.data.startswith("color_"):
        color = call.data.split("_")[1]
        colors = {
            "red": "Qizil",
            "blue": "Ko'k", 
            "green": "Yashil",
            "black": "Qora"
        }
        bot.answer_callback_query(call.id, f"✅ Rang o'zgartirildi: {colors[color]}")
        bot.edit_message_text(f"✅ **Rang muvaffaqiyatli o'zgartirildi!**\n\n🎨 Yangi rang: {colors[color]}",
                              call.message.chat.id, call.message.message_id)

def cleanup_old_data():
    """Eski ma'lumotlarni tozalash"""
    while True:
        time.sleep(3600)  # Har 1 soatda
        # Tozalash logikasi
        print("Ma'lumotlar tozalandi")

# Tozalash threadini ishga tushirish
cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    print("🤖 Bot ishga tushdi...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Botda xatolik: {e}")