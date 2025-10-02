from flask import Flask, render_template, request, jsonify
import json, os, time, traceback, datetime
from json import JSONDecodeError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pyngrok import ngrok

# === 初始化 Flask ===
app = Flask(__name__)

# === 檔案設定 ===
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
LOG_FILE = "login_log.txt"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# === Gmail 寄信設定 ===
GMAIL_USER = "airing777xx@gmail.com"       # 你的 Gmail
GMAIL_PASS = "dyctctnluxecpoqn"            # Gmail 應用程式密碼

def send_verification_email(to_email, username):
    """寄送驗證信"""
    subject = "帳號註冊驗證信"
    body = f"""
    親愛的 {username} 您好：

    感謝您註冊本網站服務！

    ✅ 這是一封驗證郵件，請確認您的信箱正確。
    您現在可以回到網站登入系統。

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

# === 輔助函式 ===
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except JSONDecodeError:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# === 路由 ===
@app.route("/")
def index():
    time.sleep(2.5)
    return render_template("index.html")

@app.route("/success")
def success():
    return render_template("success.html")

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

        users.append({"name": name, "email": email, "password": password})
        save_users(users)

        # ✅ 註冊成功後寄出驗證信
        send_verification_email(email, name)

        return jsonify({"ok": True, "msg": "註冊成功，驗證信已寄出"}), 200

    except Exception as e:
        app.logger.error("REGISTER ERROR:\n" + traceback.format_exc())
        return jsonify({"ok": False, "msg": "伺服器錯誤"}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        username_or_email = (data.get("usernameOrEmail") or "").strip().lower()
        password = (data.get("password") or "").strip()
        user_ip = request.remote_addr  # ✅ 取得使用者 IP

        users = load_users()
        user = next(
            (u for u in users if u["name"].lower() == username_or_email or u["email"].lower() == username_or_email),
            None
        )

        if not user:
            return jsonify({"ok": False, "msg": "帳號不存在"}), 404
        if user["password"] != password:
            return jsonify({"ok": False, "msg": "密碼錯誤"}), 401

        # ✅ 登入成功：印出與記錄 Email + IP
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{now}] 使用者登入：{user['email']} | IP：{user_ip}\n"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)

        print(f"📩 {log_entry.strip()}")

        return jsonify({"ok": True, "msg": "登入成功", "user": user}), 200

    except Exception as e:
        app.logger.error("LOGIN ERROR:\n" + traceback.format_exc())
        return jsonify({"ok": False, "msg": "伺服器錯誤"}), 500

# === Ngrok 公開網址 ===
if __name__ == "__main__":
    public_url = ngrok.connect(5000)
    print("🔗 公開網址:", public_url)
    app.run()
