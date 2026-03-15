#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║        FREE FIRE TOOL - FLASK WEB VERSION                    ║
# ║        Garena Account Manager · Web UI                       ║
# ╚══════════════════════════════════════════════════════════════╝

from flask import Flask, render_template, request, jsonify, session
import requests as req
import json, os, time, uuid
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import urllib3
urllib3.disable_warnings()

# ── Import core logic ──
from core import (
    gLogin, do_logout,
    api_check_bind, api_send_otp, api_verify_identity,
    api_verify_otp, api_create_rebind, api_create_unbind,
    api_cancel_bind, convert_eat_to_access,
    do_check_platform, do_unbind_platform,
    PLATFORM_NAMES,
)

app = Flask(__name__)
app.secret_key = os.urandom(32)

# ── In-memory OTP state (keyed by session_id) ──
otp_state = {}

# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def ok(data=None, **kw):
    return jsonify({"ok": True, "data": data or kw})

def err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code

def fmt_cd(secs):
    if not secs or int(secs) <= 0: return None
    s = int(secs)
    d = s // 86400; s %= 86400
    h = s // 3600;  s %= 3600
    m = s // 60;    s %= 60
    parts = []
    if d: parts.append(f"{d} Ngày")
    if h: parts.append(f"{h} Giờ")
    if m: parts.append(f"{m} Phút")
    if s: parts.append(f"{s} Giây")
    return " ".join(parts)

# ══════════════════════════════════════════════════════════
#  ROUTES — PAGES
# ══════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")

# ══════════════════════════════════════════════════════════
#  API — BIND INFO
# ══════════════════════════════════════════════════════════
@app.route("/api/bind-info", methods=["POST"])
def api_bind_info():
    token = request.json.get("token", "").strip()
    if not token:
        return err("Token không được để trống")
    try:
        d1, d2 = api_check_bind(token)
        email_cur  = d1.get("email") or d1.get("bind_email") or ""
        email_to   = d1.get("email_to_be") or ""
        mobile     = d1.get("mobile") or ""
        mobile_to  = d1.get("mobile_to_be") or ""
        countdown  = d1.get("request_exec_countdown") or 0
        result_code= d1.get("result", -1)
        open_id    = d2.get("open_id") or "?"
        plat       = d2.get("platform", 0)
        pname      = PLATFORM_NAMES.get(int(plat) if str(plat).isdigit() else 0, f"Platform {plat}")
        acc_id     = d2.get("account_id") or d2.get("open_id") or "?"
        return ok(
            email=email_cur,
            email_to_be=email_to,
            mobile=mobile,
            mobile_to_be=mobile_to,
            countdown=countdown,
            countdown_fmt=fmt_cd(countdown),
            result_code=result_code,
            bound=bool(email_cur),
            open_id=open_id,
            account_id=acc_id,
            platform=pname,
        )
    except Exception as e:
        return err(str(e))

# ══════════════════════════════════════════════════════════
#  API — LOGOUT
# ══════════════════════════════════════════════════════════
@app.route("/api/logout", methods=["POST"])
def api_logout():
    token = request.json.get("token", "").strip()
    if not token:
        return err("Token không được để trống")
    try:
        nick, s1, s2 = do_logout(token)
        success = s1 == 200
        return ok(nickname=nick, game_status=s1, garena_status=s2, success=success)
    except Exception as e:
        return err(str(e))

# ══════════════════════════════════════════════════════════
#  API — EAT → ACCESS TOKEN
# ══════════════════════════════════════════════════════════
@app.route("/api/eat-convert", methods=["POST"])
def api_eat_convert():
    eat = request.json.get("eat_token", "").strip()
    if not eat:
        return err("EAT token không được để trống")
    try:
        access_token = convert_eat_to_access(eat)
        return ok(access_token=access_token)
    except Exception as e:
        return err(str(e))

# ══════════════════════════════════════════════════════════
#  API — CHECK PLATFORM LINKS
# ══════════════════════════════════════════════════════════
@app.route("/api/check-platform", methods=["POST"])
def api_check_plat():
    token = request.json.get("token", "").strip()
    if not token:
        return err("Token không được để trống")
    try:
        tok, nick, aId, oId, plat, bounded, avail = do_check_platform(token)
        pname_main = PLATFORM_NAMES.get(plat, str(plat))
        bounded_fmt = []
        for item in bounded:
            pid = item.get("platform") or item.get("platform_id") or 0
            try: pid_int = int(pid)
            except: pid_int = 0
            uid2   = str(item.get("uid") or item.get("platform_open_id") or "?")
            uinfo  = item.get("user_info") or {}
            bounded_fmt.append({
                "pid": pid_int,
                "platform_name": PLATFORM_NAMES.get(pid_int, f"Platform {pid_int}"),
                "uid": uid2,
                "nickname": uinfo.get("nickname") or "",
                "email": uinfo.get("email") or "",
            })
        avail_fmt = [PLATFORM_NAMES.get(int(p) if str(p).isdigit() else 0, f"P{p}") for p in (avail or [])]
        # Store jwt in server-side dict (keyed by a sid)
        sid = str(uuid.uuid4())
        otp_state[sid] = {"access_token": token, "jwt_token": tok, "ts": time.time()}
        return ok(
            sid=sid,
            nickname=nick,
            account_id=aId,
            open_id=oId,
            platform=pname_main,
            bounded=bounded_fmt,
            available=avail_fmt,
        )
    except Exception as e:
        return err(str(e))

@app.route("/api/unbind-platform", methods=["POST"])
def api_unbind_plat():
    data   = request.json or {}
    sid    = data.get("sid", "")
    pid    = data.get("pid")
    uid_str= data.get("uid", "")
    state  = otp_state.get(sid)
    if not state:
        return err("Phiên hết hạn — vui lòng check lại")
    try:
        pid_int  = int(pid)
        pname    = PLATFORM_NAMES.get(pid_int, f"Platform {pid_int}")
        status   = do_unbind_platform(state["access_token"], state["jwt_token"], pid_int, uid_str)
        if status == 200:
            return ok(message=f"Gỡ {pname} thành công", platform=pname)
        else:
            return err(f"Thất bại — HTTP {status}")
    except Exception as e:
        return err(str(e))

# ══════════════════════════════════════════════════════════
#  API — CANCEL BIND
# ══════════════════════════════════════════════════════════
@app.route("/api/cancel-bind", methods=["POST"])
def api_cancel():
    token = request.json.get("token", "").strip()
    if not token:
        return err("Token không được để trống")
    try:
        r = api_cancel_bind(token)
        success = '"result": 0' in r.text
        return ok(success=success, raw=r.text[:300])
    except Exception as e:
        return err(str(e))

# ══════════════════════════════════════════════════════════
#  API — CHANGE BIND EMAIL (multi-step via state)
# ══════════════════════════════════════════════════════════
@app.route("/api/change-bind/step1", methods=["POST"])
def change_bind_step1():
    """Gửi OTP tới email cũ."""
    data      = request.json or {}
    token     = data.get("token", "").strip()
    old_email = data.get("old_email", "").strip()
    new_email = data.get("new_email", "").strip()
    if not all([token, old_email, new_email]):
        return err("Thiếu token / email cũ / email mới")
    try:
        r = api_send_otp(old_email, token)
        if r.get("result") != 0:
            return err(f"Gửi OTP tới email cũ thất bại: {r}")
        sid = str(uuid.uuid4())
        otp_state[sid] = {
            "token": token, "old_email": old_email,
            "new_email": new_email, "step": "otp_old", "ts": time.time()
        }
        return ok(sid=sid, message=f"OTP đã gửi tới {old_email}")
    except Exception as e:
        return err(str(e))

@app.route("/api/change-bind/step2", methods=["POST"])
def change_bind_step2():
    """Xác minh OTP email cũ → gửi OTP email mới."""
    data    = request.json or {}
    sid     = data.get("sid", "")
    otp_old = data.get("otp", "").strip()
    state   = otp_state.get(sid)
    if not state or state.get("step") != "otp_old":
        return err("Phiên không hợp lệ hoặc đã hết hạn")
    try:
        rv = api_verify_identity(state["old_email"], otp_old, state["token"])
        identity_token = rv.get("identity_token")
        if not identity_token:
            return err(f"OTP email cũ không đúng: {rv}")
        r2 = api_send_otp(state["new_email"], state["token"])
        if r2.get("result") != 0:
            return err(f"Gửi OTP email mới thất bại: {r2}")
        otp_state[sid]["identity_token"] = identity_token
        otp_state[sid]["step"] = "otp_new"
        return ok(message=f"OTP đã gửi tới {state['new_email']}")
    except Exception as e:
        return err(str(e))

@app.route("/api/change-bind/step3", methods=["POST"])
def change_bind_step3():
    """Xác minh OTP email mới → hoàn tất đổi bind."""
    data    = request.json or {}
    sid     = data.get("sid", "")
    otp_new = data.get("otp", "").strip()
    state   = otp_state.get(sid)
    if not state or state.get("step") != "otp_new":
        return err("Phiên không hợp lệ hoặc đã hết hạn")
    try:
        rv = api_verify_otp(state["new_email"], otp_new, state["token"])
        verifier_token = rv.get("verifier_token")
        if not verifier_token:
            return err(f"OTP email mới không đúng: {rv}")
        r = api_create_rebind(state["token"], state["identity_token"],
                              state["new_email"], verifier_token)
        success = '"result": 0' in r.text
        del otp_state[sid]
        return ok(success=success,
                  message="Đổi email bind thành công!" if success else "Đổi email bind thất bại")
    except Exception as e:
        return err(str(e))

# ══════════════════════════════════════════════════════════
#  API — UNBIND EMAIL (multi-step)
# ══════════════════════════════════════════════════════════
@app.route("/api/unbind-email/step1", methods=["POST"])
def unbind_email_step1():
    data  = request.json or {}
    token = data.get("token", "").strip()
    email = data.get("email", "").strip()
    if not all([token, email]):
        return err("Thiếu token / email")
    try:
        r = api_send_otp(email, token)
        if r.get("result") != 0:
            return err(f"Gửi OTP thất bại: {r}")
        sid = str(uuid.uuid4())
        otp_state[sid] = {"token": token, "email": email, "step": "unbind_otp", "ts": time.time()}
        return ok(sid=sid, message=f"OTP đã gửi tới {email}")
    except Exception as e:
        return err(str(e))

@app.route("/api/unbind-email/step2", methods=["POST"])
def unbind_email_step2():
    data  = request.json or {}
    sid   = data.get("sid", "")
    otp   = data.get("otp", "").strip()
    state = otp_state.get(sid)
    if not state or state.get("step") != "unbind_otp":
        return err("Phiên không hợp lệ")
    try:
        rv = api_verify_identity(state["email"], otp, state["token"])
        identity_token = rv.get("identity_token")
        if not identity_token:
            return err(f"OTP không đúng: {rv}")
        r = api_create_unbind(state["token"], identity_token)
        success = '"result": 0' in r.text
        del otp_state[sid]
        return ok(success=success,
                  message="Gỡ bind email thành công!" if success else "Gỡ bind thất bại")
    except Exception as e:
        return err(str(e))

# ══════════════════════════════════════════════════════════
#  CLEANUP old states every 30min
# ══════════════════════════════════════════════════════════
@app.before_request
def cleanup_states():
    now = time.time()
    expired = [k for k, v in otp_state.items() if now - v.get("ts", now) > 1800]
    for k in expired:
        del otp_state[k]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
