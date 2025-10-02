from flask import Flask, render_template, request, jsonify
import json, os, time, traceback, uuid
from json import JSONDecodeError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# === 載入 .env（本機測試用，Render 會使用 Environment Variables） ===
load_dotenv()

app = Flask(__name__)

# === 資料儲存 ===
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# === Gmail 寄信設定 ===
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

def send_verification_email(to_email, username, token, base_url):
    """寄送 Gmail 驗證信"""
    if not (GMAIL_USER and GMAIL_PASS):
        print("⚠️ 未設定 GMAIL_USER/GMAIL_PASS，略過寄信")
        return False

    verify_url = f"{base_url}/verify?email={to_email}&token={token}"
    subject = "帳號註冊驗證信"
    body = f"""
親愛的 {username} 您好：

感謝您註冊本站服務！

✅ 請點擊以下連結完成信箱驗證：
{verify_url}

若無法點擊，請將上方網址貼到瀏覽器開啟。

此致，
Flask 登入系統 敬上
"""

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print(f"✅ 驗證信已寄出至 {to_email}")
        return True
    except Exception as e:
        print("❌ 寄信失敗：", e)
        return False

# === 輔助方法 ===
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except JSONDecodeError:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# === 頁面 ===
@app.route("/")
def index():
    time.sleep(1.5)  # 防爆破 loading
    return render_template("index.html")

@app.route("/success")
def success():
    return render_template("success.html")

# === 註冊 API ===
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(force=True)
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = (data.get("password") or "").strip()

        if not name or not email or not password:
            return jsonify({"ok": False, "msg": "請完整填寫所有欄位"}), 400
        if not email.endswith("@gmail.com"):
            return jsonify({"ok": False, "msg": "電子郵件格式錯誤（需為 Gmail）"}), 400

        users = load_users()
        if any(u["name"].lower() == name.lower() or u["email"].lower() == email for u in users):
            return jsonify({"ok": False, "msg": "使用者名稱或電子郵件已存在"}), 409

        token = str(uuid.uuid4())
        users.append({
            "name": name,
            "email": email,
            "password": password,
            "verified": False,
            "token": token
        })
        save_users(users)

        # Render 上的 HTTPS 連結會自動從 Proxy Header 判斷
        base_url = request.headers.get("X-Forwarded-Proto", request.scheme) + "://" + request.headers.get("X-Forwarded-Host", request.host)
        send_verification_email(email, name, token, base_url)

        return jsonify({"ok": True, "msg": "註冊成功，請至信箱點擊驗證連結"}), 200
    except Exception as e:
        app.logger.error("REGISTER ERROR:\n" + traceback.format_exc())
        return jsonify({"ok": False, "msg": "伺服器錯誤"}), 500

# === 登入 API ===
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        username_or_email = (data.get("usernameOrEmail") or "").strip().lower()
        password = (data.get("password") or "").strip()

        users = load_users()
        user = next((u for u in users if u["name"].lower() == username_or_email or u["email"].lower() == username_or_email), None)

        if not user:
            return jsonify({"ok": False, "msg": "帳號不存在"}), 404
        if user["password"] != password:
            return jsonify({"ok": False, "msg": "密碼錯誤"}), 401
        if not user.get("verified", False):
            return jsonify({"ok": False, "msg": "請先完成信箱驗證後再登入"}), 403

        return jsonify({"ok": True, "msg": "登入成功", "user": user}), 200
    except Exception:
        app.logger.error("LOGIN ERROR:\n" + traceback.format_exc())
        return jsonify({"ok": False, "msg": "伺服器錯誤"}), 500

# === 驗證連結 ===
@app.route("/verify")
def verify():
    email = (request.args.get("email") or "").strip().lower()
    token = (request.args.get("token") or "").strip()

    users = load_users()
    for u in users:
        if u["email"] == email and u.get("token") == token:
            u["verified"] = True
            u["token"] = ""
            save_users(users)
            return render_template("verify.html", ok=True, email=email)
    return render_template("verify.html", ok=False, email=email)

# === 主程式入口（Render 版不使用 ngrok） ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
