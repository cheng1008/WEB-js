document.addEventListener("DOMContentLoaded", () => {
  const loading = document.getElementById("security-loading");
  const loginContainer = document.getElementById("login-container");
  const registerContainer = document.getElementById("register-container");

  setTimeout(() => {
    loading.style.display = "none";
    loginContainer.classList.remove("hidden");
  }, 2500);

  document.getElementById("show-register").addEventListener("click", () => {
    loginContainer.classList.add("hidden");
    registerContainer.classList.remove("hidden");
  });
  document.getElementById("show-login").addEventListener("click", () => {
    registerContainer.classList.add("hidden");
    loginContainer.classList.remove("hidden");
  });

  document.getElementById("login-btn").addEventListener("click", async () => {
    const usernameOrEmail = document.getElementById("login-username").value.trim().toLowerCase();
    const password = document.getElementById("login-password").value.trim();

    if (!usernameOrEmail || !password) {
      alert("請輸入帳號與密碼！");
      return;
    }

    try {
      const res = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usernameOrEmail, password }),
      });
      const data = await res.json();

      if (!data.ok) {
        alert(data.msg);
        return;
      }

      localStorage.setItem("currentUser", JSON.stringify(data.user));
      window.location.href = "/success";
    } catch (err) {
      alert("伺服器錯誤，請稍後再試！");
      console.error(err);
    }
  });
});
