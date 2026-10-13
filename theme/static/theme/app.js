(() => {
  const root = document.querySelector("[data-page]");
  if (!root) return;

  const page = root.dataset.page;
  const notice = document.getElementById("page-notice");
  const currency = new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    maximumFractionDigits: 2,
  });
  const csrfToken = () => {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) return input.value;
    const cookie = document.cookie.split("; ").find((part) => part.startsWith("csrftoken="));
    return cookie ? decodeURIComponent(cookie.slice("csrftoken=".length)) : "";
  };

  const showNotice = (message, isError = false) => {
    if (!notice) return;
    notice.textContent = message;
    notice.className = `mb-5 rounded-xl border px-4 py-3 text-sm ${
      isError
        ? "border-rose-200 bg-rose-50 text-rose-800"
        : "border-emerald-200 bg-emerald-50 text-emerald-800"
    }`;
  };

  const request = async (path, options = {}) => {
    const headers = { Accept: "application/json", ...(options.headers || {}) };
    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
      headers["X-CSRFToken"] = csrfToken();
    }
    const response = await fetch(`/api/${path}`, {
      ...options,
      headers,
      credentials: "same-origin",
    });
    if (response.status === 401) {
      window.location.assign(`/login/?next=${encodeURIComponent(window.location.pathname)}`);
      throw new Error("Your session has expired. Please sign in again.");
    }
    if (!response.ok) {
      let detail = `Request failed (${response.status}).`;
      try {
        const data = await response.json();
        if (typeof data.detail === "string") detail = data.detail;
        else {
          const messages = Object.entries(data).flatMap(([field, errors]) =>
            (Array.isArray(errors) ? errors : [errors]).map((error) =>
              `${field}: ${typeof error === "string" ? error : JSON.stringify(error)}`,
            ),
          );
          if (messages.length) detail = messages.join(" ");
        }
      } catch (error) {
        if (error instanceof SyntaxError) detail = `Request failed (${response.status}).`;
        else throw error;
      }
      throw new Error(detail);
    }
    if (response.status === 204) return null;
    return response.json();
  };

  const el = (tag, className = "", text = "") => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== "") node.textContent = text;
    return node;
  };

  const addText = (parent, tag, className, text) => {
    const node = el(tag, className, text);
    parent.append(node);
    return node;
  };

  const money = (value) => currency.format(Number(value) || 0);
  const dateLabel = (value, options = { day: "numeric", month: "short", year: "numeric" }) => {
    if (!value) return "No date";
    const date = new Date(`${value.slice(0, 10)}T00:00:00`);
    return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat("en", options).format(date);
  };
  const empty = (parent, text, className = "py-8 text-center text-sm text-slate-500") => {
    parent.replaceChildren(el("p", className, text));
  };
  const getList = async (endpoint) => {
    const data = await request(endpoint);
    if (!Array.isArray(data)) throw new Error("The API returned an unexpected list response.");
    return data;
  };
  const dialog = (id) => document.getElementById(id);
  const formData = (form) => {
    const data = Object.fromEntries(new FormData(form).entries());
    delete data.csrfmiddlewaretoken;
    return data;
  };
  const todayInputValue = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  };
  const submitForm = (form, endpoint, method, afterSave) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector('button[type="submit"]');
      if (button) button.disabled = true;
      try {
        await request(endpoint, { method, body: JSON.stringify(formData(form)) });
        form.reset();
        const modal = form.closest("dialog");
        if (modal?.open) modal.close();
        showNotice("Saved successfully.");
        await afterSave();
      } catch (error) {
        showNotice(error.message, true);
      } finally {
        if (button) button.disabled = false;
      }
    });
  };

  document.querySelectorAll("[data-open-dialog]").forEach((button) => {
    button.addEventListener("click", () => dialog(button.dataset.openDialog)?.showModal());
  });
  document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => dialog(button.dataset.closeDialog)?.close());
  });
  document.querySelectorAll("[data-today]").forEach((input) => {
    const now = new Date();
    input.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  });

  const createProgress = (parent, percent, color = "bg-indigo-500") => {
    const track = el("div", "h-2 overflow-hidden rounded-full bg-slate-100");
    const bar = el("div", `h-full rounded-full transition-all ${color}`);
    bar.style.width = `${Math.min(Math.max(Number(percent) || 0, 0), 100)}%`;
    track.append(bar);
    parent.append(track);
  };

  const renderTransactionLine = (parent, transaction, compact = false) => {
    const row = el("div", `flex items-center justify-between gap-4 ${compact ? "py-3" : "py-4"}`);
    const details = el("div", "flex min-w-0 items-center gap-3");
    const positive = transaction.transaction_type === "income";
    const mark = el(
      "span",
      `grid size-10 shrink-0 place-items-center rounded-xl text-sm font-bold ${positive ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`,
      positive ? "↙" : "↗",
    );
    const text = el("div", "min-w-0");
    addText(text, "p", "truncate text-sm font-semibold text-slate-900", transaction.description || transaction.category);
    addText(text, "p", "mt-1 truncate text-xs capitalize text-slate-500", `${transaction.category} · ${dateLabel(transaction.transaction_date)}`);
    details.append(mark, text);
    row.append(details);
    addText(
      row,
      "p",
      `shrink-0 text-sm font-bold ${positive ? "text-emerald-700" : "text-slate-900"}`,
      `${positive ? "+" : "−"}${money(transaction.amount)}`,
    );
    parent.append(row);
    return row;
  };

  const budgetTone = (level) => ({
    none: "bg-emerald-500",
    warning: "bg-amber-500",
    exceeded: "bg-rose-500",
  })[level] || "bg-indigo-500";
  const budgetBadge = (level) => ({
    none: ["On track", "bg-emerald-50 text-emerald-700"],
    warning: ["Heads up", "bg-amber-50 text-amber-700"],
    exceeded: ["Over limit", "bg-rose-50 text-rose-700"],
  })[level] || ["On track", "bg-slate-100 text-slate-600"];

  const renderBudget = (parent, budget, options = {}) => {
    const card = el("article", options.compact ? "rounded-xl border border-slate-100 p-4" : "panel");
    const heading = el("div", "flex items-start justify-between gap-3");
    const title = el("div");
    addText(title, "h3", "font-bold capitalize text-slate-950", budget.category);
    addText(title, "p", "mt-1 text-xs capitalize text-slate-500", `${budget.period} · ${dateLabel(budget.period_start, { day: "numeric", month: "short" })} – ${dateLabel(budget.period_end, { day: "numeric", month: "short" })}`);
    heading.append(title);
    const [badgeText, badgeClass] = budgetBadge(budget.alert_level);
    heading.append(el("span", `shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${badgeClass}`, badgeText));
    card.append(heading);

    const totals = el("div", "mt-5 flex items-baseline justify-between gap-3");
    addText(totals, "p", "text-sm font-semibold text-slate-900", money(budget.spent));
    addText(totals, "p", "text-xs text-slate-500", `of ${money(budget.limit_amount)}`);
    card.append(totals);
    createProgress(card, budget.percent_used, budgetTone(budget.alert_level));
    const footer = el("div", "mt-3 flex items-center justify-between gap-3 text-xs text-slate-500");
    addText(footer, "span", "", `${budget.percent_used}% used`);
    addText(footer, "span", "", `${money(budget.remaining)} left`);
    card.append(footer);
    if (options.actions) {
      const actions = el("div", "mt-4 flex justify-end gap-2 border-t border-slate-100 pt-3");
      const edit = el("button", "rounded-lg px-3 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-50", "Edit limit");
      edit.type = "button";
      edit.addEventListener("click", () => options.onEdit(budget));
      const remove = el("button", "rounded-lg px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-50", "Delete");
      remove.type = "button";
      remove.addEventListener("click", () => options.onDelete(budget));
      actions.append(edit, remove);
      card.append(actions);
    }
    parent.append(card);
    return card;
  };

  const renderGoal = (parent, goal, options = {}) => {
    const card = el("article", options.actions ? "panel" : "rounded-xl border border-slate-100 p-4");
    const header = el("div", "flex items-start justify-between gap-3");
    const details = el("div");
    addText(details, "h3", "font-bold text-slate-950", goal.title);
    addText(details, "p", "mt-1 text-xs text-slate-500", goal.deadline ? `Target · ${dateLabel(goal.deadline)}` : "No target date");
    header.append(details);
    if (options.actions) {
      const remove = el("button", "rounded-lg px-2 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-50", "Delete");
      remove.type = "button";
      remove.addEventListener("click", () => options.onDelete(goal));
      header.append(remove);
    }
    card.append(header);
    const totals = el("div", "mt-5 flex items-baseline justify-between gap-3");
    addText(totals, "p", "text-sm font-semibold text-slate-900", money(goal.current_amount));
    addText(totals, "p", "text-xs text-slate-500", `of ${money(goal.target_amount)}`);
    card.append(totals);
    createProgress(card, goal.progress);
    const footer = el("div", "mt-3 flex items-center justify-between text-xs text-slate-500");
    addText(footer, "span", "", `${goal.progress}% complete`);
    addText(footer, "span", "", `${money(Math.max(Number(goal.target_amount) - Number(goal.current_amount), 0))} to go`);
    card.append(footer);
    if (options.actions) {
      const contribute = el("button", "mt-4 w-full rounded-xl border border-indigo-100 px-3 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-50", "Add savings");
      contribute.type = "button";
      contribute.addEventListener("click", () => options.onContribute(goal));
      card.append(contribute);
    }
    parent.append(card);
  };

  async function loadDashboard() {
    const data = await request("dashboard/");
    document.querySelector('[data-stat="balance"]').textContent = money(data.balance);
    document.querySelector('[data-stat="income"]').textContent = money(data.total_income);
    document.querySelector('[data-stat="expense"]').textContent = money(data.total_expense);
    document.querySelector('[data-stat="goal-count"]').textContent = String(data.goals.length);

    const transactions = document.getElementById("dashboard-transactions");
    if (data.recent_transactions.length) {
      transactions.replaceChildren();
      data.recent_transactions.forEach((item) => renderTransactionLine(transactions, item, true));
    } else empty(transactions, "No transactions yet. Add one to get started.");

    const budgets = document.getElementById("dashboard-budgets");
    if (data.budgets.length) {
      budgets.replaceChildren();
      data.budgets.slice(0, 4).forEach((budget) => renderBudget(budgets, budget, { compact: true }));
    } else empty(budgets, "No budgets yet. Set a limit to keep spending in view.");

    const goals = document.getElementById("dashboard-goals");
    if (data.goals.length) {
      goals.replaceChildren();
      data.goals.forEach((goal) => renderGoal(goals, goal));
    } else empty(goals, "No goals yet. Give your next milestone a name.", "col-span-full py-8 text-center text-sm text-slate-500");
  }

  let transactions = [];
  let editingTransaction = null;
  const drawTransactionRows = () => {
    const body = document.getElementById("transaction-rows");
    const query = document.getElementById("transaction-search").value.trim().toLowerCase();
    const visible = transactions.filter((item) =>
      `${item.category} ${item.description || ""} ${item.transaction_type}`.toLowerCase().includes(query),
    );
    document.getElementById("transaction-count").textContent = String(visible.length);
    if (!visible.length) return empty(body, transactions.length ? "No transactions match your search." : "No transactions yet. Add your first one.", "px-3 py-10 text-center text-sm text-slate-500");
    body.replaceChildren();
    visible.forEach((item) => {
      const row = el("tr", "hover:bg-slate-50/70");
      const description = el("td", "px-3 py-4");
      addText(description, "p", "font-semibold text-slate-900", item.description || item.category);
      addText(description, "p", "mt-1 text-xs capitalize text-slate-500", item.transaction_type);
      row.append(description);
      addText(row, "td", "px-3 py-4 capitalize text-slate-600", item.category);
      addText(row, "td", "px-3 py-4 text-slate-600", dateLabel(item.transaction_date));
      addText(row, "td", `px-3 py-4 text-right font-semibold ${item.transaction_type === "income" ? "text-emerald-700" : "text-slate-900"}`, `${item.transaction_type === "income" ? "+" : "−"}${money(item.amount)}`);
      const actions = el("td", "px-3 py-4 text-right whitespace-nowrap");
      const edit = el("button", "rounded-lg px-2 py-1 text-xs font-semibold text-indigo-700 hover:bg-indigo-50", "Edit");
      edit.type = "button";
      edit.addEventListener("click", () => {
        editingTransaction = item.id;
        const form = document.getElementById("transaction-form");
        Object.entries(item).forEach(([key, value]) => {
          if (form.elements.namedItem(key)) form.elements.namedItem(key).value = value ?? "";
        });
        document.querySelector("#transaction-dialog h2").textContent = "Edit transaction";
        form.querySelector('button[type="submit"]').textContent = "Save changes";
        dialog("transaction-dialog").showModal();
      });
      const remove = el("button", "rounded-lg px-2 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-50", "Delete");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!window.confirm("Delete this transaction?")) return;
        try {
          await request(`transactions/${item.id}/`, { method: "DELETE" });
          showNotice("Transaction deleted.");
          await loadTransactions();
        } catch (error) {
          showNotice(error.message, true);
        }
      });
      actions.append(edit, remove);
      row.append(actions);
      body.append(row);
    });
  };
  const loadTransactions = async () => {
    transactions = await getList("transactions/");
    drawTransactionRows();
  };
  const transactionForm = document.getElementById("transaction-form");
  if (transactionForm) {
    transactionForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = transactionForm.querySelector('button[type="submit"]');
      button.disabled = true;
      try {
        const method = editingTransaction ? "PATCH" : "POST";
        const endpoint = editingTransaction ? `transactions/${editingTransaction}/` : "transactions/";
        await request(endpoint, { method, body: JSON.stringify(formData(transactionForm)) });
        transactionForm.reset();
        document.querySelector("[data-today]").value = todayInputValue();
        editingTransaction = null;
        document.querySelector("#transaction-dialog h2").textContent = "Add transaction";
        button.textContent = "Save transaction";
        dialog("transaction-dialog").close();
        showNotice("Transaction saved.");
        await loadTransactions();
      } catch (error) {
        showNotice(error.message, true);
      } finally {
        button.disabled = false;
      }
    });
    dialog("transaction-dialog").addEventListener("close", () => {
      if (editingTransaction) {
        transactionForm.reset();
        editingTransaction = null;
        document.querySelector("#transaction-dialog h2").textContent = "Add transaction";
        transactionForm.querySelector('button[type="submit"]').textContent = "Save transaction";
      }
    });
  }
  document.querySelector('[data-filter="transactions"]')?.addEventListener("input", drawTransactionRows);

  const loadBudgets = async () => {
    const parent = document.getElementById("budget-grid");
    const budgets = await getList("budgets/");
    if (!budgets.length) return empty(parent, "No budgets yet. Create your first category budget.", "panel col-span-full py-12 text-center text-sm text-slate-500");
    parent.replaceChildren();
    budgets.forEach((budget) => renderBudget(parent, budget, {
      actions: true,
      onEdit: async (item) => {
        const amount = window.prompt(`New limit for ${item.category}`, item.limit_amount);
        if (amount === null) return;
        try {
          await request(`budgets/${item.id}/`, { method: "PATCH", body: JSON.stringify({ limit_amount: amount }) });
          showNotice("Budget updated.");
          await loadBudgets();
        } catch (error) {
          showNotice(error.message, true);
        }
      },
      onDelete: async (item) => {
        if (!window.confirm(`Delete the ${item.category} budget?`)) return;
        try {
          await request(`budgets/${item.id}/`, { method: "DELETE" });
          showNotice("Budget deleted.");
          await loadBudgets();
        } catch (error) {
          showNotice(error.message, true);
        }
      },
    }));
  };
  const budgetForm = document.getElementById("budget-form");
  if (budgetForm) submitForm(budgetForm, "budgets/", "POST", loadBudgets);

  const loadGoals = async () => {
    const parent = document.getElementById("goal-grid");
    const goals = await getList("goals/");
    if (!goals.length) return empty(parent, "No goals yet. Create one to start tracking your progress.", "panel col-span-full py-12 text-center text-sm text-slate-500");
    parent.replaceChildren();
    goals.forEach((goal) => renderGoal(parent, goal, {
      actions: true,
      onContribute: async (item) => {
        const amount = window.prompt(`How much did you save toward ${item.title}?`, "");
        if (amount === null) return;
        const contribution = Number(amount);
        if (!Number.isFinite(contribution) || contribution <= 0) {
          showNotice("Enter a savings amount greater than zero.", true);
          return;
        }
        try {
          await request(`goals/${item.id}/`, {
            method: "PATCH",
            body: JSON.stringify({ current_amount: (Number(item.current_amount) + contribution).toFixed(2) }),
          });
          showNotice("Goal progress updated.");
          await loadGoals();
        } catch (error) {
          showNotice(error.message, true);
        }
      },
      onDelete: async (item) => {
        if (!window.confirm(`Delete the “${item.title}” goal?`)) return;
        try {
          await request(`goals/${item.id}/`, { method: "DELETE" });
          showNotice("Goal deleted.");
          await loadGoals();
        } catch (error) {
          showNotice(error.message, true);
        }
      },
    }));
  };
  const goalForm = document.getElementById("goal-form");
  if (goalForm) submitForm(goalForm, "goals/", "POST", loadGoals);

  const renderAnalytics = (items) => {
    const now = new Date();
    const firstOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const monthTransactions = items.filter((item) => new Date(`${item.transaction_date}T00:00:00`) >= firstOfMonth);
    const totals = monthTransactions.reduce((sum, item) => {
      sum[item.transaction_type] += Number(item.amount) || 0;
      return sum;
    }, { income: 0, expense: 0 });
    document.querySelector('[data-analytics="income"]').textContent = money(totals.income);
    document.querySelector('[data-analytics="expense"]').textContent = money(totals.expense);
    document.querySelector('[data-analytics="net"]').textContent = money(totals.income - totals.expense);

    const months = [];
    for (let offset = 5; offset >= 0; offset -= 1) {
      const date = new Date(now.getFullYear(), now.getMonth() - offset, 1);
      const year = date.getFullYear();
      const month = date.getMonth();
      const monthItems = items.filter((item) => {
        const transactionDate = new Date(`${item.transaction_date}T00:00:00`);
        return transactionDate.getFullYear() === year && transactionDate.getMonth() === month;
      });
      months.push({
        label: new Intl.DateTimeFormat("en", { month: "short" }).format(date),
        income: monthItems.filter((item) => item.transaction_type === "income").reduce((sum, item) => sum + Number(item.amount), 0),
        expense: monthItems.filter((item) => item.transaction_type === "expense").reduce((sum, item) => sum + Number(item.amount), 0),
      });
    }
    const chart = document.getElementById("cashflow-chart");
    chart.replaceChildren();
    const maxTotal = Math.max(1, ...months.flatMap((item) => [item.income, item.expense]));
    months.forEach((item) => {
      const group = el("div", "flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-2");
      const bars = el("div", "flex h-52 w-full items-end justify-center gap-1");
      [[item.income, "bg-emerald-500", "income"], [item.expense, "bg-indigo-500", "expenses"]].forEach(([amount, color, label]) => {
        const bar = el("div", `w-4 rounded-t-md sm:w-6 ${color}`);
        bar.style.height = `${Math.max(amount ? 2 : 0, (amount / maxTotal) * 100)}%`;
        bar.title = `${label}: ${money(amount)}`;
        bars.append(bar);
      });
      group.append(bars);
      addText(group, "span", "text-xs text-slate-500", item.label);
      chart.append(group);
    });

    const categories = new Map();
    monthTransactions.filter((item) => item.transaction_type === "expense").forEach((item) => {
      const key = item.category || "Other";
      categories.set(key, (categories.get(key) || 0) + Number(item.amount));
    });
    const categoryChart = document.getElementById("category-chart");
    categoryChart.replaceChildren();
    const sorted = [...categories.entries()].sort((a, b) => b[1] - a[1]);
    if (!sorted.length) return empty(categoryChart, "No expenses recorded this month.");
    const maxCategory = sorted[0][1];
    sorted.slice(0, 8).forEach(([name, amount]) => {
      const row = el("div");
      const labels = el("div", "mb-2 flex items-center justify-between gap-3 text-sm");
      addText(labels, "span", "truncate font-medium capitalize text-slate-700", name);
      addText(labels, "span", "shrink-0 font-semibold text-slate-900", money(amount));
      row.append(labels);
      createProgress(row, (amount / maxCategory) * 100, "bg-indigo-500");
      categoryChart.append(row);
    });
  };

  const loadProfile = async () => {
    const [profile, user] = await Promise.all([request("auth/profile/"), request("auth/user/")]);
    const form = document.getElementById("profile-form");
    if (!form) return;
    Object.entries(profile).forEach(([key, value]) => {
      const field = form.elements.namedItem(key);
      if (field) field.value = value ?? "";
    });
    const email = el("p", "mb-5 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600", `Signed in as ${user.email}`);
    form.prepend(email);
  };

  const loadReminders = async () => {
    const parent = document.getElementById("reminder-list");
    const reminders = await getList("reminders/");
    if (!reminders.length) return empty(parent, "No reminders yet.");
    parent.replaceChildren();
    reminders.forEach((reminder) => {
      const row = el("div", "flex items-start justify-between gap-3 py-4");
      const text = el("div", "min-w-0");
      addText(text, "p", `font-semibold ${reminder.is_completed ? "text-slate-400 line-through" : "text-slate-900"}`, reminder.title);
      addText(text, "p", "mt-1 text-xs text-slate-500", dateLabel(reminder.remind_at.slice(0, 10)));
      if (reminder.message) addText(text, "p", "mt-2 text-sm text-slate-600", reminder.message);
      const actions = el("div", "flex shrink-0 gap-1");
      const toggle = el("button", "rounded-lg px-2 py-1 text-xs font-semibold text-indigo-700 hover:bg-indigo-50", reminder.is_completed ? "Undo" : "Done");
      toggle.type = "button";
      toggle.addEventListener("click", async () => {
        try {
          await request(`reminders/${reminder.id}/`, { method: "PATCH", body: JSON.stringify({ is_completed: !reminder.is_completed }) });
          await loadReminders();
        } catch (error) {
          showNotice(error.message, true);
        }
      });
      const remove = el("button", "rounded-lg px-2 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-50", "Delete");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!window.confirm("Delete this reminder?")) return;
        try {
          await request(`reminders/${reminder.id}/`, { method: "DELETE" });
          showNotice("Reminder deleted.");
          await loadReminders();
        } catch (error) {
          showNotice(error.message, true);
        }
      });
      actions.append(toggle, remove);
      row.append(text, actions);
      parent.append(row);
    });
  };
  const profileForm = document.getElementById("profile-form");
  if (profileForm) {
    loadProfile().catch((error) => showNotice(error.message, true));
    profileForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = formData(profileForm);
      ["date_of_birth", "phone_number"].forEach((key) => {
        if (data[key] === "") data[key] = null;
      });
      try {
        await request("auth/profile/", { method: "PATCH", body: JSON.stringify(data) });
        showNotice("Profile updated.");
      } catch (error) {
        showNotice(error.message, true);
      }
    });
    loadReminders().catch((error) => showNotice(error.message, true));
  }
  const reminderForm = document.getElementById("reminder-form");
  if (reminderForm) submitForm(reminderForm, "reminders/", "POST", loadReminders);

  const loaders = {
    dashboard: loadDashboard,
    transactions: loadTransactions,
    budgets: loadBudgets,
    goals: loadGoals,
    analytics: async () => renderAnalytics(await getList("transactions/")),
  };
  const load = loaders[page];
  if (load) load().catch((error) => showNotice(error.message, true));
})();
