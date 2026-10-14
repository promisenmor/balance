(() => {
  const form = document.getElementById("registration-form");
  const notice = document.getElementById("registration-notice");
  if (!form || !notice) return;

  const showNotice = (message, isError = false) => {
    notice.textContent = message;
    notice.className = `mt-6 rounded-xl border px-4 py-3 text-sm ${
      isError
        ? "border-rose-200 bg-rose-50 text-rose-800"
        : "border-emerald-200 bg-emerald-50 text-emerald-800"
    }`;
  };

  const errorMessage = (data) => {
    if (typeof data.detail === "string") return data.detail;
    return Object.entries(data)
      .flatMap(([field, errors]) =>
        (Array.isArray(errors) ? errors : [errors]).map((error) =>
          `${field}: ${typeof error === "string" ? error : JSON.stringify(error)}`,
        ),
      )
      .join(" ");
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    const fields = new FormData(form);
    const password = fields.get("password1");
    const confirmation = fields.get("password2");
    if (password !== confirmation) {
      showNotice("The passwords do not match.", true);
      form.elements.password2.focus();
      return;
    }

    button.disabled = true;
    try {
      const response = await fetch("/api/auth/registration/", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({
          email: fields.get("email"),
          password1: password,
          password2: confirmation,
        }),
      });
      let data;
      try {
        data = await response.json();
      } catch (error) {
        if (!(error instanceof SyntaxError)) throw error;
        throw new Error(`Registration failed (${response.status}). Please try again.`);
      }
      if (!response.ok) {
        throw new Error(errorMessage(data) || `Registration failed (${response.status}).`);
      }
      form.reset();
      form.hidden = true;
      showNotice("Account created. Check your email for a verification link before signing in.");
    } catch (error) {
      showNotice(error.message || "Registration failed. Please try again.", true);
    } finally {
      button.disabled = false;
    }
  });
})();
