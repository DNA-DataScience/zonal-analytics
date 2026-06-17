/**
 * toast.ts — shared, light-themed toast notifications.
 * Replaces blocking browser alert()s. Styles live in src/app/ui-theme.css.
 */

export type ToastType = "success" | "error" | "warning" | "info";

const ICONS: Record<ToastType, string> = {
  success:
    '<path fill="currentColor" d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z"/>',
  error:
    '<path fill="currentColor" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>',
  warning:
    '<path fill="currentColor" d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>',
  info: '<path fill="currentColor" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>',
};

function getStack(): HTMLDivElement {
  let stack = document.querySelector<HTMLDivElement>(".ui-toast-stack");
  if (!stack) {
    stack = document.createElement("div");
    stack.className = "ui-toast-stack";
    document.body.appendChild(stack);
  }
  return stack;
}

export function showToast(
  message: string,
  type: ToastType = "info",
  duration = 4000,
): void {
  if (typeof document === "undefined") return;

  const stack = getStack();

  const toast = document.createElement("div");
  toast.className = `ui-toast ui-toast--${type}`;
  toast.setAttribute("role", type === "error" ? "alert" : "status");
  toast.innerHTML = `
    <svg class="ui-toast__icon" viewBox="0 0 24 24" aria-hidden="true">${ICONS[type]}</svg>
    <span class="ui-toast__msg"></span>
  `;
  const msgEl = toast.querySelector<HTMLElement>(".ui-toast__msg");
  if (msgEl) msgEl.textContent = message;

  stack.appendChild(toast);

  // Animate in on next frame.
  requestAnimationFrame(() => toast.classList.add("show"));

  const remove = () => {
    toast.classList.remove("show");
    window.setTimeout(() => toast.remove(), 280);
  };

  const timer = window.setTimeout(remove, duration);
  toast.addEventListener("click", () => {
    window.clearTimeout(timer);
    remove();
  });
}
