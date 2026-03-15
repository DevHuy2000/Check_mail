#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║         FREE FIRE TOOL BOT - TELEGRAM                        ║
# ║         Garena Email Bind + Token Logout Manager             ║
# ║         Developed with PyTelegramBotAPI                      ║
# ╚══════════════════════════════════════════════════════════════╝

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import os
import random
import time
import jwt as jwtLib
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime
import MajorLoginRes_pb2 as mLrPb

urllib3.disable_warnings()

# ══════════════════ CONFIG ══════════════════
BOT_TOKEN   = "8676420403:AAGOSA458UJwmayRxtz8vYzsyTyox8ta2EQ"
ADMIN_IDS   = [1804489430]          # ← Thay bằng Telegram ID của admin
COST_PER_USE = 10                  # Xu mỗi lần dùng chức năng
DATA_FILE   = "users.json"

bot = telebot.TeleBot(BOT_TOKEN)

# ══════════════════ AES CONFIG (out.py) ══════════════════
AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'

mLuRl = "https://loginbp.ggpolarbear.com/MajorLogin"
iNuRl = "https://100067.connect.garena.com/oauth/token/inspect?token={t}"

mLhDr = {
    "User-Agent":      "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
    "Connection":      "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type":    "application/octet-stream",
    "Expect":          "100-continue",
    "X-GA":            "v1 1",
    "X-Unity-Version": "2018.4.11f1",
    "ReleaseVersion":  "OB52",
}
iNhDr = {
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "close",
    "Content-Type":    "application/x-www-form-urlencoded",
    "Host":            "100067.connect.garena.com",
    "User-Agent":      "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)",
}
lOhDr = {
    "User-Agent":      "Free%20Fire/2019119620 CFNetwork/1335.0.3.4 Darwin/21.6.0",
    "X-GA":            "v1 1",
    "X-Unity-Version": "2018.4.11f1",
    "ReleaseVersion":  "OB52",
    "Content-Type":    "application/octet-stream",
    "Accept":          "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Host":            "clientbp.ggpolarbear.com",
}

# ══════════════════ CHECK-BIND / UNBIND-PLATFORM ══════════════════
bNuRl = "https://100067.connect.garena.com/bind/app/platform/info/get"
bIdUr = "https://clientbp.ggpolarbear.com/BindDelete"
bIdHd = {
    "User-Agent":      "Free%20Fire/2019119620 CFNetwork/1335.0.3.4 Darwin/21.6.0",
    "X-GA":            "v1 1",
    "X-Unity-Version": "2018.4.11f1",
    "ReleaseVersion":  "OB52",
    "Content-Type":    "application/octet-stream",
    "Accept":          "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Host":            "clientbp.ggpolarbear.com",
}
PLATFORM_NAMES = {
    1:  "Facebook",
    2:  "VK",
    4:  "Google",
    7:  "Guest",
    8:  "Garena",
    9:  "Huawei",
    11: "Twitter",
    12: "Apple",
}

# ══════════════════ DATABASE (JSON) ══════════════════
def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def get_user(uid):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {"coins": 0, "uses": 0, "joined": str(datetime.now())}
        save_db(db)
    return db[uid]

def update_coins(uid, amount):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {"coins": 0, "uses": 0, "joined": str(datetime.now())}
    db[uid]["coins"] = db[uid].get("coins", 0) + amount
    save_db(db)
    return db[uid]["coins"]

def deduct_coins(uid):
    """Trừ xu, trả về True nếu đủ, False nếu thiếu"""
    db = load_db()
    uid = str(uid)
    if db.get(uid, {}).get("coins", 0) < COST_PER_USE:
        return False
    db[uid]["coins"] -= COST_PER_USE
    db[uid]["uses"]  = db[uid].get("uses", 0) + 1
    save_db(db)
    return True

def is_admin(uid):
    return int(uid) in ADMIN_IDS

# ══════════════════ AES HELPERS ══════════════════
def encA(d):
    return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))

def decA(d):
    return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

def eVr(n):
    r = []
    while True:
        b = n & 0x7F; n >>= 7
        if n: b |= 0x80
        r.append(b)
        if not n: break
    return bytes(r)

def _s(f, v):
    ev = v.encode() if isinstance(v, str) else v
    return eVr((f << 3) | 2) + eVr(len(ev)) + ev

def _i(f, v):
    return eVr((f << 3) | 0) + eVr(v)

def bUiLd(oId, tok, plat):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p  = str(plat)
    pl = (
        _s(1,  ts)   + _s(4, "free fire")  + _i(5, 1)
      + _s(7,  "1.120.2")
      + _s(8,  "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)")
      + _s(9,  "Handheld")  + _s(10, "Verizon")   + _s(11, "WIFI")
      + _i(12, 1920)        + _i(13, 1080)         + _s(14, "280")
      + _s(15, "ARM64 FP ASIMD AES VMH | 2865 | 4")
      + _i(16, 3003)
      + _s(17, "Adreno (TM) 640")     + _s(18, "OpenGL ES 3.1 v1.46")
      + _s(19, "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57")
      + _s(20, "223.191.51.89")       + _s(21, "en")
      + _s(22, oId)  + _s(23, p)      + _s(24, "Handheld")  + _s(25, "07@Q")
      + _s(29, tok)  + _i(30, 1)
      + _s(41, "Verizon")  + _s(42, "WIFI")
      + _s(57, "7428b253defc164018c604a1ebbfebdf")
      + _i(60,36235)+_i(61,31335)+_i(62,2519)+_i(63,703)
      + _i(64,25010)+_i(65,26628)+_i(66,32992)+_i(67,36235)
      + _i(73, 3)
      + _s(74, "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64")
      + _i(76, 1)
      + _s(77, "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk")
      + _i(78,3)+_i(79,2)
      + _s(81,"64")  + _s(83,"2019118695")  + _s(86,"OpenGLES2")
      + _i(87,16383) + _i(88,4)
      + _s(89,"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg==")
      + _i(92,13564)
      + _s(93,"android")
      + _s(94,"KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY=")
      + _i(95,110009)+_i(97,1)+_i(98,1)
      + _s(99,p) + _s(100,p)
    )
    return encA(pl)

def gLogin(aT):
    r = requests.get(iNuRl.format(t=aT), headers=iNhDr, timeout=10).json()
    if 'error' in r:
        raise Exception(f"Token không hợp lệ: {r.get('error')}")
    oId  = r['open_id']
    plat = r.get('platform', 8)
    pl   = bUiLd(oId, aT, plat)
    x    = requests.post(mLuRl, headers=mLhDr, data=pl, timeout=15, verify=False)
    if not x.ok:
        raise Exception(f"MajorLogin thất bại: HTTP {x.status_code}")
    res = mLrPb.MajorLoginRes()
    try:
        res.ParseFromString(decA(x.content))
    except:
        res.ParseFromString(x.content)
    if not res.token:
        raise Exception("Token rỗng từ server")
    cl   = jwtLib.decode(res.token, options={"verify_signature": False})
    aId  = cl.get('account_id', getattr(res, 'account_id', oId))
    nick = cl.get('nickname', 'Unknown')
    return res.token, nick, aId, oId, plat

def do_logout(aT):
    tok, nick, *_ = gLogin(aT)
    pkt = _s(1, aT) + _s(2, "Android|00000000-0000-0000-0000-000000000000") + _s(3, "samsung SM-T505N")
    enc = encA(pkt)
    hd  = {**lOhDr, "Authorization": f"Bearer {tok}"}
    r1  = requests.post("https://clientbp.ggpolarbear.com/Logout",
                        headers=hd, data=enc, verify=False, timeout=10)
    r2  = requests.get(f"https://100067.connect.garena.com/oauth/logout?access_token={aT}",
                       headers=iNhDr, timeout=10)
    return nick, r1.status_code, r2.status_code

# ══════════════════ BIND HELPERS ══════════════════
HDR_BIND = {
    "User-Agent":   "GarenaMSDK/4.0.30",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept":       "application/json"
}

# ── Header chuẩn cho bind info API ──
HDR_BIND_INFO = {
    "User-Agent":      "GarenaMSDK/4.0.19P9(Redmi Note 5;Android 9;en;US;)",
    "Accept":          "application/json",
    "Accept-Encoding": "gzip",
    "Connection":      "Keep-Alive",
}

def api_check_bind(access_token):
    """Lấy thông tin bind email — dùng API chuẩn auth.garena.com."""
    # API chính: get_bind_info
    url1 = "https://auth.garena.com/game/account_security/bind:get_bind_info"
    try:
        r1 = requests.get(url1, params={
            "app_id": "100067",
            "access_token": access_token
        }, headers=HDR_BIND_INFO, timeout=12)
        r1.raise_for_status()
        d1 = r1.json()
    except Exception:
        d1 = {}

    # API phụ: inspect — lấy open_id, platform, account_id
    url2 = "https://100067.connect.garena.com/oauth/token/inspect?token=" + access_token
    try:
        r2 = requests.get(url2, headers=HDR_BIND, timeout=10)
        d2 = r2.json()
    except Exception:
        d2 = {}

    return d1, d2

def api_send_otp(email, access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    r   = requests.post(url, headers=HDR_BIND, data={
        "email": email, "locale": "en_PK", "region": "PK",
        "app_id": "100067", "access_token": access_token
    }, timeout=10)
    return r.json()

def api_verify_identity(email, otp, access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    r   = requests.post(url, headers=HDR_BIND, data={
        "email": email, "app_id": "100067",
        "access_token": access_token, "otp": otp
    }, timeout=10)
    return r.json()

def api_verify_otp(email, otp, access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    r   = requests.post(url, headers=HDR_BIND, data={
        "email": email, "app_id": "100067",
        "access_token": access_token, "otp": otp
    }, timeout=10)
    return r.json()

def api_create_rebind(access_token, identity_token, new_email, verifier_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
    r   = requests.post(url, headers=HDR_BIND, data={
        "identity_token": identity_token, "email": new_email,
        "app_id": "100067", "verifier_token": verifier_token,
        "access_token": access_token
    }, timeout=10)
    return r

def api_create_unbind(access_token, identity_token):
    url = "https://100067.connect.gopapi.io/game/account_security/bind:create_unbind_request"
    r   = requests.post(url, headers=HDR_BIND, data={
        "app_id": "100067", "access_token": access_token,
        "identity_token": identity_token
    }, timeout=10)
    return r

def api_cancel_bind(access_token):
    url = "https://100067.connect.gopapi.io/game/account_security/bind:cancel_request"
    r   = requests.post(url, headers=HDR_BIND, data={
        "app_id": "100067", "access_token": access_token
    }, timeout=10)
    return r

# ══════════════════ EAT → ACCESS TOKEN ══════════════════
from urllib.parse import urlparse, parse_qs

def convert_eat_to_access(eat_token: str):
    """Chuyển đổi EAT token sang Access Token qua Garena callback API."""
    api = "https://api-otrss.garena.com/support/callback/?access_token={}"
    r   = requests.get(api.format(eat_token), allow_redirects=False, timeout=10)
    location = r.headers.get("Location", "")
    if not location:
        raise Exception("Không nhận được redirect URL — Token không hợp lệ hoặc đã hết hạn")
    parsed = urlparse(location)
    access_token = parse_qs(parsed.query).get("access_token", [None])[0]
    if not access_token:
        raise Exception(f"Không tìm thấy access_token trong URL redirect:\n{location}")
    return access_token

# ══════════════════ CHECK + UNBIND PLATFORM ══════════════════
def do_check_platform(aT):
    """Lấy danh sách nền tảng đang liên kết với tài khoản."""
    tok, nick, aId, oId, plat = gLogin(aT)
    r = requests.get(
        bNuRl,
        params={"access_token": aT},
        headers={
            "User-Agent":      "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
            "Connection":      "Keep-Alive",
            "Accept-Encoding": "gzip",
        },
        timeout=10
    )
    d = r.json()
    if isinstance(d, dict) and 'data' in d:
        d = d['data']
    bounded = []
    avail   = []
    if isinstance(d, dict):
        bounded = d.get('bounded_accounts') or d.get('list') or d.get('bind_list') or []
        avail   = d.get('available_platforms') or []
    return tok, nick, aId, oId, plat, bounded, avail

def do_unbind_platform(aT, tok, pid_int, uid_str):
    """Gỡ liên kết 1 nền tảng cụ thể."""
    pkt = _s(1, aT) + _s(2, str(pid_int)) + _s(3, uid_str)
    enc = encA(pkt)
    hd  = {**bIdHd, "Authorization": f"Bearer {tok}"}
    r   = requests.post(bIdUr, headers=hd, data=enc, verify=False, timeout=10)
    return r.status_code

# ══════════════════ SESSION STORAGE ══════════════════
# session[uid] = {"step": "...", "data": {...}}
session = {}

def set_session(uid, step, **kwargs):
    existing = session.get(str(uid), {})
    # Giữ lại msg_ids khi chuyển bước
    msg_ids      = existing.get("msg_ids", [])
    user_msg_ids = existing.get("user_msg_ids", [])
    session[str(uid)] = {
        "step": step,
        "data": kwargs,
        "msg_ids": msg_ids,
        "user_msg_ids": user_msg_ids,
    }

def get_session(uid):
    return session.get(str(uid), {})

def clear_session(uid):
    session.pop(str(uid), None)

def track_bot_msg(uid, msg):
    """Theo dõi tin nhắn bot gửi ra."""
    if msg is None: return
    s = session.setdefault(str(uid), {"step": "", "data": {}, "msg_ids": [], "user_msg_ids": []})
    s.setdefault("msg_ids", []).append(msg.message_id)

def track_user_msg(uid, msg_id):
    """Theo dõi tin nhắn user gửi vào (để xoá token nhạy cảm)."""
    s = session.setdefault(str(uid), {"step": "", "data": {}, "msg_ids": [], "user_msg_ids": []})
    s.setdefault("user_msg_ids", []).append(msg_id)

def delete_tracked(chat_id, uid):
    """Xoá toàn bộ tin nhắn đã track của một flow."""
    s = session.get(str(uid), {})
    all_ids = s.get("msg_ids", []) + s.get("user_msg_ids", [])
    for mid in all_ids:
        try:
            bot.delete_message(chat_id, mid)
        except Exception:
            pass

# ══════════════════ KEYBOARDS ══════════════════
def main_menu_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔄 Đổi Bind",   callback_data="menu_change_bind"),
        InlineKeyboardButton("🔓 Gỡ Bind",    callback_data="menu_unbind"),
    )
    kb.add(
        InlineKeyboardButton("✖️ Hủy Bind", callback_data="menu_cancel_bind"),
        InlineKeyboardButton("ℹ️ Info Bind",callback_data="menu_bind_info"),
    )
    kb.add(
        InlineKeyboardButton("🚪 Logout",      callback_data="menu_logout"),
        InlineKeyboardButton("🔑 EAT → AT",callback_data="menu_eat"),
    )
    kb.add(
        InlineKeyboardButton("🔗 Check Liên Kết", callback_data="menu_check_platform"),
    )
    kb.add(
        InlineKeyboardButton("💰 Xu Của Tôi",     callback_data="my_coins"),
        InlineKeyboardButton("📋 Lịch Sử",  callback_data="my_history"),
    )
    return kb

def admin_menu_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Thêm Xu",  callback_data="admin_add_coins"),
        InlineKeyboardButton("➖ Trừ Xu",   callback_data="admin_sub_coins"),
    )
    kb.add(
        InlineKeyboardButton("👥 DS User", callback_data="admin_list_users"),
        InlineKeyboardButton("🔍 Info User",  callback_data="admin_view_user"),
    )
    kb.add(
        InlineKeyboardButton("📢 Broadcast",      callback_data="admin_broadcast"),
    )
    kb.add(
        InlineKeyboardButton("🏠 Menu Chính",     callback_data="back_main"),
    )
    return kb

def back_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏠 Menu Chính", callback_data="back_main"))
    return kb

def cancel_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ Huỷ", callback_data="cancel_action"))
    return kb

# ══════════════════ MESSAGE TEMPLATES ══════════════════
def welcome_text(user, coins):
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return (
        f"🎮 **Chào mừng đến với FF Tool Bot\\!**\n\n"
        f"┌────────────────────────\n"
        f"│ 👤 *Tên:* `{name}`\n"
        f"│ 🆔 *Telegram ID:* `{user.id}`\n"
        f"│ 💰 *Xu hiện tại:* `{coins} xu`\n"
        f"└────────────────────────\n\n"
        f"> _🎁 Bạn vừa nhận được xu thưởng khi lần đầu khởi động\\!_\n\n"
        f"Mỗi chức năng tốn **{COST_PER_USE} xu\\/lần**\\.\n"
        f"Hãy chọn một chức năng bên dưới\\:"
    )

def intro_text():
    return (
        "🔥 *FREE FIRE TOOL BOT*\n"
        "> _Garena Account Manager_\n\n"
        "┌─────────────────────\n"
        "│ 🔄 Đổi Bind  │ 🔓 Gỡ Bind\n"
        "│ ✖️ Hủy Bind  │ ℹ️ Info Bind\n"
        "│ 🚪 Logout    │ 🔑 EAT→AT\n"
        "│ 🔗 Check Liên Kết / Gỡ Nền Tảng\n"
        "└─────────────────────\n\n"
        f"> _💎 {COST_PER_USE} xu / lần · Chọn chức năng:_"
    )

def coins_text(uid):
    u = get_user(uid)
    return (
        f"💰 *Ví Xu*\n\n"
        f"┌──────────────────\n"
        f"│ 💵 Xu: `{u.get('coins', 0)} xu`\n"
        f"│ 🔢 Dùng: `{u.get('uses', 0)} lần`\n"
        f"│ 📅 Tham gia: `{u.get('joined', 'N/A')[:10]}`\n"
        f"└──────────────────\n"
        f"> _{COST_PER_USE} xu / lần sử dụng_"
    )

def not_enough_coins_text(coins):
    return (
        f"❌ *Không đủ xu!*\n"
        f"💰 Hiện có: `{coins} xu` · Cần: `{COST_PER_USE} xu`\n"
        f"> _Liên hệ admin để nạp thêm_"
    )

# ══════════════════ /start ══════════════════
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid  = msg.from_user.id
    user = get_user(uid)

    is_new = user.get("coins", 0) == 0 and user.get("uses", 0) == 0

    if is_new:
        bonus = random.randint(1, 5)
        coins = update_coins(uid, bonus)
        # Lấy ảnh avatar
        try:
            photos = bot.get_user_profile_photos(uid, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][0].file_id
                bot.send_photo(
                    msg.chat.id,
                    file_id,
                    caption=(
                        f"🎮 *Chào mừng đến với FF Tool Bot\\!*\n\n"
                        f"┌────────────────────────\n"
                        f"│ 👤 *Tên:* `{msg.from_user.first_name or 'User'}`\n"
                        f"│ 🆔 *Telegram ID:* `{uid}`\n"
                        f"│ 💰 *Xu hiện tại:* `{coins} xu`\n"
                        f"└────────────────────────\n\n"
                        f"> _🎁 Chào mừng\\! Bạn nhận được *{bonus} xu* thưởng đầu tiên\\!_\n\n"
                        f"Mỗi chức năng tốn *{COST_PER_USE} xu/lần*."
                    ),
                    parse_mode="MarkdownV2",
                    reply_markup=main_menu_kb()
                )
                return
        except:
            pass

        bot.send_message(
            msg.chat.id,
            (
                f"🎮 *Chào mừng đến với FF Tool Bot\\!*\n\n"
                f"┌────────────────────────\n"
                f"│ 👤 *Tên:* `{msg.from_user.first_name or 'User'}`\n"
                f"│ 🆔 *Telegram ID:* `{uid}`\n"
                f"│ 💰 *Xu hiện tại:* `{coins} xu`\n"
                f"└────────────────────────\n\n"
                f"> _🎁 Chào mừng\\! Bạn nhận được *{bonus} xu* thưởng đầu tiên\\!_\n\n"
                f"Mỗi chức năng tốn *{COST_PER_USE} xu/lần*."
            ),
            parse_mode="MarkdownV2",
            reply_markup=main_menu_kb()
        )
    else:
        coins = user.get("coins", 0)
        bot.send_message(
            msg.chat.id,
            intro_text(),
            parse_mode="Markdown",
            reply_markup=main_menu_kb()
        )

# ══════════════════ /eat ══════════════════
@bot.message_handler(commands=['eat'])
def cmd_eat(msg):
    uid  = msg.from_user.id
    args = msg.text.strip().split(maxsplit=1)

    # Dùng inline: /eat <token>
    if len(args) == 2:
        eat_token = args[1].strip()
        u = get_user(uid)
        if u.get("coins", 0) < COST_PER_USE:
            bot.reply_to(
                msg,
                not_enough_coins_text(u.get("coins", 0)),
                parse_mode="MarkdownV2"
            )
            return
        processing = bot.reply_to(msg, "⏳ *Đang chuyển đổi EAT token\\.\\.\\.*", parse_mode="MarkdownV2")
        try:
            access_token = convert_eat_to_access(eat_token)
            deduct_coins(uid)
            new_coins = get_user(uid)["coins"]
            result = (
                f"✅ *Chuyển Đổi Thành Công\\!*\n\n"
                f"> _EAT token đã được chuyển sang Access Token_\n\n"
                f"┌──────────────────────────\n"
                f"│ 🔑 *Access Token:*\n"
                f"│ `{access_token}`\n"
                f"└──────────────────────────\n\n"
                f"💰 Xu còn lại: `{new_coins} xu`"
            )
            bot.edit_message_text(result, msg.chat.id, processing.message_id, parse_mode="MarkdownV2")
        except Exception as e:
            bot.edit_message_text(
                f"❌ *Lỗi chuyển đổi:*\n`{str(e)[:300]}`",
                msg.chat.id, processing.message_id, parse_mode="Markdown"
            )
        return

    # Không có token → hướng dẫn
    bot.reply_to(
        msg,
        "🔑 *Chuyển EAT → Access Token*\n\n"
        "> _Cách sử dụng:_\n\n"
        "`/eat <eat_token>`\n\n"
        "Hoặc chọn từ menu chính bên dưới:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔑 EAT → Access Token", callback_data="menu_eat")
        )
    )

# ══════════════════ /admin ══════════════════
@bot.message_handler(commands=['admin'])
def cmd_admin(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "⛔ *Bạn không có quyền admin\\!*", parse_mode="MarkdownV2")
        return
    bot.send_message(
        msg.chat.id,
        "🛡 *Admin Panel*\n> _Chọn chức năng:_",
        parse_mode="Markdown",
        reply_markup=admin_menu_kb()
    )

# ══════════════════ CALLBACK HANDLER ══════════════════
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid  = call.from_user.id
    data = call.data
    chat = call.message.chat.id
    mid  = call.message.message_id

    # ── Helper: safe_edit (xử lý cả message thường lẫn message có ảnh) ──
    def safe_edit(txt, kb=None, pm="Markdown"):
        try:
            bot.edit_message_text(txt, chat, mid, parse_mode=pm,
                                  reply_markup=kb if kb is not None else main_menu_kb())
        except Exception:
            try:
                bot.delete_message(chat, mid)
            except Exception:
                pass
            bot.send_message(chat, txt, parse_mode=pm,
                             reply_markup=kb if kb is not None else main_menu_kb())

    # ── Back / Cancel ──
    if data == "back_main":
        clear_session(uid)
        safe_edit(intro_text(), main_menu_kb())
        bot.answer_callback_query(call.id)
        return

    if data == "cancel_action":
        delete_tracked(chat, uid)
        clear_session(uid)
        safe_edit("❌ *Đã huỷ thao tác.*", back_kb())
        bot.answer_callback_query(call.id, "Đã huỷ")
        return

    # ── My Coins ──
    if data == "my_coins":
        safe_edit(coins_text(uid), back_kb())
        bot.answer_callback_query(call.id)
        return

    if data == "my_history":
        u = get_user(uid)
        text = (
            f"📋 *Lịch Sử Sử Dụng*\n\n"
            f"> _Thống kê hoạt động tài khoản_\n\n"
            f"┌─────────────────────\n"
            f"│ 🔢 Tổng lần dùng: `{u.get('uses', 0)} lần`\n"
            f"│ 💵 Xu đã tiêu: `{u.get('uses', 0) * COST_PER_USE} xu`\n"
            f"│ 💰 Xu còn lại: `{u.get('coins', 0)} xu`\n"
            f"└─────────────────────"
        )
        safe_edit(text, back_kb())
        bot.answer_callback_query(call.id)
        return

    # ══ MENU FUNCTIONS ══
    u     = get_user(uid)
    coins = u.get("coins", 0)

    def check_coins():
        if coins < COST_PER_USE:
            safe_edit(not_enough_coins_text(coins), back_kb())
            bot.answer_callback_query(call.id, "❌ Không đủ xu!")
            return False
        return True

    # ── Bind Info (miễn phí xem) ──
    if data == "menu_bind_info":
        set_session(uid, "bind_info_token")
        safe_edit(
            "ℹ️ *Xem Thông Tin Bind*\n\n"
            "> _Gửi Access Token của bạn:_",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    # ── Change Bind ──
    if data == "menu_change_bind":
        if not check_coins(): return
        set_session(uid, "cb_token")
        safe_edit(
            "🔄 *Đổi Email Bind*\n\n"
            f"> _Chi phí: {COST_PER_USE} xu_\n\n"
            "**Bước 1/4** — Gửi Access Token:",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    # ── Unbind ──
    if data == "menu_unbind":
        if not check_coins(): return
        set_session(uid, "ub_token")
        safe_edit(
            "🔓 *Gỡ Bind Email*\n\n"
            f"> _Chi phí: {COST_PER_USE} xu_\n\n"
            "**Bước 1/3** — Gửi Access Token:",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    # ── Cancel Bind ──
    if data == "menu_cancel_bind":
        if not check_coins(): return
        set_session(uid, "cn_token")
        safe_edit(
            "✖️ *Hủy Yêu Cầu Bind*\n\n"
            f"> _Chi phí: {COST_PER_USE} xu_\n\n"
            "**Bước 1/1** — Gửi Access Token:",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    # ── Logout ──
    if data == "menu_logout":
        if not check_coins(): return
        set_session(uid, "lo_token")
        safe_edit(
            "🚪 *Logout Token*\n\n"
            f"> _Chi phí: {COST_PER_USE} xu_\n\n"
            "**Bước 1/1** — Gửi Access Token:",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    # ── EAT → Access Token ──
    if data == "menu_eat":
        if not check_coins(): return
        set_session(uid, "eat_token")
        safe_edit(
            "🔑 *Chuyển Đổi EAT → Access Token*\n\n"
            f"> _Chi phí: {COST_PER_USE} xu_\n\n"
            "**Bước 1/1** — Gửi EAT Token của bạn:\n\n"
            "_Hoặc dùng lệnh nhanh:_ `/eat <token>`",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    # ── Check Liên Kết Platform ──
    if data == "menu_check_platform":
        if not check_coins(): return
        set_session(uid, "cp_token")
        safe_edit(
            "🔗 *Check Liên Kết Nền Tảng*\n\n"
            f"> _Chi phí: {COST_PER_USE} xu_\n\n"
            "Gửi Access Token của bạn:",
            cancel_kb()
        )
        bot.answer_callback_query(call.id)
        return

    # ── Callback chọn gỡ nền tảng ──
    if data.startswith("unbind_plat:"):
        # format: unbind_plat:<pid_int>:<uid_str>
        parts = data.split(":", 2)
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "Dữ liệu không hợp lệ")
            return
        pid_int  = int(parts[1])
        uid_str  = parts[2]
        sess2    = get_session(uid)
        aT_saved = sess2.get("data", {}).get("access_token")
        tok_saved= sess2.get("data", {}).get("jwt_token")
        pname    = PLATFORM_NAMES.get(pid_int, f"Platform {pid_int}")
        if not aT_saved or not tok_saved:
            bot.answer_callback_query(call.id, "Phiên đã hết hạn, vui lòng thử lại")
            return
        # Confirm keyboard
        kb_confirm = InlineKeyboardMarkup()
        kb_confirm.add(
            InlineKeyboardButton(f"✅ Xác nhận gỡ {pname}", callback_data=f"confirm_unbind:{pid_int}:{uid_str}"),
            InlineKeyboardButton("❌ Huỷ", callback_data="cancel_action"),
        )
        safe_edit(
            f"⚠️ *Xác Nhận Gỡ Liên Kết*\n\n"
            f"Nền tảng: *{pname}*\n"
            f"UID: `{uid_str}`\n\n"
            f"> _Bấm xác nhận để tiếp tục_",
            kb_confirm
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("confirm_unbind:"):
        parts = data.split(":", 2)
        pid_int  = int(parts[1])
        uid_str  = parts[2]
        pname    = PLATFORM_NAMES.get(pid_int, f"Platform {pid_int}")
        sess2    = get_session(uid)
        aT_saved = sess2.get("data", {}).get("access_token")
        tok_saved= sess2.get("data", {}).get("jwt_token")
        if not aT_saved or not tok_saved:
            bot.answer_callback_query(call.id, "Phiên hết hạn")
            return
        try:
            status = do_unbind_platform(aT_saved, tok_saved, pid_int, uid_str)
            if status == 200:
                safe_edit(
                    f"✅ *Gỡ Liên Kết Thành Công!*\n\n"
                    f"Nền tảng: *{pname}*\n"
                    f"UID: `{uid_str}`",
                    back_kb()
                )
            else:
                safe_edit(f"❌ *Thất bại* — HTTP `{status}`", back_kb())
        except Exception as e:
            safe_edit(f"❌ *Lỗi:* `{str(e)[:200]}`", back_kb())
        delete_tracked(chat, uid)
        clear_session(uid)
        bot.answer_callback_query(call.id)
        return

    # ══ ADMIN CALLBACKS ══
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "⛔ Không có quyền!")
        return

    if data == "admin_add_coins":
        set_session(uid, "adm_add_uid")
        safe_edit(
            "➕ *Thêm Xu cho User*\n\n> _Gửi Telegram ID của user:_",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_sub_coins":
        set_session(uid, "adm_sub_uid")
        safe_edit(
            "➖ *Trừ Xu của User*\n\n> _Gửi Telegram ID của user:_",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_list_users":
        db  = load_db()
        txt = "👥 *Danh Sách User*\n\n> _Tổng cộng {} user_\n\n".format(len(db))
        for i, (k, v) in enumerate(list(db.items())[:20], 1):
            txt += f"`{i}.` ID: `{k}` | 💰 `{v.get('coins',0)} xu` | 🔢 `{v.get('uses',0)} lần`\n"
        if len(db) > 20:
            txt += f"\n_...và {len(db)-20} user khác_"
        safe_edit(txt, back_kb(), "Markdown")
        bot.answer_callback_query(call.id)
        return

    if data == "admin_view_user":
        set_session(uid, "adm_view_uid")
        safe_edit(
            "🔍 *Xem Info User*\n\n> _Gửi Telegram ID của user:_",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_broadcast":
        set_session(uid, "adm_broadcast")
        safe_edit(
            "📢 *Broadcast Tin Nhắn*\n\n> _Gửi nội dung muốn broadcast đến toàn bộ user:_",
            cancel_kb(), "Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)

# ══════════════════ MESSAGE HANDLER ══════════════════
@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_text(msg):
    uid  = msg.from_user.id
    text = msg.text.strip()
    chat = msg.chat.id
    sess = get_session(uid)
    step = sess.get("step", "")
    sdat = sess.get("data", {})

    if not step:
        return

    # Track tin nhắn user gửi vào (token, otp, email...)
    track_user_msg(uid, msg.message_id)

    def reply(txt, kb=None):
        sent = bot.send_message(chat, txt, parse_mode="Markdown", reply_markup=kb or back_kb())
        track_bot_msg(uid, sent)
        return sent

    def reply_v2(txt, kb=None):
        sent = bot.send_message(chat, txt, parse_mode="MarkdownV2", reply_markup=kb or back_kb())
        track_bot_msg(uid, sent)
        return sent

    def finish(txt, kb=None):
        """Xoá toàn bộ tin nhắn cũ, gửi kết quả sạch."""
        delete_tracked(chat, uid)
        clear_session(uid)
        bot.send_message(chat, txt, parse_mode="Markdown", reply_markup=kb or back_kb())

    # ══ BIND INFO ══
    if step == "bind_info_token":
        reply("⏳ *Đang lấy thông tin bind...*", None)
        try:
            d1, d2 = api_check_bind(text)

            # ── Fields từ get_bind_info ──
            email_cur   = d1.get("email") or d1.get("bind_email") or ""
            email_to    = d1.get("email_to_be") or ""
            mobile      = d1.get("mobile") or ""
            mobile_to   = d1.get("mobile_to_be") or ""
            countdown   = d1.get("request_exec_countdown") or 0
            result_code = d1.get("result", -1)
            bound       = bool(email_cur)

            # ── Fields từ inspect ──
            open_id  = d2.get("open_id") or "?"
            plat     = d2.get("platform", 0)
            pname    = PLATFORM_NAMES.get(int(plat) if str(plat).isdigit() else 0,
                                          f"Platform {plat}")
            acc_id   = d2.get("account_id") or d2.get("open_id") or "?"

            # ── Format countdown ──
            def fmt_cd(secs):
                if not secs or int(secs) <= 0:
                    return "Không có"
                s = int(secs)
                d = s // 86400; s %= 86400
                h = s // 3600;  s %= 3600
                m = s // 60;    s %= 60
                parts = []
                if d: parts.append(f"{d} Ngày")
                if h: parts.append(f"{h} Giờ")
                if m: parts.append(f"{m} Phút")
                if s: parts.append(f"{s} Giây")
                return " ".join(parts) if parts else "Không có"

            bind_icon   = "✅" if bound else "❌"
            status_text = "Đã bind" if bound else "Chưa bind"

            result = (
                f"ℹ️ *Thông Tin Bind*\n\n"
                f"┌──────────────────────\n"
                f"│ 🆔 Open ID: `{open_id}`\n"
                f"│ 🔑 Acc ID: `{acc_id}`\n"
                f"│ 🌐 Nền tảng: `{pname}`\n"
                f"└──────────────────────\n\n"
                f"📧 *Email:*\n"
                f"┌──────────────────────\n"
                f"│ {bind_icon} Trạng thái: *{status_text}*\n"
                f"│ 📩 Hiện tại: `{email_cur if email_cur else 'Trống'}`\n"
                f"│ 🔄 Đang chờ: `{email_to if email_to else 'Không có'}`\n"
            )
            if countdown and int(countdown) > 0:
                result += f"│ ⏱ Countdown: `{fmt_cd(countdown)}`\n"
            if mobile:
                result += f"│ 📱 Mobile: `{mobile}`\n"
            if mobile_to:
                result += f"│ 📱 Mobile mới: `{mobile_to}`\n"
            result += f"└──────────────────────"

            if not d1 and not d2:
                result = "❌ *Không lấy được dữ liệu — Token không hợp lệ hoặc đã hết hạn*"

        except Exception as e:
            result = f"❌ *Lỗi:* `{str(e)[:300]}`"
        finish(result)
        return

    # ══ LOGOUT ══
    if step == "lo_token":
        reply("⏳ *Đang xử lý logout\\.\\.\\.*", None)
        try:
            if not deduct_coins(uid):
                reply(not_enough_coins_text(get_user(uid)['coins']))
                clear_session(uid)
                return
            nick, s1, s2 = do_logout(text)
            new_coins = get_user(uid)['coins']
            result = (
                f"{'✅' if s1==200 else '❌'} *Logout {'Thành Công' if s1==200 else 'Thất Bại'}*\n\n"
                f"> _Token đã được xử lý_\n\n"
                f"┌──────────────────────\n"
                f"│ 👤 Nickname: `{nick}`\n"
                f"│ 🎮 Game server: `{s1}`\n"
                f"│ 🔑 Garena: `{s2}`\n"
                f"└──────────────────────\n\n"
                f"💰 Xu còn lại: `{new_coins} xu`"
            )
        except Exception as e:
            result = f"❌ *Lỗi khi logout:*\n`{str(e)[:200]}`"
        finish(result)
        return

    # ══ CANCEL BIND ══
    if step == "cn_token":
        reply("⏳ *Đang gửi yêu cầu hủy bind\\.\\.\\.*", None)
        try:
            if not deduct_coins(uid):
                reply(not_enough_coins_text(get_user(uid)['coins']))
                clear_session(uid)
                return
            r  = api_cancel_bind(text)
            ok = '"result": 0' in r.text
            new_coins = get_user(uid)['coins']
            result = (
                f"{'✅' if ok else '❌'} *Hủy Bind {'Thành Công' if ok else 'Thất Bại'}*\n\n"
                f"> _Yêu cầu hủy bind đã được xử lý_\n\n"
                f"💰 Xu còn lại: `{new_coins} xu`"
            )
        except Exception as e:
            result = f"❌ *Lỗi:* `{str(e)[:200]}`"
        finish(result)
        return

    # ══ UNBIND — bước từng step ══
    if step == "ub_token":
        set_session(uid, "ub_email", token=text)
        reply("🔓 *Gỡ Bind Email*\n\n**Bước 2/3** — Gửi Email cần gỡ:", cancel_kb())
        return

    if step == "ub_email":
        set_session(uid, "ub_send_otp", token=sdat["token"], email=text)
        reply("⏳ *Đang gửi OTP tới email\\.\\.\\.*", None)
        try:
            r = api_send_otp(text, sdat["token"])
            if r.get("result") == 0:
                reply(
                    f"✅ *OTP đã gửi tới:* `{text}`\n\n"
                    f"**Bước 3/3** — Nhập mã OTP nhận được:",
                    cancel_kb()
                )
                set_session(uid, "ub_otp", token=sdat["token"], email=text)
            else:
                reply(f"❌ *Gửi OTP thất bại:*\n`{r}`")
                clear_session(uid)
        except Exception as e:
            reply(f"❌ *Lỗi:* `{e}`")
            clear_session(uid)
        return

    if step == "ub_otp":
        reply("⏳ *Đang xác minh OTP và gỡ bind\\.\\.\\.*", None)
        try:
            if not deduct_coins(uid):
                reply(not_enough_coins_text(get_user(uid)['coins']))
                clear_session(uid)
                return
            rv = api_verify_identity(sdat["email"], text, sdat["token"])
            identity_token = rv.get("identity_token")
            if not identity_token:
                reply(f"❌ *Xác minh OTP thất bại:*\n`{rv}`")
                clear_session(uid)
                return
            r  = api_create_unbind(sdat["token"], identity_token)
            ok = '"result": 0' in r.text
            new_coins = get_user(uid)['coins']
            result = (
                f"{'✅' if ok else '❌'} *Gỡ Bind {'Thành Công' if ok else 'Thất Bại'}*\n\n"
                f"> _Kết quả từ Garena API_\n\n"
                f"💰 Xu còn lại: `{new_coins} xu`"
            )
        except Exception as e:
            result = f"❌ *Lỗi:* `{str(e)[:200]}`"
        finish(result)
        return

    # ══ CHANGE BIND — bước từng step ══
    if step == "cb_token":
        set_session(uid, "cb_old_email", token=text)
        reply(
            "🔄 *Đổi Email Bind*\n\n"
            "**Bước 2/4** — Gửi Email Cũ:",
            cancel_kb()
        )
        return

    if step == "cb_old_email":
        set_session(uid, "cb_new_email", token=sdat["token"], old_email=text)
        reply(
            "🔄 *Đổi Email Bind*\n\n"
            "**Bước 3/4** — Gửi Email Mới:",
            cancel_kb()
        )
        return

    if step == "cb_new_email":
        set_session(uid, "cb_send_otp_old",
                    token=sdat["token"], old_email=sdat["old_email"], new_email=text)
        reply("⏳ *Đang gửi OTP tới email cũ\\.\\.\\.*", None)
        try:
            r = api_send_otp(sdat["old_email"], sdat["token"])
            if r.get("result") == 0:
                reply(
                    f"✅ *OTP đã gửi tới email cũ:* `{sdat['old_email']}`\n\n"
                    f"**Bước 4a/5** — Nhập OTP từ email cũ:",
                    cancel_kb()
                )
                set_session(uid, "cb_otp_old",
                            token=sdat["token"], old_email=sdat["old_email"], new_email=text)
            else:
                reply(f"❌ *Gửi OTP thất bại:*\n`{r}`")
                clear_session(uid)
        except Exception as e:
            reply(f"❌ *Lỗi:* `{e}`")
            clear_session(uid)
        return

    if step == "cb_otp_old":
        reply("⏳ *Đang xác minh OTP email cũ\\.\\.\\.*", None)
        try:
            rv = api_verify_identity(sdat["old_email"], text, sdat["token"])
            identity_token = rv.get("identity_token")
            if not identity_token:
                reply(f"❌ *Xác minh OTP cũ thất bại:*\n`{rv}`")
                clear_session(uid)
                return
            r2 = api_send_otp(sdat["new_email"], sdat["token"])
            if r2.get("result") == 0:
                reply(
                    f"✅ *OTP đã gửi tới email mới:* `{sdat['new_email']}`\n\n"
                    f"**Bước 4b/5** — Nhập OTP từ email mới:",
                    cancel_kb()
                )
                set_session(uid, "cb_otp_new",
                            token=sdat["token"], old_email=sdat["old_email"],
                            new_email=sdat["new_email"], identity_token=identity_token)
            else:
                reply(f"❌ *Gửi OTP email mới thất bại:*\n`{r2}`")
                clear_session(uid)
        except Exception as e:
            reply(f"❌ *Lỗi:* `{e}`")
            clear_session(uid)
        return

    if step == "cb_otp_new":
        reply("⏳ *Đang hoàn tất đổi email\\.\\.\\.*", None)
        try:
            if not deduct_coins(uid):
                reply(not_enough_coins_text(get_user(uid)['coins']))
                clear_session(uid)
                return
            rv = api_verify_otp(sdat["new_email"], text, sdat["token"])
            verifier_token = rv.get("verifier_token")
            if not verifier_token:
                reply(f"❌ *Xác minh OTP mới thất bại:*\n`{rv}`")
                clear_session(uid)
                return
            r  = api_create_rebind(sdat["token"], sdat["identity_token"],
                                   sdat["new_email"], verifier_token)
            ok = '"result": 0' in r.text
            new_coins = get_user(uid)['coins']
            result = (
                f"{'✅' if ok else '❌'} *Đổi Email {'Thành Công' if ok else 'Thất Bại'}*\n\n"
                f"> _Yêu cầu đổi email đã được xử lý_\n\n"
                f"┌──────────────────────\n"
                f"│ 📧 Email cũ: `{sdat['old_email']}`\n"
                f"│ 📧 Email mới: `{sdat['new_email']}`\n"
                f"└──────────────────────\n\n"
                f"💰 Xu còn lại: `{new_coins} xu`"
            )
        except Exception as e:
            result = f"❌ *Lỗi:* `{str(e)[:200]}`"
        finish(result)
        return

    # ══ CHECK PLATFORM ══
    if step == "cp_token":
        reply("⏳ *Đang kiểm tra liên kết...*", None)
        try:
            if not deduct_coins(uid):
                reply(not_enough_coins_text(get_user(uid)['coins']))
                clear_session(uid)
                return
            tok, nick, aId, oId, plat, bounded, avail = do_check_platform(text)
            new_coins = get_user(uid)['coins']
            pname_main = PLATFORM_NAMES.get(plat, str(plat))

            # Build result text
            result = (
                f"🔗 *Check Liên Kết*\n\n"
                f"┌──────────────────────\n"
                f"│ 👤 Nick: `{nick}`\n"
                f"│ 🆔 Account ID: `{aId}`\n"
                f"│ 🌐 Nền tảng chính: `{pname_main}`\n"
                f"└──────────────────────\n"
            )

            if bounded:
                result += f"\n*Đang liên kết ({len(bounded)} nền tảng):*\n"
                for item in bounded:
                    pid = item.get('platform') or item.get('platform_id') or 0
                    try: pid_int = int(pid)
                    except: pid_int = 0
                    pn   = PLATFORM_NAMES.get(pid_int, f"P{pid}")
                    uid2 = str(item.get('uid') or item.get('platform_open_id') or '?')
                    uinfo= item.get('user_info') or {}
                    unick= uinfo.get('nickname') or ''
                    mail = uinfo.get('email') or ''
                    result += f"\n🔹 *{pn}*"
                    if unick: result += f" — `{unick}`"
                    result += f"\n   UID: `{uid2}`"
                    if mail: result += f" | 📧 `{mail}`"
                result += "\n"
            else:
                result += "\n> _Chưa liên kết nền tảng nào_\n"

            if avail:
                names = [PLATFORM_NAMES.get(int(p) if str(p).isdigit() else 0, f"P{p}") for p in avail]
                result += f"\n💡 Có thể liên kết: `{', '.join(names)}`\n"

            result += f"\n💰 Xu còn lại: `{new_coins} xu`"

            # Keyboard gỡ liên kết (mỗi nền tảng 1 button)
            kb_unbind = InlineKeyboardMarkup(row_width=2)
            for item in bounded:
                pid = item.get('platform') or item.get('platform_id') or 0
                try: pid_int = int(pid)
                except: pid_int = 0
                pn   = PLATFORM_NAMES.get(pid_int, f"P{pid}")
                uid2 = str(item.get('uid') or item.get('platform_open_id') or '')
                kb_unbind.add(InlineKeyboardButton(
                    f"🗑 Gỡ {pn}",
                    callback_data=f"unbind_plat:{pid_int}:{uid2}"
                ))
            kb_unbind.add(InlineKeyboardButton("🏠 Menu Chính", callback_data="back_main"))

            # Xoá tin nhắn cũ trước khi gửi kết quả
            delete_tracked(chat, uid)
            # Lưu token vào session để dùng khi gỡ (reset msg_ids sau khi xoá)
            set_session(uid, "cp_done", access_token=text, jwt_token=tok)
            bot.send_message(chat, result, parse_mode="Markdown",
                             reply_markup=kb_unbind if bounded else back_kb())
        except Exception as e:
            finish(f"❌ *Lỗi:* `{str(e)[:300]}`")
        return

    # ══ EAT → ACCESS TOKEN ══
    if step == "eat_token":
        reply("⏳ *Đang chuyển đổi EAT token\\.\\.\\.*", None)
        try:
            if not deduct_coins(uid):
                reply(not_enough_coins_text(get_user(uid)['coins']))
                clear_session(uid)
                return
            access_token = convert_eat_to_access(text)
            new_coins = get_user(uid)['coins']
            result = (
                f"✅ *Chuyển Đổi Thành Công\\!*\n\n"
                f"> _EAT token đã được chuyển sang Access Token_\n\n"
                f"┌──────────────────────────\n"
                f"│ 🔑 *Access Token:*\n"
                f"│ `{access_token}`\n"
                f"└──────────────────────────\n\n"
                f"💰 Xu còn lại: `{new_coins} xu`"
            )
        except Exception as e:
            result = f"❌ *Lỗi chuyển đổi:*\n`{str(e)[:300]}`"
        finish(result)
        return

    # ══ ADMIN STEPS ══
    if step == "adm_add_uid":
        set_session(uid, "adm_add_amount", target_uid=text)
        reply(f"➕ *Thêm xu cho user* `{text}`\n\n> _Gửi số xu muốn thêm:_", cancel_kb())
        return

    if step == "adm_add_amount":
        try:
            amount = int(text)
            new_c  = update_coins(sdat["target_uid"], amount)
            reply(
                f"✅ *Đã thêm {amount} xu cho user* `{sdat['target_uid']}`\n\n"
                f"💰 Xu mới: `{new_c} xu`"
            )
        except:
            reply("❌ *Số xu không hợp lệ\\!*")
        clear_session(uid)
        return

    if step == "adm_sub_uid":
        set_session(uid, "adm_sub_amount", target_uid=text)
        reply(f"➖ *Trừ xu của user* `{text}`\n\n> _Gửi số xu muốn trừ:_", cancel_kb())
        return

    if step == "adm_sub_amount":
        try:
            amount = int(text)
            new_c  = update_coins(sdat["target_uid"], -amount)
            reply(
                f"✅ *Đã trừ {amount} xu của user* `{sdat['target_uid']}`\n\n"
                f"💰 Xu còn lại: `{new_c} xu`"
            )
        except:
            reply("❌ *Số xu không hợp lệ\\!*")
        clear_session(uid)
        return

    if step == "adm_view_uid":
        db = load_db()
        u2 = db.get(text, {})
        if not u2:
            reply(f"❌ *Không tìm thấy user* `{text}`")
        else:
            reply(
                f"🔍 *Thông Tin User*\n\n"
                f"┌──────────────────────\n"
                f"│ 🆔 ID: `{text}`\n"
                f"│ 💰 Xu: `{u2.get('coins',0)} xu`\n"
                f"│ 🔢 Lần dùng: `{u2.get('uses',0)} lần`\n"
                f"│ 📅 Tham gia: `{u2.get('joined','?')[:10]}`\n"
                f"└──────────────────────"
            )
        clear_session(uid)
        return

    if step == "adm_broadcast":
        db      = load_db()
        success = 0
        for target in db.keys():
            try:
                bot.send_message(int(target), f"📢 *Thông Báo Từ Admin*\n\n{text}", parse_mode="Markdown")
                success += 1
                time.sleep(0.05)
            except:
                pass
        reply(f"✅ *Broadcast hoàn tất*\n\n📨 Đã gửi đến `{success}/{len(db)}` user")
        clear_session(uid)
        return

# ══════════════════ RUN ══════════════════
if __name__ == "__main__":
    print("🤖 FF Tool Bot đang chạy...")
    print(f"   Admin IDs: {ADMIN_IDS}")
    print(f"   Chi phí/lần: {COST_PER_USE} xu")
    bot.infinity_polling(timeout=30)
