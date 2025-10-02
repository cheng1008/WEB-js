document.addEventListener("DOMContentLoaded", () => {
  const nameInput = document.getElementById("register-name");
  const emailInput = document.getElementById("register-email");
  const passwordInput = document.getElementById("register-password");
  const confirmInput = document.getElementById("register-confirm");

  const nameError = document.getElementById("name-error");
  const emailError = document.getElementById("email-error");
  const passwordError = document.getElementById("password-error");
  const confirmError = document.getElementById("confirm-error");

  const clearErrors = () => {
    [nameError, emailError, passwordError, confirmError].forEach(e => e.textContent = "");
    [nameInput, emailInput, passwordInput, confirmInput].forEach(i => i.classList.remove("error"));
  };

  document.getElementById("register-btn").addEventListener("click", async () => {
    clearErrors();
    const name = nameInput.value.trim();
    const email = emailInput.value.trim().toLowerCase();
    const password = passwordInput.value.trim();
    const confirm = confirmInput.value.trim();

    let hasError = false;

    if (!name) { nameError.textContent = "請輸入使用者名稱"; nameInput.classList.add("error"); hasError = true; }
    if (!email) { emailError.textContent = "請輸入電子郵件"; emailInput.classList.add("error"); hasError = true; }
    else if (!email.endsWith("@gmail.com")) { emailError.textContent = "電子郵件格式錯誤（需為 @gmail.com）"; emailInput.classList.add("error"); hasError = true; }
    if (!password) { passwordError.textContent = "請設定密碼"; passwordInput.classList.add("error"); hasError = true; }
    if (password !== confirm) { confirmError.textContent = "兩次密碼輸入不一致"; confirmInput.classList.add("error"); hasError = true; }

    if (hasError) return;

    try {
      const res = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      const ct = res.headers.get("content-type") || "";
      let data = {};
      if (ct.includes("application/json")) {
        data = await res.json();
      } else {
        const text = await res.text();
        console.error("Non-JSON:", text);
        emailError.textContent = `伺服器回傳非 JSON（HTTP ${res.status}）`;
        return;
      }

      if (!res.ok || !data.ok) {
        emailError.textContent = data.msg || "註冊失敗";
        return;
      }

      [nameInput, emailInput, passwordInput, confirmInput].forEach(i => i.value = "");
      clearErrors();
      document.getElementById("register-container").classList.add("hidden");
      document.getElementById("login-container").classList.remove("hidden");
    } catch (err) {
      console.error(err);
      emailError.textContent = "伺服器錯誤，請稍後再試";
    }
  });
});
