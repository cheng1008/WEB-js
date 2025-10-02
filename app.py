from flask import Flask, render_template, request, jsonify
import json, os, time, traceback
from json import JSONDecodeError

app = Flask(__name__)

# 相對路徑設定（以目前執行的目錄為基準）
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# 如果資料夾不存在就建立
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 初始化 users.json
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# --- 輔助函式 ---
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except JSONDecodeError:
        # 檔案壞掉重建
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# --- 路由 ---
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
        return jsonify({"ok": True, "msg": "註冊成功"}), 200

    except Exception as e:
        app.logger.error("REGISTER ERROR:\n" + traceback.format_exc())
        return jsonify({"ok": False, "msg": "伺服器錯誤，請稍後再試"}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        username_or_email = (data.get("usernameOrEmail") or "").strip().lower()
        password = (data.get("password") or "").strip()

        users = load_users()
        user = next(
            (u for u in users if u["name"].lower() == username_or_email or u["email"].lower() == username_or_email),
            None
        )

        if not user:
            return jsonify({"ok": False, "msg": "帳號不存在"}), 404
        if user["password"] != password:
            return jsonify({"ok": False, "msg": "密碼錯誤"}), 401

        return jsonify({"ok": True, "msg": "登入成功", "user": user}), 200

    except Exception as e:
        app.logger.error("LOGIN ERROR:\n" + traceback.format_exc())
        return jsonify({"ok": False, "msg": "伺服器錯誤，請稍後再試"}), 500

if __name__ == "__main__":
    app.run(debug=True)
