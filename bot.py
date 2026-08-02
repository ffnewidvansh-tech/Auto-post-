import os
import json
import time
import random
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
GROUPS_FILE = "groups.json"
SETTINGS_FILE = "settings.json"
POSTS_FILE = "posts.json"

# Bot state
sending_active = False
sending_thread = None

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
        "welcome_image": "https://iili.io/C8DNTyQ.jpg",
        "welcome_text": "Welcome to the group! 🎉",
        "post_text": "Hello everyone! This is an auto post!",
        "send_interval": 6,
        "sending_active": False
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

# ============================================================
# SEND STYLISH + PREMIUM EMOJI MESSAGE
# ============================================================
def build_emoji_entities(text):
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

def send_pe(chat_id, text, reply_markup=None, parse_mode=None):
    try:
        processed_text, entities = build_emoji_entities(text)
        return bot.send_message(
            chat_id,
            processed_text,
            entities=entities,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        print(f"Send PE error: {e}")
        return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)

def send_to_group(group_id, text, photo=None):
    """Group me text + photo send karega"""
    try:
        if photo and photo.startswith("http"):
            bot.send_photo(group_id, photo=photo, caption=text)
        elif photo:
            bot.send_photo(group_id, photo=photo, caption=text)
        else:
            send_pe(group_id, text)
        return True
    except Exception as e:
        print(f"Send to group error: {e}")
        return False

# ============================================================
# AUTO SENDING THREAD
# ============================================================
def auto_send_loop():
    global sending_active
    settings = load_settings()
    posts = load_posts()
    groups = load_groups()
    
    if not groups:
        print("No groups added!")
        return
    
    if not posts:
        print("No posts available!")
        return
    
    index = 0
    while sending_active:
        try:
            settings = load_settings()
            posts = load_posts()
            groups = load_groups()
            
            if not posts:
                time.sleep(5)
                continue
            
            # Current post
            current_post = posts[index % len(posts)]
            text = current_post.get("text", "Hello!")
            photo = current_post.get("photo", None)
            
            # Send to all groups
            for group_id in groups.keys():
                try:
                    send_to_group(group_id, text, photo)
                    print(f"Sent to group: {group_id}")
                except Exception as e:
                    print(f"Failed to send to {group_id}: {e}")
            
            index += 1
            time.sleep(settings.get("send_interval", 6))
            
        except Exception as e:
            print(f"Auto send error: {e}")
            time.sleep(5)

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
# IS ADMIN CHECK
# ============================================================
def is_admin(user_id):
    return user_id in ADMIN_IDS

# ============================================================
# GET ADMIN MENU
# ============================================================
def get_admin_menu(user_id):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(KeyboardButton(stylish_text("ADD GROUP")), KeyboardButton(stylish_text("REMOVE GROUP")))
    markup.row(KeyboardButton(stylish_text("LIST GROUPS")), KeyboardButton(stylish_text("SET WELCOME")))
    markup.row(KeyboardButton(stylish_text("ADD POST")), KeyboardButton(stylish_text("LIST POSTS")))
    markup.row(KeyboardButton(stylish_text("START SENDING")), KeyboardButton(stylish_text("STOP SENDING")))
    markup.row(KeyboardButton(stylish_text("SET INTERVAL")), KeyboardButton(stylish_text("STATUS")))
    markup.row(KeyboardButton(stylish_text("HELP")), KeyboardButton(stylish_text("ABOUT")))
    return markup

# ============================================================
# BOT COMMANDS
# ============================================================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    if not is_admin(uid):
        send_pe(message.chat.id, "You are not authorized to use this bot!")
        return
    
    text = """
WELCOME TO AUTO POST BOT
═══════════════════════

I will automatically send posts to your groups!

FEATURES:
1. Add Group - Save group ID
2. Add Post - Text + Photo
3. Start/Stop Sending
4. Set Interval (Default 6 sec)
5. Welcome Image Change

═══════════════════════
DEVELOPER: @iflexzyan
"""
    markup = get_admin_menu(uid)
    send_pe(message.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
HELP
═══════════════════════

ADD GROUP - Add current group
REMOVE GROUP - Remove group
LIST GROUPS - Show all groups
SET WELCOME - Change welcome image
ADD POST - Add new post
LIST POSTS - Show all posts
START SENDING - Start auto send
STOP SENDING - Stop auto send
SET INTERVAL - Set send interval
STATUS - Show current status

═══════════════════════
"""
    markup = get_admin_menu(uid)
    send_pe(message.chat.id, text, reply_markup=markup)

# ============================================================
# ADD GROUP
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("ADD GROUP") in m.text)
def add_group_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
ADD GROUP
═══════════════════════

Send me the GROUP ID or forward a message from the group!

Or simply add me to the group and send /addgroup

═══════════════════════
"""
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_add_group)

def process_add_group(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    group_id = message.text.strip()
    
    # Check if it's a forwarded message
    if message.forward_from_chat:
        group_id = str(message.forward_from_chat.id)
    
    # Check if it's a number (group ID)
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
    
    text = f"""
GROUP ADDED
═══════════════════════
Group ID: {group_id}
Total Groups: {len(groups)}

═══════════════════════
"""
    send_pe(message.chat.id, text)
    markup = get_admin_menu(uid)
    send_pe(message.chat.id, "Select option:", reply_markup=markup)

@bot.message_handler(commands=['addgroup'])
def addgroup_cmd(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    if message.chat.type in ['group', 'supergroup']:
        group_id = str(message.chat.id)
        groups = load_groups()
        if group_id in groups:
            send_pe(message.chat.id, "Group already added!")
            return
        
        groups[group_id] = {
            "added_by": uid,
            "added_at": datetime.now().isoformat(),
            "name": message.chat.title
        }
        save_groups(groups)
        
        send_pe(message.chat.id, f"Group added successfully!\nID: {group_id}\nName: {message.chat.title}")
    else:
        send_pe(message.chat.id, "This command only works in groups!")

# ============================================================
# REMOVE GROUP
# ============================================================

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
    
    send_pe(message.chat.id, f"Group {group_id} removed!")

# ============================================================
# LIST GROUPS
# ============================================================

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
        added_at = data.get("added_at", "Unknown")
        text += f"• {gid} ({name})\n  Added: {added_at}\n\n"
    
    text += f"TOTAL: {len(groups)}"
    send_pe(message.chat.id, text)

# ============================================================
# SET WELCOME IMAGE
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("SET WELCOME") in m.text)
def set_welcome_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
SET WELCOME
═══════════════════════

Send me:
1. A PHOTO (for welcome image)
2. A TEXT (for welcome message)

Or send in format:
image_url|welcome_text

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
        send_pe(message.chat.id, "Welcome image updated from photo!")
    elif message.text:
        if '|' in message.text:
            parts = message.text.split('|', 1)
            settings["welcome_image"] = parts[0].strip()
            settings["welcome_text"] = parts[1].strip()
            save_settings(settings)
            send_pe(message.chat.id, "Welcome image and text updated!")
        else:
            settings["welcome_text"] = message.text.strip()
            save_settings(settings)
            send_pe(message.chat.id, "Welcome text updated!")

# ============================================================
# ADD POST
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("ADD POST") in m.text)
def add_post_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
ADD POST
═══════════════════════

Send your post in this format:
text|photo_url

Or just send text (no photo)
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
        caption = message.caption or "Photo post"
        posts.append({
            "text": caption,
            "photo": file_id,
            "added_by": uid,
            "added_at": datetime.now().isoformat()
        })
        save_posts(posts)
        send_pe(message.chat.id, "Photo post added!")
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
            send_pe(message.chat.id, "Post with photo added!")
        else:
            posts.append({
                "text": message.text.strip(),
                "photo": None,
                "added_by": uid,
                "added_at": datetime.now().isoformat()
            })
            save_posts(posts)
            send_pe(message.chat.id, "Text post added!")

# ============================================================
# LIST POSTS
# ============================================================

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
        text += f"{i}. {post.get('text', 'No text')[:50]}...\n"
        if post.get('photo'):
            text += "   📷 Has photo\n"
        text += "\n"
    
    text += f"TOTAL: {len(posts)}"
    send_pe(message.chat.id, text)

# ============================================================
# START/STOP SENDING
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("START SENDING") in m.text)
def start_sending(message):
    global sending_active, sending_thread
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    groups = load_groups()
    if not groups:
        send_pe(message.chat.id, "No groups added! Add a group first.")
        return
    
    posts = load_posts()
    if not posts:
        send_pe(message.chat.id, "No posts added! Add a post first.")
        return
    
    if sending_active:
        send_pe(message.chat.id, "Already sending!")
        return
    
    sending_active = True
    settings = load_settings()
    settings["sending_active"] = True
    save_settings(settings)
    
    import threading
    sending_thread = threading.Thread(target=auto_send_loop, daemon=True)
    sending_thread.start()
    
    send_pe(message.chat.id, f"Sending started! Interval: {settings.get('send_interval', 6)} seconds")

@bot.message_handler(func=lambda m: m.text and stylish_text("STOP SENDING") in m.text)
def stop_sending(message):
    global sending_active
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    sending_active = False
    settings = load_settings()
    settings["sending_active"] = False
    save_settings(settings)
    
    send_pe(message.chat.id, "Sending stopped!")

# ============================================================
# SET INTERVAL
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("SET INTERVAL") in m.text)
def set_interval_start(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
SET INTERVAL
═══════════════════════

Current interval: {interval} seconds

Send the new interval in seconds (minimum 2):

═══════════════════════
""".format(interval=load_settings().get('send_interval', 6))
    send_pe(message.chat.id, text)
    bot.register_next_step_handler(message, process_set_interval)

def process_set_interval(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    try:
        interval = int(message.text.strip())
        if interval < 2:
            send_pe(message.chat.id, "Minimum interval is 2 seconds!")
            return
        
        settings = load_settings()
        settings["send_interval"] = interval
        save_settings(settings)
        
        send_pe(message.chat.id, f"Interval set to {interval} seconds!")
    except:
        send_pe(message.chat.id, "Invalid number!")

# ============================================================
# STATUS
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("STATUS") in m.text)
def status_cmd(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    settings = load_settings()
    groups = load_groups()
    posts = load_posts()
    
    text = f"""
STATUS
═══════════════════════

SENDING: {'🟢 ACTIVE' if settings.get('sending_active', False) else '🔴 INACTIVE'}
INTERVAL: {settings.get('send_interval', 6)} seconds
TOTAL GROUPS: {len(groups)}
TOTAL POSTS: {len(posts)}
WELCOME IMAGE: {'✅ Set' if settings.get('welcome_image') else '❌ Not set'}

═══════════════════════
"""
    send_pe(message.chat.id, text)

# ============================================================
# ABOUT
# ============================================================

@bot.message_handler(func=lambda m: m.text and stylish_text("ABOUT") in m.text)
def about_cmd(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    
    text = """
ABOUT
═══════════════════════

AUTO POST BOT

Automatically sends posts to your groups!

FEATURES:
- Add multiple groups
- Add multiple posts
- Text + Photo support
- Custom interval
- Start/Stop control
- Welcome image change

DEVELOPER: @iflexzyan

═══════════════════════
"""
    send_pe(message.chat.id, text)

# ============================================================
# WELCOME MESSAGE IN GROUP
# ============================================================

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    try:
        settings = load_settings()
        welcome_text = settings.get("welcome_text", "Welcome to the group! 🎉")
        welcome_image = settings.get("welcome_image", None)
        
        for member in message.new_chat_members:
            if member.id == bot.get_me().id:
                # Bot added to group - auto add
                group_id = str(message.chat.id)
                groups = load_groups()
                if group_id not in groups:
                    groups[group_id] = {
                        "added_by": "BOT_ADDED",
                        "added_at": datetime.now().isoformat(),
                        "name": message.chat.title
                    }
                    save_groups(groups)
                    send_pe(message.chat.id, f"✅ Group automatically added!\nID: {group_id}")
                
                # Send welcome with image
                if welcome_image:
                    try:
                        bot.send_photo(message.chat.id, photo=welcome_image, caption=welcome_text)
                    except:
                        send_pe(message.chat.id, welcome_text)
                else:
                    send_pe(message.chat.id, welcome_text)
                
                return
        
        # Other members joining
        for member in message.new_chat_members:
            send_pe(message.chat.id, f"Welcome {member.first_name}! 🎉")
    except Exception as e:
        print(f"Welcome error: {e}")

# ============================================================
# FLASK WEBHOOK - PORT FIX
# ============================================================

@app.route('/', methods=['GET'])
def index():
    return "AUTO POST BOT is running on Render!"

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
    print("AUTO POST BOT Started!")
    print(f"Owner: {OWNER_ID}")
    print(f"Groups: {len(load_groups())}")
    print(f"Posts: {len(load_posts())}")
    
    # Auto start sending if it was active
    settings = load_settings()
    if settings.get("sending_active", False):
        import threading
        sending_active = True
        sending_thread = threading.Thread(target=auto_send_loop, daemon=True)
        sending_thread.start()
        print("Auto sending started!")
    
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