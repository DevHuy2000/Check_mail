#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║  CORE LOGIC — dùng chung cho Bot Telegram & Flask Web        ║
# ╚══════════════════════════════════════════════════════════════╝

import requests, urllib3, jwt as jwtLib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import MajorLoginRes_pb2 as mLrPb

urllib3.disable_warnings()

# ══════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════
AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'

mLuRl = "https://loginbp.ggpolarbear.com/MajorLogin"
iNuRl = "https://100067.connect.garena.com/oauth/token/inspect?token={t}"
bNuRl = "https://100067.connect.garena.com/bind/app/platform/info/get"
bIdUr = "https://clientbp.ggpolarbear.com/BindDelete"

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
HDR_BIND = {
    "User-Agent":   "GarenaMSDK/4.0.30",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept":       "application/json",
}
HDR_BIND_INFO = {
    "User-Agent":      "GarenaMSDK/4.0.19P9(Redmi Note 5;Android 9;en;US;)",
    "Accept":          "application/json",
    "Accept-Encoding": "gzip",
    "Connection":      "Keep-Alive",
}
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
    1: "Facebook", 2: "VK",     4: "Google",
    7: "Guest",    8: "Garena", 9: "Huawei",
    11: "Twitter", 12: "Apple",
}

# ══════════════════════════════════════════════════════════
#  CRYPTO
# ══════════════════════════════════════════════════════════
def encA(d): return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))
def decA(d): return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

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
        _s(1,ts) + _s(4,"free fire") + _i(5,1) + _s(7,"1.120.2")
      + _s(8,"Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)")
      + _s(9,"Handheld") + _s(10,"Verizon") + _s(11,"WIFI")
      + _i(12,1920) + _i(13,1080) + _s(14,"280")
      + _s(15,"ARM64 FP ASIMD AES VMH | 2865 | 4") + _i(16,3003)
      + _s(17,"Adreno (TM) 640") + _s(18,"OpenGL ES 3.1 v1.46")
      + _s(19,"Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57")
      + _s(20,"223.191.51.89") + _s(21,"en")
      + _s(22,oId) + _s(23,p) + _s(24,"Handheld") + _s(25,"07@Q")
      + _s(29,tok) + _i(30,1)
      + _s(41,"Verizon") + _s(42,"WIFI")
      + _s(57,"7428b253defc164018c604a1ebbfebdf")
      + _i(60,36235)+_i(61,31335)+_i(62,2519)+_i(63,703)
      + _i(64,25010)+_i(65,26628)+_i(66,32992)+_i(67,36235)
      + _i(73,3)
      + _s(74,"/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64")
      + _i(76,1)
      + _s(77,"5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk")
      + _i(78,3)+_i(79,2)
      + _s(81,"64") + _s(83,"2019118695") + _s(86,"OpenGLES2")
      + _i(87,16383)+_i(88,4)
      + _s(89,"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg==")
      + _i(92,13564) + _s(93,"android")
      + _s(94,"KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY=")
      + _i(95,110009)+_i(97,1)+_i(98,1)
      + _s(99,p)+_s(100,p)
    )
    return encA(pl)

# ══════════════════════════════════════════════════════════
#  CORE API FUNCTIONS
# ══════════════════════════════════════════════════════════
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
    try:    res.ParseFromString(decA(x.content))
    except: res.ParseFromString(x.content)
    if not res.token:
        raise Exception("Token rỗng từ server")
    cl   = jwtLib.decode(res.token, options={"verify_signature": False})
    aId  = cl.get('account_id', getattr(res, 'account_id', oId))
    nick = cl.get('nickname', 'Unknown')
    return res.token, nick, aId, oId, plat

def do_logout(aT):
    tok, nick, *_ = gLogin(aT)
    pkt = _s(1,aT) + _s(2,"Android|00000000-0000-0000-0000-000000000000") + _s(3,"samsung SM-T505N")
    enc = encA(pkt)
    hd  = {**lOhDr, "Authorization": f"Bearer {tok}"}
    r1  = requests.post("https://clientbp.ggpolarbear.com/Logout",
                        headers=hd, data=enc, verify=False, timeout=10)
    r2  = requests.get(f"https://100067.connect.garena.com/oauth/logout?access_token={aT}",
                       headers=iNhDr, timeout=10)
    return nick, r1.status_code, r2.status_code

def api_check_bind(access_token):
    url1 = "https://auth.garena.com/game/account_security/bind:get_bind_info"
    try:
        r1 = requests.get(url1, params={"app_id":"100067","access_token":access_token},
                          headers=HDR_BIND_INFO, timeout=12)
        r1.raise_for_status()
        d1 = r1.json()
    except: d1 = {}
    url2 = "https://100067.connect.garena.com/oauth/token/inspect?token=" + access_token
    try:
        r2 = requests.get(url2, headers=HDR_BIND, timeout=10)
        d2 = r2.json()
    except: d2 = {}
    return d1, d2

def api_send_otp(email, access_token):
    r = requests.post(
        "https://100067.connect.garena.com/game/account_security/bind:send_otp",
        headers=HDR_BIND,
        data={"email":email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":access_token},
        timeout=10)
    return r.json()

def api_verify_identity(email, otp, access_token):
    r = requests.post(
        "https://100067.connect.garena.com/game/account_security/bind:verify_identity",
        headers=HDR_BIND,
        data={"email":email,"app_id":"100067","access_token":access_token,"otp":otp},
        timeout=10)
    return r.json()

def api_verify_otp(email, otp, access_token):
    r = requests.post(
        "https://100067.connect.garena.com/game/account_security/bind:verify_otp",
        headers=HDR_BIND,
        data={"email":email,"app_id":"100067","access_token":access_token,"otp":otp},
        timeout=10)
    return r.json()

def api_create_rebind(access_token, identity_token, new_email, verifier_token):
    return requests.post(
        "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request",
        headers=HDR_BIND,
        data={"identity_token":identity_token,"email":new_email,"app_id":"100067",
              "verifier_token":verifier_token,"access_token":access_token},
        timeout=10)

def api_create_unbind(access_token, identity_token):
    return requests.post(
        "https://100067.connect.gopapi.io/game/account_security/bind:create_unbind_request",
        headers=HDR_BIND,
        data={"app_id":"100067","access_token":access_token,"identity_token":identity_token},
        timeout=10)

def api_cancel_bind(access_token):
    return requests.post(
        "https://100067.connect.gopapi.io/game/account_security/bind:cancel_request",
        headers=HDR_BIND,
        data={"app_id":"100067","access_token":access_token},
        timeout=10)

def convert_eat_to_access(eat_token):
    r = requests.get(
        f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}",
        allow_redirects=False, timeout=10)
    location = r.headers.get("Location", "")
    if not location:
        raise Exception("Không nhận được redirect — Token không hợp lệ hoặc hết hạn")
    access_token = parse_qs(urlparse(location).query).get("access_token", [None])[0]
    if not access_token:
        raise Exception(f"Không tìm thấy access_token trong: {location}")
    return access_token

def do_check_platform(aT):
    tok, nick, aId, oId, plat = gLogin(aT)
    r = requests.get(bNuRl, params={"access_token":aT},
                     headers={"User-Agent":"GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
                               "Connection":"Keep-Alive","Accept-Encoding":"gzip"},
                     timeout=10)
    d = r.json()
    if isinstance(d, dict) and 'data' in d: d = d['data']
    bounded = avail = []
    if isinstance(d, dict):
        bounded = d.get('bounded_accounts') or d.get('list') or d.get('bind_list') or []
        avail   = d.get('available_platforms') or []
    return tok, nick, aId, oId, plat, bounded, avail

def do_unbind_platform(aT, tok, pid_int, uid_str):
    pkt = _s(1,aT) + _s(2,str(pid_int)) + _s(3,uid_str)
    enc = encA(pkt)
    hd  = {**bIdHd, "Authorization": f"Bearer {tok}"}
    r   = requests.post(bIdUr, headers=hd, data=enc, verify=False, timeout=10)
    return r.status_code
