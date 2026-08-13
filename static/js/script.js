// Auto-dismiss flash messages after a few seconds
document.querySelectorAll(".flash").forEach((el) => {
  setTimeout(() => {
    el.style.transition = "opacity 0.4s ease";
    el.style.opacity = "0";
    setTimeout(() => el.remove(), 400);
  }, 5000);
});

// ---- OTP input boxes: auto-advance, backspace, paste ----
function initOtpBoxes() {
  const boxes = Array.from(document.querySelectorAll(".otp-box"));
  if (!boxes.length) return;

  boxes.forEach((box, i) => {
    box.addEventListener("input", (e) => {
      const val = e.target.value.replace(/[^0-9]/g, "");
      e.target.value = val.slice(-1);
      if (val && i < boxes.length - 1) boxes[i + 1].focus();
      maybeAutoSubmit(boxes);
    });

    box.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !box.value && i > 0) {
        boxes[i - 1].focus();
      }
    });

    box.addEventListener("paste", (e) => {
      e.preventDefault();
      const paste = (e.clipboardData || window.clipboardData)
        .getData("text")
        .replace(/[^0-9]/g, "");
      paste
        .slice(0, boxes.length)
        .split("")
        .forEach((digit, idx) => {
          if (boxes[idx]) boxes[idx].value = digit;
        });
      const lastFilled = Math.min(paste.length, boxes.length) - 1;
      if (lastFilled >= 0) boxes[lastFilled].focus();
      maybeAutoSubmit(boxes);
    });
  });

  boxes[0].focus();
}

function maybeAutoSubmit(boxes) {
  const filled = boxes.every((b) => b.value.length === 1);
  if (filled) {
    const form = boxes[0].closest("form");
    if (form) form.requestSubmit();
  }
}

// ---- Resend OTP with cooldown ----
function initResend() {
  const btn = document.getElementById("resendBtn");
  if (!btn) return;

  let cooldown = 0;
  let timer = null;

  const startCooldown = (seconds) => {
    cooldown = seconds;
    btn.disabled = true;
    updateLabel();
    timer = setInterval(() => {
      cooldown -= 1;
      updateLabel();
      if (cooldown <= 0) {
        clearInterval(timer);
        btn.disabled = false;
        btn.textContent = "Resend code";
      }
    }, 1000);
  };

  const updateLabel = () => {
    btn.textContent = `Resend code (${cooldown}s)`;
  };

  startCooldown(30);

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    const original = btn.textContent;
    btn.textContent = "Sending...";
    try {
      const res = await fetch("/resend-otp", { method: "POST" });
      const data = await res.json();
      showToast(data.message, data.ok ? "success" : "error");
    } catch (err) {
      showToast("Something went wrong. Please try again.", "error");
    }
    startCooldown(30);
  });
}

function showToast(message, type) {
  const stack = document.getElementById("flashStack") || (() => {
    const s = document.createElement("div");
    s.className = "flash-stack";
    s.id = "flashStack";
    document.body.appendChild(s);
    return s;
  })();

  const el = document.createElement("div");
  el.className = `flash flash--${type === "success" ? "success" : "error"}`;
  el.innerHTML = `<span>${message}</span><button class="flash__close">&times;</button>`;
  el.querySelector(".flash__close").addEventListener("click", () => el.remove());
  stack.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

document.addEventListener("DOMContentLoaded", () => {
  initOtpBoxes();
  initResend();
});
