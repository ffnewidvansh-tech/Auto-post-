import os
import json
import time
import random
import threading
import requests
from datetime import datetime
from flask import Flask, request
from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, MessageEntity

# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "8471373583"))
ADMIN_IDS = [OWNER_ID]
PORT = int(os.environ.get("PORT", 10000))

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not set!")
    exit(1)

bot = TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# ============================================================
# FILES & DATA
# ============================================================
USERS_FILE = "users.json"
GROUPS_FILE = "groups.json"
SETTINGS_FILE = "settings.json"
POSTS_FILE = "posts.json"
PENDING_FILE = "pending.json"
STATS_FILE = "stats.json"

# ============================================================
# STYLISH CHARACTERS
# ============================================================
def stylish_text(text: str) -> str:
    stylish_chars = {
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 'ꜱ', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ',
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ',
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'
    }
    result = ""
    for char in text:
        result += stylish_chars.get(char, char)
    return result

# ============================================================
# PREMIUM EMOJIS
# ============================================================
PREMIUM_EMOJIS = {
    "verified": {"id": "6147565374289220368", "fallback": "✅"},
    "stars": {"id": "6235403472741603087", "fallback": "⭐"},
    "heart": {"id": "6147617184479711380", "fallback": "❤️"},
    "done": {"id": "6274007313107915274", "fallback": "👍"},
    "flex": {"id": "6147464060305676048", "fallback": "😎"},
    "blue_verification": {"id": "6147524086768604985", "fallback": "💎"},
    "frozen": {"id": "5449449325434266744", "fallback": "❄️"},
    "crying": {"id": "6273840152980755328", "fallback": "😭"},
    "smiling": {"id": "6276057176444246654", "fallback": "🙂"},
    "seeing_up": {"id": "6273997026661241933", "fallback": "😋"},
    "teeth": {"id": "6273726078649372769", "fallback": "😁"},
    "blue_badge": {"id": "5978776771623914876", "fallback": "🟫"},
    "black_badge": {"id": "5978686323907628843", "fallback": "🔸"},
    "busy_tag": {"id": "5852873584912896283", "fallback": "🟧"},
    "instagram": {"id": "5895297528106061174", "fallback": "🌐"},
    "telegram": {"id": "5895735846698487922", "fallback": "🌐"},
    "whatsapp": {"id": "5895343514320899727", "fallback": "🌐"},
    "india": {"id": "5913754823643107921", "fallback": "🇮🇳"},
    "dollar": {"id": "5197434882321567830", "fallback": "💵"},
    "top": {"id": "5463071033256848094", "fallback": "🔝"},
    "bro": {"id": "5463256910851546817", "fallback": "🤝"},
    "yes": {"id": "5463423955014529788", "fallback": "👌"},
    "lock": {"id": "5465443379917629504", "fallback": "🔓"},
    "good": {"id": "5465465194056525619", "fallback": "👍"},
    "sigma": {"id": "6235620067942341623", "fallback": "🥃"},
    "don": {"id": "6235717714023814969", "fallback": "🍂"},
    "skills": {"id": "6235593671073339928", "fallback": "💀"},
    "github": {"id": "5346181118884331907", "fallback": "📱"},
    "motion": {"id": "5971944878815317190", "fallback": "💠"},
}

def get_random_emoji():
    return random.choice(list(PREMIUM_EMOJIS.keys()))

def get_premium_fallback(name):
    if name in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[name]["fallback"]
    return ""

# ============================================================
# DATA FUNCTIONS
# ============================================================
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_groups():
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_groups(groups):
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f, indent=2)

def load_settings():
    default = {
        "upi": "vanshx111@naviaxis",
        "price": 99,
        "premium_emojis": True,
        "bold_characters": True,
        "send_interval": 6,
        "sending_active": False,
        "welcome_image": "https://iili.io/C8DNTyQ.jpg",
        "welcome_text": "Welcome to Ad Bot! 🎉",
        "how_to_use_text": "1. Add me to any group\n2. Click Start Ads\n3. Pay subscription\n4. Ads will run!",
        "how_to_use_video": None,
        "total_messages": 0,
        "dm_username": None
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                for key, val in default.items():
                    if key not in data:
                        data[key] = val
                return data
        except:
            return default
    return default

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def load_posts():
    if os.path.exists(POSTS_FILE):
        try:
            with open(POSTS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_posts(posts):
    with open(POSTS_FILE, "w") as f:
        json.dump(posts, f, indent=2)

def load_pending():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pending(pending):
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2)

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except:
            return {"total_messages": 0}
    return {"total_messages": 0}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

# ============================================================
# SEND FUNCTIONS
# ============================================================
def build_message(text, use_premium=True, use_bold=True):
    """Text ko format karega based on settings"""
    # Convert to stylish if bold ON
    if use_bold:
        text = stylish_text(text)
    
    # Add premium emojis if ON
    if use_premium:
        lines = text.split('\n')
        result_lines = []
        entities = []
        offset = 0
        
        for line in lines:
            if line.strip():
                emoji_name = get_random_emoji()
                emoji_data = PREMIUM_EMOJIS[emoji_name]
                new_line = f"{emoji_data['fallback']} {line}"
                result_lines.append(new_line)
                entities.append(MessageEntity(
                    type="custom_emoji",
                    offset=offset,
                    length=1,
                    custom_emoji_id=emoji_data["id"]
                ))
                offset += len(new_line) + 1
            else:
                result_lines.append(line)
                offset += len(line) + 1
        
        return '\n'.join(result_lines), entities
    
    return text, None

def send_pe(chat_id, text, reply_markup=None, parse_mode=None, use_premium=True, use_bold=True):
    """Send message with premium emojis and bold"""
    try:
        processed_text, entities = build_message(text, use_premium, use_bold)
        if entities:
            return bot.send_message(
                chat_id,
                processed_text,
                entities=entities,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            return bot.send_message(
                chat_id,
                processed_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    except Exception as e:
        print(f"Send error: {e}")
        return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)

def send_to_group(group_id, text, photo=None, use_premium=True, use_bold=True):
    """Group me send karega"""
    try:
        settings = load_settings()
        stats = load_stats()
        
        # Update stats
        stats["total_messages"] = stats.get("total_messages", 0) + 1
        save_stats(stats)
        
        if photo:
            bot.send_photo(group_id, photo=photo, caption=text)
        else:
            send_pe(group_id, text, use_premium=use_premium, use_bold=use_bold)
        return True
    except Exception as e:
        print(f"Send to group error: {e}")
        return False

# ============================================================
# COLORFUL BUTTONS
# ============================================================
def make_green_button(text, callback=None, url=None):
    final = stylish_text(text)
    emoji = get_random_emoji()
    fb = get_premium_fallback(emoji)
    final = f"{fb} {final} {fb}"
    try:
        if callback:
            return InlineKeyboardButton(text=final, style="success", callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final, style="success", url=url)
        else:
            return InlineKeyboardButton(text=final, style="success")
    except:
        if callback:
            return InlineKeyboardButton(text=final, callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final, url=url)
        else:
            return InlineKeyboardButton(text=final)

def make_red_button(text, callback=None, url=None):
    final = stylish_text(text)
    emoji = get_random_emoji()
    fb = get_premium_fallback(emoji)
    final = f"{fb} {final} {fb}"
    try:
        if callback:
            return InlineKeyboardButton(text=final, style="danger", callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final, style="danger", url=url)
        else:
            return InlineKeyboardButton(text=final, style="danger")
    except:
        if callback:
            return InlineKeyboardButton(text=final, callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final, url=url)
        else:
            return InlineKeyboardButton(text=final)

def make_blue_button(text, callback=None, url=None):
    final = stylish_text(text)
    emoji = get_random_emoji()
    fb = get_premium_fallback(emoji)
    final = f"{fb} {final} {fb}"
    try:
        if callback:
            return InlineKeyboardButton(text=final, style="primary", callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final, style="primary", url=url)
        else:
            return InlineKeyboardButton(text=final, style="primary")
    except:
        if callback:
            return InlineKeyboardButton(text=final, callback_data=callback)
        elif url:
            return InlineKeyboardButton(text=final, url=url)
        else:
            return InlineKeyboardButton(text=final)

# ============================================================
# AUTO SENDING
# ============================================================
sending_active = False
sending_thread = None

def auto_send_loop():
    global sending_active
    settings = load_settings()
    posts = load_posts()
    groups = load_groups()
    use_premium = settings.get("premium_emojis", True)
    use_bold = settings.get("bold_characters", True)
    dm_username = settings.get("dm_username", None)
    
    if not groups or not posts:
        return
    
    index = 0
    while sending_active:
        try:
            settings = load_settings()
            posts = load_posts()
            groups = load_groups()
            use_premium = settings.get("premium_emojis", True)
            use_bold = settings.get("bold_characters", True)
            dm_username = settings.get("dm_username", None)
            
            if not posts:
                time.sleep(5)
                continue
            
            current_post = posts[index % len(posts)]
            text = current_post.get("text", "Advertisement")
            photo = current_post.get("photo", None)
            
            # Add DM button if set
            if dm_username:
                text += f"\n\n📩 DM: @{dm_username}"
            
            for group_id in groups.keys():
                try:
                    send_to_group(group_id, text, photo, use_premium, use_bold)
                except:
                    pass
            
            index += 1
            time.sleep(settings.get("send_interval", 6))
            
        except Exception as e:
            print(f"Auto send error: {e}")
            time.sleep(5)

# ============================================================
# IS ADMIN CHECK
# ============================================================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def register_user(uid, username=None, name=None):
    users = load_users()
    if str(uid) not in users:
        users[str(uid)] = {
            "id": uid,
            "username": username,
            "name": name or "Unknown",
            "joined": datetime.now().isoformat(),
            "approved": False,
            "banned": False,
            "admin": False
        }
        save_users(users)
        # Notify owner
        send_pe(OWNER_ID, f"✅ New User Joined!\n👤 ID: {uid}\n👾 @{username or 'N/A'}\n📛 {name or 'Unknown'}")
    return users[str(uid)]

def get_user(uid):
    users = load_users()
    return users.get(str(uid))

def update_user(uid, key, val):
    users = load_users()
    if str(uid) in users:
        users[str(uid)][key] = val
        save_users(users)

# ============================================================
# USER MENU
# ============================================================
def get_user_menu(uid):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(KeyboardButton(stylish_text("START ADS")), KeyboardButton(stylish_text("STOP ADS")))
    markup.row(KeyboardButton(stylish_text("BUY SUBSCRIPTION")), KeyboardButton(stylish_text("ADD DM IN ADS")))
    markup.row(KeyboardButton(stylish_text("HOW TO USE")), KeyboardButton(stylish_text("STATS")))
    markup.row(KeyboardButton(stylish_text("SUPPORT")), KeyboardButton(stylish_text("HELP")))
    markup.row(KeyboardButton(stylish_text("ABOUT")), KeyboardButton(stylish_text("")))
    return markup

def get_admin_menu(uid):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(KeyboardButton(stylish_text("ADD GROUP")), KeyboardButton(stylish_text("REMOVE GROUP")))
    markup.row(KeyboardButton(stylish_text("LIST GROUPS")), KeyboardButton(stylish_text("ADD POST")))
    markup.row(KeyboardButton(stylish_text("LIST POSTS")), KeyboardButton(stylish_text("START ADS")))
    markup.row(KeyboardButton(stylish_text("STOP ADS")), KeyboardButton(stylish_text("SET INTERVAL")))
    markup.row(KeyboardButton(stylish_text("PREMIUM EMOJIS ON")), KeyboardButton(stylish_text("PREMIUM EMOJIS OFF")))
    markup.row(KeyboardButton(stylish_text("BOLD CHARACTERS ON")), KeyboardButton(stylish_text("BOLD CHARACTERS OFF")))
    markup.row(KeyboardButton(stylish_text("USERS")), KeyboardButton(stylish_text("DATA")))
    markup.row(KeyboardButton(stylish_text("PENDING USERS")), KeyboardButton(stylish_text("TOTAL MESSAGES")))
    markup.row(KeyboardButton(stylish_text("CHANGE UPI")), KeyboardButton(stylish_text("CHANGE PRICE")))
    markup.row(KeyboardButton(stylish_text("SET DM USERNAME")), KeyboardButton(stylish_text("SET WELCOME")))
    markup.row(KeyboardButton(stylish_text("SET HOW TO USE")), KeyboardButton(stylish_text("BOT ON")))
    markup.row(KeyboardButton(stylish_text("BOT OFF")), KeyboardButton(stylish_text("STATUS")))
    markup.row(KeyboardButton(stylish_text("HELP")), KeyboardButton(stylish_text("ABOUT")))
    return markup

# ============================================================
# BOT COMMANDS
# ============================================================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    try:
        uid = message.from_user.id
        username = message.from_user.username
        name = message.from_user.first_name
        
        # Register user
        user = register_user(uid, username, name)
        
        if user.get("banned", False):
            send_pe(message.chat.id, "❌ You are banned from using this bot!")
            return
        
        settings = load_settings()
        welcome_image = settings.get("welcome_image", "https://iili.io/C8DNTyQ.jpg")
        
        try:
            bot.send_photo(message.chat.id, photo=welcome_image)
        except:
            pass
        
        text = f"""
WELCOME TO AD BOT
═══════════════════════
USER: {name}
ID: {uid}
USERNAME: @{username or 'N/A'}

═══════════════════════

THIS BOT IS USED FOR RUNNING ADS IN CHEAP RATES

Add me to any group for advertisement!

═══════════════════════
DEVELOPER: @iflexzyan
"""
        if is_admin(uid):
            markup = get_admin_menu(uid)
        else:
            markup = get_user_menu(uid)
        
        send_pe(message.chat.id, text, reply_markup=markup)
    except Exception as e:
        print(f"Start error: {e}")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    uid = message.from_user.id
    text = """
HELP
═══════════════════════

1. START ADS - Start advertising
2. STOP ADS - Stop advertising
3. BUY SUBSCRIPTION - Get access
4. ADD DM IN ADS - Add your username
5. HOW TO USE - Guide
6. STATS - View stats
7. SUPPORT - Contact support

═══════════════════════
"""
    if is_admin(uid):
        markup = get_admin_menu(uid)
    else:
        markup = get_user_menu(uid)
    
    send_pe(message.chat.id, text, reply_markup=markup)

# ============================================================
# START ADS - QR
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("START ADS") in m.text)
def start_ads(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    if not user or user.get("banned", False):
        send_pe(message.chat.id, "❌ You are banned!")
        return
    
    if not user.get("approved", False) and not is_admin(uid):
        send_pe(message.chat.id, "❌ You are not approved! Please buy subscription.")
        return
    
    settings = load_settings()
    groups = load_groups()
    posts = load_posts()
    
    if not groups:
        send_pe(message.chat.id, "❌ No groups added! Add me to a group first.")
        return
    
    if not posts:
        send_pe(message.chat.id, "❌ No posts added! Add a post first.")
        return
    
    global sending_active, sending_thread
    
    if sending_active:
        send_pe(message.chat.id, "✅ Ads already running!")
        return
    
    sending_active = True
    settings["sending_active"] = True
    save_settings(settings)
    
    import threading
    sending_thread = threading.Thread(target=auto_send_loop, daemon=True)
    sending_thread.start()
    
    send_pe(message.chat.id, f"✅ Ads started! Interval: {settings.get('send_interval', 6)} seconds")

@bot.message_handler(func=lambda m: m.text and stylish_text("STOP ADS") in m.text)
def stop_ads(message):
    global sending_active
    uid = message.from_user.id
    
    if not is_admin(uid):
        user = get_user(uid)
        if not user or not user.get("approved", False):
            send_pe(message.chat.id, "❌ You are not approved!")
            return
    
    sending_active = False
    settings = load_settings()
    settings["sending_active"] = False
    save_settings(settings)
    
    send_pe(message.chat.id, "✅ Ads stopped!")

# ============================================================
# BUY SUBSCRIPTION - QR
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("BUY SUBSCRIPTION") in m.text)
def buy_subscription(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    if user and user.get("approved", False):
        send_pe(message.chat.id, "✅ You already have access!")
        return
    
    settings = load_settings()
    upi = settings.get("upi", "vanshx111@naviaxis")
    price = settings.get("price", 99)
    
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={upi}&am={price}&cu=INR"
    
    text = f"""
BUY SUBSCRIPTION
═══════════════════════
UPI: {upi}
AMOUNT: Rs.{price}

Scan QR to Pay

═══════════════════════
"""
    
    keyboard = [
        [make_green_button("I HAVE PAID", callback=f"paid_{uid}")],
        [make_blue_button("SUPPORT", callback="support")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    
    try:
        bot.send_photo(message.chat.id, photo=qr_url, caption=text, reply_markup=markup)
    except:
        send_pe(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("paid_"))
def handle_paid(call):
    uid = int(call.data.split("_")[1])
    user_id = call.from_user.id
    
    if user_id != uid:
        send_pe(call.message.chat.id, "❌ This is not your request!")
        bot.answer_callback_query(call.id)
        return
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    pending = load_pending()
    pending[str(uid)] = {
        "user_id": uid,
        "username": call.from_user.username,
        "name": call.from_user.first_name,
        "status": "pending",
        "requested": datetime.now().isoformat()
    }
    save_pending(pending)
    
    send_pe(call.message.chat.id, "📸 Send payment screenshot!")
    bot.register_next_step_handler(call.message, receive_payment_screenshot)
    bot.answer_callback_query(call.id)

def receive_payment_screenshot(message):
    uid = message.from_user.id
    
    if message.photo:
        file_id = message.photo[-1].file_id
        pending = load_pending()
        if str(uid) in pending:
            pending[str(uid)]["screenshot"] = file_id
            pending[str(uid)]["status"] = "pending"
            save_pending(pending)
        
        send_pe(message.chat.id, "✅ Received! Waiting for admin approval.")
        
        admin_text = f"""
NEW PAYMENT
═══════════════════════
USER: {message.from_user.first_name}
ID: {uid}
USERNAME: @{message.from_user.username or 'N/A'}
═══════════════════════
"""
        keyboard = [
            [make_green_button("APPROVE", callback=f"admin_approve_{uid}")],
            [make_red_button("REJECT", callback=f"admin_reject_{uid}")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        
        for admin in ADMIN_IDS:
            try:
                bot.send_photo(admin, photo=file_id, caption=admin_text, reply_markup=markup)
            except:
                send_pe(admin, admin_text, reply_markup=markup)
    else:
        send_pe(message.chat.id, "❌ Send a photo!")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("admin_approve_"))
def admin_approve(call):
    if not is_admin(call.from_user.id):
        send_pe(call.message.chat.id, "❌ Unauthorized!")
        bot.answer_callback_query(call.id)
        return
    
    uid = int(call.data.split("_")[2])
    
    update_user(uid, "approved", True)
    
    pending = load_pending()
    if str(uid) in pending:
        del pending[str(uid)]
        save_pending(pending)
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    send_pe(call.message.chat.id, f"✅ User {uid} approved!")
    
    try:
        send_pe(uid, "✅ Congratulations! You now have access to run ads! 🎉")
    except:
        pass
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("admin_reject_"))
def admin_reject(call):
    if not is_admin(call.from_user.id):
        send_pe(call.message.chat.id, "❌ Unauthorized!")
        bot.answer_callback_query(call.id)
        return
    
    uid = int(call.data.split("_")[2])
    
    pending = load_pending()
    if str(uid) in pending:
        del pending[str(uid)]
        save_pending(pending)
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    send_pe(call.message.chat.id, f"❌ User {uid} rejected!")
    
    try:
        send_pe(uid, "❌ Your payment was not approved. Please contact support.")
    except:
        pass
    
    bot.answer_callback_query(call.id)

# ============================================================
# ADD DM IN ADS
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("ADD DM IN ADS") in m.text)
def add_dm_start(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    if not user or user.get("banned", False):
        send_pe(message.chat.id, "❌ You are banned!")
        return
    
    if not user.get("approved", False) and not is_admin(uid):
        send_pe(message.chat.id, "❌ You are not approved!")
        return
    
    text = """
ADD DM IN ADS
═══════════════════════

Send your Telegram username (without @):

Example: iflexzyan

This username will appear in ads as DM button.

═══════════════════════
"""
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_add_dm)

def process_add_dm(message):
    uid = message.from_user.id
    username = message.text.strip().replace('@', '')
    
    settings = load_settings()
    settings["dm_username"] = username
    save_settings(settings)
    
    send_pe(message.chat.id, f"✅ DM username set to: @{username}")

# ============================================================
# HOW TO USE
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("HOW TO USE") in m.text)
def how_to_use(message):
    settings = load_settings()
    video = settings.get("how_to_use_video", None)
    text = settings.get("how_to_use_text", "1. Add me to any group\n2. Click Start Ads\n3. Pay subscription\n4. Ads will run!")
    
    if video:
        try:
            bot.send_video(message.chat.id, video=video, caption=text)
        except:
            send_pe(message.chat.id, text)
    else:
        send_pe(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text and stylish_text("SET HOW TO USE") in m.text)
def set_how_to_use_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
SET HOW TO USE
═══════════════════════

Send new guide text or send a video for guide

═══════════════════════
"""
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_set_how_to_use)

def process_set_how_to_use(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    settings = load_settings()
    
    if message.video:
        file_id = message.video.file_id
        settings["how_to_use_video"] = file_id
        caption = message.caption or "Video Guide"
        settings["how_to_use_text"] = caption
        save_settings(settings)
        send_pe(message.chat.id, "✅ How to use video updated!")
    elif message.text:
        settings["how_to_use_text"] = message.text.strip()
        settings["how_to_use_video"] = None
        save_settings(settings)
        send_pe(message.chat.id, "✅ How to use text updated!")

# ============================================================
# STATS
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("STATS") in m.text)
def stats_cmd(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    if user and user.get("banned", False):
        send_pe(message.chat.id, "❌ You are banned!")
        return
    
    settings = load_settings()
    stats = load_stats()
    
    if is_admin(uid):
        text = f"""
STATS
═══════════════════════
TOTAL GROUPS: {len(load_groups())}
TOTAL POSTS: {len(load_posts())}
TOTAL MESSAGES: {stats.get('total_messages', 0)}
INTERVAL: {settings.get('send_interval', 6)} sec
SENDING: {'ACTIVE' if settings.get('sending_active', False) else 'INACTIVE'}
PREMIUM EMOJIS: {'ON' if settings.get('premium_emojis', True) else 'OFF'}
BOLD CHARACTERS: {'ON' if settings.get('bold_characters', True) else 'OFF'}
DM USERNAME: @{settings.get('dm_username', 'Not Set')}
═══════════════════════
"""
        send_pe(message.chat.id, text)
    else:
        stats = load_stats()
        text = f"""
STATS
═══════════════════════
TOTAL MESSAGES: {stats.get('total_messages', 0)}
SENDING: {'ACTIVE' if settings.get('sending_active', False) else 'INACTIVE'}
═══════════════════════
"""
        send_pe(message.chat.id, text)

# ============================================================
# SUPPORT
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("SUPPORT") in m.text)
def support_cmd(message):
    text = """
SUPPORT
═══════════════════════
DEVELOPER: @iflexzyan
For any issues, contact:
📱 Telegram: @iflexzyan
═══════════════════════
"""
    markup = InlineKeyboardMarkup([
        [make_blue_button("CONTACT SUPPORT", url="https://t.me/iflexzyan")]
    ])
    send_pe(message.chat.id, text, reply_markup=markup)

# ============================================================
# ABOUT
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("ABOUT") in m.text)
def about_cmd(message):
    text = """
ABOUT
═══════════════════════
AD BOT
Run ads in groups easily!
Features:
- Auto posting
- Premium emojis
- Bold characters
- DM button
- Subscription system
═══════════════════════
DEVELOPER: @iflexzyan
"""
    send_pe(message.chat.id, text)

# ============================================================
# ADMIN COMMANDS
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("ADD GROUP") in m.text)
def add_group_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
ADD GROUP
═══════════════════════
Send the GROUP ID or add me to group and send /addgroup

═══════════════════════
"""
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_add_group)

def process_add_group(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    group_id = message.text.strip()
    
    if not group_id.startswith('-') and not group_id.startswith('@'):
        try:
            group_id = str(int(group_id))
        except:
            send_pe(message.chat.id, "Invalid group ID!")
            return
    
    groups = load_groups()
    if group_id in groups:
        send_pe(message.chat.id, "Group already added!")
        return
    
    groups[group_id] = {
        "added_by": uid,
        "added_at": datetime.now().isoformat()
    }
    save_groups(groups)
    
    send_pe(message.chat.id, f"✅ Group added: {group_id}")

@bot.message_handler(commands=['addgroup'])
def addgroup_cmd(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    if message.chat.type in ['group', 'supergroup']:
        group_id = str(message.chat.id)
        groups = load_groups()
        if group_id not in groups:
            groups[group_id] = {
                "added_by": uid,
                "added_at": datetime.now().isoformat(),
                "name": message.chat.title
            }
            save_groups(groups)
            send_pe(message.chat.id, f"✅ Group added successfully!\nID: {group_id}\nName: {message.chat.title}")
        else:
            send_pe(message.chat.id, "Group already added!")
    else:
        send_pe(message.chat.id, "This command only works in groups!")

@bot.message_handler(func=lambda m: m.text and stylish_text("REMOVE GROUP") in m.text)
def remove_group_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    groups = load_groups()
    if not groups:
        send_pe(message.chat.id, "No groups added!")
        return
    
    text = "REMOVE GROUP\n═══════════════════════\nSend the GROUP ID to remove:\n\n"
    for gid in groups.keys():
        name = groups[gid].get("name", "Unknown")
        text += f"• {gid} ({name})\n"
    
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_remove_group)

def process_remove_group(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    group_id = message.text.strip()
    groups = load_groups()
    if group_id not in groups:
        send_pe(message.chat.id, "Group not found!")
        return
    
    del groups[group_id]
    save_groups(groups)
    send_pe(message.chat.id, f"✅ Group {group_id} removed!")

@bot.message_handler(func=lambda m: m.text and stylish_text("LIST GROUPS") in m.text)
def list_groups(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    groups = load_groups()
    if not groups:
        send_pe(message.chat.id, "No groups added!")
        return
    
    text = "GROUPS\n═══════════════════════\n"
    for gid, data in groups.items():
        name = data.get("name", "Unknown")
        text += f"• {gid} ({name})\n"
    
    text += f"\nTOTAL: {len(groups)}"
    send_pe(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text and stylish_text("ADD POST") in m.text)
def add_post_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
ADD POST
═══════════════════════
Send your post in format:
text|photo_url

Or just send text
Or send a photo with caption

═══════════════════════
"""
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_add_post)

def process_add_post(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    posts = load_posts()
    
    if message.photo:
        file_id = message.photo[-1].file_id
        caption = message.caption or "Advertisement"
        posts.append({
            "text": caption,
            "photo": file_id,
            "added_by": uid,
            "added_at": datetime.now().isoformat()
        })
        save_posts(posts)
        send_pe(message.chat.id, "✅ Photo post added!")
    elif message.text:
        if '|' in message.text:
            parts = message.text.split('|', 1)
            posts.append({
                "text": parts[0].strip(),
                "photo": parts[1].strip(),
                "added_by": uid,
                "added_at": datetime.now().isoformat()
            })
            save_posts(posts)
            send_pe(message.chat.id, "✅ Post with photo added!")
        else:
            posts.append({
                "text": message.text.strip(),
                "photo": None,
                "added_by": uid,
                "added_at": datetime.now().isoformat()
            })
            save_posts(posts)
            send_pe(message.chat.id, "✅ Text post added!")

@bot.message_handler(func=lambda m: m.text and stylish_text("LIST POSTS") in m.text)
def list_posts(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    posts = load_posts()
    if not posts:
        send_pe(message.chat.id, "No posts added!")
        return
    
    text = "POSTS\n═══════════════════════\n"
    for i, post in enumerate(posts, 1):
        text += f"{i}. {post.get('text', '')[:50]}...\n"
        if post.get('photo'):
            text += "   📷 Has photo\n"
        text += "\n"
    
    text += f"TOTAL: {len(posts)}"
    send_pe(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text and stylish_text("SET INTERVAL") in m.text)
def set_interval_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    settings = load_settings()
    text = f"""
SET INTERVAL
═══════════════════════
Current interval: {settings.get('send_interval', 6)} seconds
Minimum: 2 seconds
Maximum: 600 seconds (10 minutes)

Send new interval:
═══════════════════════
"""
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_set_interval)

def process_set_interval(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    try:
        interval = int(message.text.strip())
        if interval < 2:
            send_pe(message.chat.id, "Minimum is 2 seconds!")
            return
        if interval > 600:
            send_pe(message.chat.id, "Maximum is 600 seconds (10 minutes)!")
            return
        
        settings = load_settings()
        settings["send_interval"] = interval
        save_settings(settings)
        send_pe(message.chat.id, f"✅ Interval set to {interval} seconds!")
    except:
        send_pe(message.chat.id, "❌ Invalid number!")

@bot.message_handler(func=lambda m: m.text and stylish_text("PREMIUM EMOJIS ON") in m.text)
def premium_emojis_on(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    settings = load_settings()
    settings["premium_emojis"] = True
    save_settings(settings)
    send_pe(message.chat.id, "✅ Premium Emojis turned ON!")

@bot.message_handler(func=lambda m: m.text and stylish_text("PREMIUM EMOJIS OFF") in m.text)
def premium_emojis_off(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    settings = load_settings()
    settings["premium_emojis"] = False
    save_settings(settings)
    send_pe(message.chat.id, "❌ Premium Emojis turned OFF!")

@bot.message_handler(func=lambda m: m.text and stylish_text("BOLD CHARACTERS ON") in m.text)
def bold_on(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    settings = load_settings()
    settings["bold_characters"] = True
    save_settings(settings)
    send_pe(message.chat.id, "✅ Bold Characters turned ON!")

@bot.message_handler(func=lambda m: m.text and stylish_text("BOLD CHARACTERS OFF") in m.text)
def bold_off(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    settings = load_settings()
    settings["bold_characters"] = False
    save_settings(settings)
    send_pe(message.chat.id, "❌ Bold Characters turned OFF!")

@bot.message_handler(func=lambda m: m.text and stylish_text("USERS") in m.text)
def users_cmd(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    users = load_users()
    if not users:
        send_pe(message.chat.id, "No users found!")
        return
    
    text = "USERS\n═══════════════════════\n"
    for uid, data in users.items():
        status = "✅" if data.get("approved", False) else "⏳"
        banned = "🚫" if data.get("banned", False) else ""
        admin = "👑" if int(uid) in ADMIN_IDS else ""
        text += f"• {data.get('name', 'Unknown')} (@{data.get('username', 'N/A')}) - {status} {banned} {admin}\n"
    
    text += f"\nTOTAL: {len(users)}"
    send_pe(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text and stylish_text("PENDING USERS") in m.text)
def pending_users(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    pending = load_pending()
    if not pending:
        send_pe(message.chat.id, "No pending users!")
        return
    
    text = "PENDING USERS\n═══════════════════════\n"
    for uid, data in pending.items():
        text += f"• {data.get('name', 'Unknown')} (@{data.get('username', 'N/A')})\n"
    
    text += f"\nTOTAL: {len(pending)}"
    send_pe(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text and stylish_text("TOTAL MESSAGES") in m.text)
def total_messages_cmd(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    stats = load_stats()
    send_pe(message.chat.id, f"📊 Total Messages Sent: {stats.get('total_messages', 0)}")

@bot.message_handler(func=lambda m: m.text and stylish_text("DATA") in m.text)
def data_cmd(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    users = load_users()
    groups = load_groups()
    posts = load_posts()
    pending = load_pending()
    settings = load_settings()
    stats = load_stats()
    
    data = {
        "users": users,
        "groups": groups,
        "posts": posts,
        "pending": pending,
        "settings": settings,
        "stats": stats,
        "admins": ADMIN_IDS,
        "total_users": len(users),
        "total_groups": len(groups),
        "total_posts": len(posts),
        "total_messages": stats.get("total_messages", 0),
        "pending_users": len(pending),
        "total_admins": len(ADMIN_IDS),
        "generated": datetime.now().isoformat()
    }
    
    file_path = "bot_data.json"
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    
    with open(file_path, "rb") as f:
        bot.send_document(message.chat.id, f, caption="📥 Full Data Export")

@bot.message_handler(func=lambda m: m.text and stylish_text("CHANGE UPI") in m.text)
def change_upi_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
CHANGE UPI
═══════════════════════
Current UPI: {upi}

Send new UPI ID:

═══════════════════════
""".format(upi=load_settings().get('upi', 'vanshx111@naviaxis'))
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_change_upi)

def process_change_upi(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    upi = message.text.strip()
    settings = load_settings()
    settings["upi"] = upi
    save_settings(settings)
    send_pe(message.chat.id, f"✅ UPI updated to: {upi}!")

@bot.message_handler(func=lambda m: m.text and stylish_text("CHANGE PRICE") in m.text)
def change_price_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
CHANGE PRICE
═══════════════════════
Current Price: Rs.{price}

Send new price:

═══════════════════════
""".format(price=load_settings().get('price', 99))
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_change_price)

def process_change_price(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    try:
        price = int(message.text.strip())
        if price <= 0:
            send_pe(message.chat.id, "❌ Price must be greater than 0!")
            return
        
        settings = load_settings()
        settings["price"] = price
        save_settings(settings)
        send_pe(message.chat.id, f"✅ Price updated to: Rs.{price}!")
    except:
        send_pe(message.chat.id, "❌ Invalid number!")

@bot.message_handler(func=lambda m: m.text and stylish_text("SET DM USERNAME") in m.text)
def set_dm_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
SET DM USERNAME
═══════════════════════
Current DM: @{dm}

Send new Telegram username (without @):

═══════════════════════
""".format(dm=load_settings().get('dm_username', 'Not Set'))
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_set_dm)

def process_set_dm(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    username = message.text.strip().replace('@', '')
    settings = load_settings()
    settings["dm_username"] = username
    save_settings(settings)
    send_pe(message.chat.id, f"✅ DM username set to: @{username}")

@bot.message_handler(func=lambda m: m.text and stylish_text("SET WELCOME") in m.text)
def set_welcome_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
SET WELCOME
═══════════════════════
Send a PHOTO for welcome image
Or send TEXT for welcome message

═══════════════════════
"""
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_set_welcome)

def process_set_welcome(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    settings = load_settings()
    
    if message.photo:
        file_id = message.photo[-1].file_id
        settings["welcome_image"] = file_id
        save_settings(settings)
        send_pe(message.chat.id, "✅ Welcome image updated from photo!")
    elif message.text:
        settings["welcome_text"] = message.text.strip()
        save_settings(settings)
        send_pe(message.chat.id, "✅ Welcome text updated!")

@bot.message_handler(func=lambda m: m.text and stylish_text("BOT ON") in m.text)
def bot_on(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    global sending_active
    
    settings = load_settings()
    if settings.get("sending_active", False):
        sending_active = True
        import threading
        thread = threading.Thread(target=auto_send_loop, daemon=True)
        thread.start()
    
    send_pe(message.chat.id, "✅ Bot is now ONLINE!")

@bot.message_handler(func=lambda m: m.text and stylish_text("BOT OFF") in m.text)
def bot_off(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    global sending_active
    sending_active = False
    settings = load_settings()
    settings["sending_active"] = False
    save_settings(settings)
    
    send_pe(message.chat.id, "❌ Bot is now OFFLINE!")

@bot.message_handler(func=lambda m: m.text and stylish_text("STATUS") in m.text)
def status_admin(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    settings = load_settings()
    stats = load_stats()
    groups = load_groups()
    posts = load_posts()
    users = load_users()
    
    text = f"""
STATUS
═══════════════════════
BOT: {'🟢 ONLINE' if settings.get('sending_active', False) else '🔴 OFFLINE'}
SENDING: {'ACTIVE' if settings.get('sending_active', False) else 'INACTIVE'}
INTERVAL: {settings.get('send_interval', 6)} sec
TOTAL GROUPS: {len(groups)}
TOTAL POSTS: {len(posts)}
TOTAL USERS: {len(users)}
TOTAL MESSAGES: {stats.get('total_messages', 0)}
PREMIUM EMOJIS: {'ON' if settings.get('premium_emojis', True) else 'OFF'}
BOLD CHARACTERS: {'ON' if settings.get('bold_characters', True) else 'OFF'}
DM USERNAME: @{settings.get('dm_username', 'Not Set')}
UPI: {settings.get('upi', 'vanshx111@naviaxis')}
PRICE: Rs.{settings.get('price', 99)}
ADMINS: {len(ADMIN_IDS)}
═══════════════════════
"""
    send_pe(message.chat.id, text)

# ============================================================
# WELCOME NEW MEMBERS
# ============================================================

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    try:
        for member in message.new_chat_members:
            if member.id == bot.get_me().id:
                # Bot added to group
                group_id = str(message.chat.id)
                groups = load_groups()
                if group_id not in groups:
                    groups[group_id] = {
                        "added_by": "BOT_ADDED",
                        "added_at": datetime.now().isoformat(),
                        "name": message.chat.title
                    }
                    save_groups(groups)
                    
                    settings = load_settings()
                    welcome_image = settings.get("welcome_image", None)
                    welcome_text = f"""
✅ Bot added to group!
GROUP: {message.chat.title}
ID: {group_id}

Add me to any group for advertisement!
Contact: @iflexzyan
"""
                    if welcome_image:
                        try:
                            bot.send_photo(message.chat.id, photo=welcome_image, caption=welcome_text)
                        except:
                            send_pe(message.chat.id, welcome_text)
                    else:
                        send_pe(message.chat.id, welcome_text)
                return
    except Exception as e:
        print(f"Welcome error: {e}")

# ============================================================
# FLASK WEBHOOK
# ============================================================

@app.route('/', methods=['GET'])
def index():
    return "AD BOT is running on Render!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
    except Exception as e:
        print(f"Webhook error: {e}")
    return '', 403

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("AD BOT Started!")
    print(f"Owner: {OWNER_ID}")
    print(f"Admins: {len(ADMIN_IDS)}")
    print(f"Users: {len(load_users())}")
    
    try:
        bot.remove_webhook()
        print("Webhook removed!")
    except Exception as e:
        print(f"Webhook remove error: {e}")
    
    try:
        hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        if hostname:
            webhook_url = f"https://{hostname}/{BOT_TOKEN}"
            bot.set_webhook(url=webhook_url)
            print(f"Webhook set: {webhook_url}")
        else:
            print("No hostname, using polling")
            bot.infinity_polling()
            exit()
    except Exception as e:
        print(f"Webhook error: {e}, falling back to polling")
        bot.infinity_polling()
        exit()
    
    app.run(host='0.0.0.0', port=PORT)