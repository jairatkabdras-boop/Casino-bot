from threading import Thread
from flask import Flask
import sqlite3
import random
import time
from telebot import TeleBot, types

# Render үшін веб-сервер
app = Flask('')

@app.route('/')
def home():
    return "Бот жұмыс істеп тұр!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Серверді фонода іске қосу
keep_alive()

# Ботыңның токені
TOKEN = "8506986123:AAFioXpfnTFPNJ3BPgOOAhheCNh6i08SdvE" # Осы жерге толық токеніңді қой
bot = TeleBot(TOKEN)

# Сенің Telegram ID-ің (Админ)
ADMIN_ID = 8851679127

# Рулеткадағы қызыл сандар
RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]

# --- БАЗА ДАННЫХ (SQLite) ---
conn = sqlite3.connect("casino.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
''')
conn.commit()

def get_user(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0))
        conn.commit()
        return 0
    return res[0]

def update_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

# --- МЕНЮ БАТЫРМАЛАРЫ ---
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💰 Баланс")
    btn2 = types.KeyboardButton("⭐ Звезда Толтыру")
    btn3 = types.KeyboardButton("⭐ Звезда Шығару")
    btn4 = types.KeyboardButton("🛠 Помощь")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id)
    bot.send_message(
        message.chat.id, 
        f"Салам, {message.from_user.first_name}! 🎰 Казино ботына қош келдің!\n\n"
        "🎮 **Қолжетімді ойындар:**\n"
        "🎰 **Слот:** `слоты [ставка]` (мысалы: `слоты 1`)\n"
        "🎡 **Европа Рулеткасы (0-36):**\n"
        "   • Санға: `рулетка [0-36] [ставка]` (мысалы: `рулетка 17 2`)\n"
        "   • Түске: `рулетка красное [ставка]` немесе `рулетка черное [ставка]`\n\n"
        "Толық ақпарат алу үшін төмендегі **«🛠 Помощь»** батырмасын бас!",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "🛠 Помощь")
def help_menu(message):
    help_text = (
        "🔥 **БАҚЫТЫҢДЫ СЫНАП КӨР!** 🔥\n\n"
        "Бұл жерде сен Telegram Stars арқылы ойнап, звездаларыңды бірнеше есе көбейте аласың! 🚀\n\n"
        "📌 **Ойын түрлері:**\n"
        "1️⃣ **Слот ойыны:** `слоты 3`\n"
        "   • 🎰 Джекпот (64) — **5 есе** ұтыс!\n\n"
        "2️⃣ **Европа Рулеткасы (0-36):**\n"
        "   • **Санға ставка:** `рулетка 17 2` (0-ден 36-ға дейін) — **36 есе** ұтыс! 🎯\n"
        "   • **Түске ставка:** `рулетка красное 5` немесе `рулетка черное 5` — **2 есе** ұтыс! 🔴⚫\n\n"
        "💸 **⭐ Звезда Шығару** батырмасы арқылы жинаған звездаларыңызды өзіңізге қайтарып ала аласыз!\n\n"
        "Бағыңызды сынап көріңіз, мүмкіндікті жіберіп алмаңыз! 👑"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def check_balance(message):
    bal = get_user(message.from_user.id)
    bot.reply_to(message, f"💳 Сенің боттағы балансың: **{bal} ⭐️**", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "⭐ Звезда Толтыру")
def ask_deposit_amount(message):
    msg = bot.send_message(
        message.chat.id, 
        "⭐ Қанша звезда салғыңыз келеді? Санын тек цифрмен жазыңыз (мысалы: `15`):",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    try:
        amount = int(message.text)
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сан 0-ден үлкен болуы керек.")
            return
        
        prices = [types.LabeledPrice(label=f"{amount} Звезда", amount=amount)]
        
        bot.send_invoice(
            chat_id=message.chat.id,
            title="Казино Балансын Толтыру",
            description=f"Боттағы ішкі балансыңа {amount} Звезда түседі.",
            invoice_payload=f"casino_deposit_{amount}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="stars-deposit"
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ Қате! Тек санды жазыңыз (Мысалы: 15).")

@bot.shipping_query_handler(func=lambda query: True)
def process_shipping(query):
    bot.answer_shipping_query(query.id, ok=True)

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    amount = message.successful_payment.total_amount
    update_balance(message.from_user.id, amount)
    bot.send_message(
        message.chat.id, 
        f"✅ Төлем сәтті өтті! Балансыңа **+{amount} ⭐️** қосылды!", 
        parse_mode="Markdown"
    )

# --- ЗВЕЗДА ШЫҒАРУ ЖӘНЕ АДМИН ТҮЙМЕЛЕРІ ---
@bot.message_handler(func=lambda m: m.text == "⭐ Звезда Шығару")
def ask_withdraw_amount(message):
    bal = get_user(message.from_user.id)
    if bal <= 0:
        bot.reply_to(message, "❌ Шығаруға болатын балансыңыз жоқ (0 ⭐️).")
        return

    msg = bot.send_message(
        message.chat.id, 
        f"📤 Қанша звезда шығарғыңыз келеді? (Сіздің балансыңыз: **{bal} ⭐️**)\nСанын тек цифрмен жазыңыз:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_withdraw_amount)

def process_withdraw_amount(message):
    user_id = message.from_user.id
    try:
        amount = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Қате! Тек санды жазыңыз.")
        return

    bal = get_user(user_id)

    if amount <= 0:
        bot.send_message(message.chat.id, "❌ Сан 0-ден үлкен болуы керек.")
        return

    if bal < amount:
        bot.send_message(message.chat.id, f"❌ Балансыңыз жеткіліксіз! Сізде бар: {bal} ⭐️")
        return

    update_balance(user_id, -amount)

    bot.send_message(
        message.chat.id, 
        f"⏳ **{amount} ⭐️** шығаруға өтініш қабылданды!\nАдмин тексеріп жатыр...", 
        parse_mode="Markdown"
    )

    user_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    admin_text = (
        f"🔔 **ЖАҢА ВЫВОД ӨТІНІШІ!**\n\n"
        f"👤 Қолданушы: {user_name} (ID: `{user_id}`)\n"
        f"💰 Сұралған сома: **{amount} ⭐️**"
    )
    
    inline_kb = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{user_id}_{amount}")
    btn_reject = types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}_{amount}")
    inline_kb.add(btn_approve, btn_reject)

    try:
        bot.send_message(ADMIN_ID, admin_text, reply_markup=inline_kb, parse_mode="Markdown")
    except Exception as e:
        print(f"Хабарлама қатесі: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_admin_decision(call):
    parts = call.data.split("_")
    action = parts[0]
    target_user_id = int(parts[1])
    amount = int(parts[2])

    if action == "approve":
        try:
            bot.send_message(
                target_user_id, 
                f"✅ **Өтінішіңіз расталды!**\n\nСаған жақын арада **{amount} ⭐️** аударамыз, күте тұр! 🎁", 
                parse_mode="Markdown"
            )
        except Exception:
            pass
        
        bot.edit_message_text(
            f"✅ **ӨТІНІШ РАСТАЛДЫ!**\n\n👤 Ойыншы ID: `{target_user_id}`\n💰 Сома: **{amount} ⭐️**\n\n*Ойыншыға күту хабарламасы жіберілді.*",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

    elif action == "reject":
        update_balance(target_user_id, amount)
        try:
            bot.send_message(
                target_user_id, 
                f"❌ **Өтінішіңіз кері қайтарылды.**\n\n{amount} ⭐️ қайтадан боттағы балансыңызға қосылды.", 
                parse_mode="Markdown"
            )
        except Exception:
            pass

        bot.edit_message_text(
            f"❌ **ӨТІНІШ КЕРІ ҚАЙТАРЫЛДЫ!**\n\n👤 Ойыншы ID: `{target_user_id}`\n💰 **{amount} ⭐️** ойыншы балансына қайтарылды.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )

# --- 1-ОЙЫН: СЛОТ ---
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("слоты"))
def play_slot_text(message):
    user_id = message.from_user.id
    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Қате формат! Былай жазып көр: `слоты 1`", parse_mode="Markdown")
        return

    try:
        stake = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Ставка тек сандық мән болуы тиіс!", parse_mode="Markdown")
        return

    bal = get_user(user_id)

    if stake <= 0 or bal < stake:
        bot.reply_to(message, f"❌ Баланс жеткіліксіз немесе қате ставка! Сізде: {bal} ⭐️", parse_mode="Markdown")
        return

    update_balance(user_id, -stake)
    msg = bot.send_dice(message.chat.id, emoji="🎰")
    value = msg.dice.value

    if value == 64:
        win_amount = stake * 5
        update_balance(user_id, win_amount)
        bot.send_message(message.chat.id, f"🎉 **ДЖЕКПОТ!** Сен **+{win_amount} ⭐️** ұтып алдың!", parse_mode="Markdown")
    elif value in [1, 22, 43]:
        win_amount = stake * 2
        update_balance(user_id, win_amount)
        bot.send_message(message.chat.id, f"🎉 Ұттың! Сен **+{win_amount} ⭐️** алдың!", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"😔 Ұтылдың (-{stake} ⭐️). Тағы бағыңды сынап көр!")

# --- 2-ОЙЫН: ЕВРОПА РУЛЕТКАСЫ (0-36) ---
# --- ЕВРОПА РУЛЕТКАСЫ (Диапазон, Түс, Сан және коэффициенттер) ---
RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]

@bot.message_handler(func=lambda message: message.text.lower().startswith('рулетка'))
def play_roulette_text(message):
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ **Қате формат!**\n\nМысалдар:\n• `рулетка 10 17` (санға)\n• `рулетка 10 к` (қызылға)\n• `рулетка 10 1-5` (диапазонға)", parse_mode="Markdown")
            return

        stake = int(parts[1])
        choice = parts[2].lower()

        user_id = message.from_user.id
        balance = get_user(user_id)[1]

        if stake <= 0:
            bot.reply_to(message, "❌ Ставка 0-ден үлкен болуы тиіс!")
            return

        if balance < stake:
            bot.reply_to(message, "❌ Балансыңда қаражат жеткіліксіз!")
            return

        # Ставканы шегереміз
        update_balance(user_id, -stake)

        winning_number = random.randint(0, 36)
        is_red = winning_number in RED_NUMBERS

        result_text = f"🎰 **Рулетка айналуда...**\n\n🎯 Түскен сан: **{winning_number}** ({'🔴 Қызыл' if is_red else '⚫ Қара'})\n\n"

        # 1. Диапазонға ставка (мысалы: 1-5)
        if '-' in choice:
            try:
                start, end = map(int, choice.split('-'))
                if not (0 <= start <= 36 and 0 <= end <= 36 and start <= end):
                    bot.reply_to(message, "❌ Қате диапазон (0 мен 36 аралығында болуы тиіс).")
                    update_balance(user_id, stake)
                    return
                
                if start <= winning_number <= end:
                    # Диапазон коэффициенті (аймақ қаншалықты тарылса, ұтыс соғұрлым үлкен)
                    multiplier = round(36 / (end - start + 1), 1)
                    win_amount = int(stake * multiplier)
                    update_balance(user_id, win_amount)
                    result_text += f"🎉 **ҰТЫС!** Сан диапазонға түсті ({multiplier}x)!\n💰 Ұтып алдың: **+{win_amount}** Звезда"
                else:
                    result_text += "😞 Өкінішке орай, ұтылдың."
            except ValueError:
                bot.reply_to(message, "❌ Диапазон форматы қате! (Мысалы: 1-5)")
                update_balance(user_id, stake)
                return

        # 2. Түске ставка (қызыл / қара / к / ч)
        elif choice in ['қызыл', 'к', 'red']:
            if is_red and winning_number != 0:
                # Мұнда коэффициентті өзің қалағаныңша өзгерте аласың (мысалы: 1.5 немесе 1.8)
                multiplier = 1.8 
                win_amount = int(stake * multiplier)
                update_balance(user_id, win_amount)
                result_text += f"🎉 **ҰТЫС!** Қызыл түсті ({multiplier}x)!\n💰 Ұтып алдың: **+{win_amount}** Звезда"
            else:
                result_text += "😞 Өкінішке орай, ұтылдың."

        elif choice in ['қара', 'ч', 'black']:
            if not is_red and winning_number != 0:
                multiplier = 1.8
                win_amount = int(stake * multiplier)
                update_balance(user_id, win_amount)
                result_text += f"🎉 **ҰТЫС!** Қара түсті ({multiplier}x)!\n💰 Ұтып алдың: **+{win_amount}** Звезда"
            else:
                result_text += "😞 Өкінішке орай, ұтылдың."

        # 3. Нақты санға ставка (0-36)
        else:
            try:
                target_number = int(choice)
                if target_number == winning_number:
                    win_amount = stake * 36
                    update_balance(user_id, win_amount)
                    result_text += f"🚀 **СУПЕР ҰТЫС!** Дәл таптың (36x)!\n💰 Ұтып алдың: **+{win_amount}** Звезда"
                else:
                    result_text += "😞 Өкінішке орай, ұтылдың."
            except ValueError:
                bot.reply_to(message, "❌ Қате таңдау! (Сан, 'к'/'ч' немесе 1-5 диапазонын жаз)", parse_mode="Markdown")
                update_balance(user_id, stake)
                return

        bot.send_message(message.chat.id, result_text, parse_mode="Markdown")

    except ValueError:
        bot.reply_to(message, "❌ Ставка санда болуы тиіс!\nМысалы: `рулетка 1 1-5`", parse_mode="Markdown")


# --- АВТО-ҚАЙТА ҚОСЫЛУ ЦИКЛЫ ---
    # Боттың үзіліссіз жұмыс істеуі үшін (polling орнына)
import time

while True:
  try:
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
  except Exception as e:
    print(f"Қате орын алды: {e}")
    time.sleep(3)

