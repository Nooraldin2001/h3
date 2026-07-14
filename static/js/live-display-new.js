(function () {
  const config = window.LIVE_DISPLAY_NEW_CONFIG || {};
  const TOKEN = config.token || "";
  const API_URL = config.apiUrl || "/live/api/state/";
  const IMAGE_BASE = config.imageBaseUrl || "/static/live_new/plates/";
  const IMAGE_VERSION = config.plateImageVersion || "1";

  const PLATE_TYPES = [
    "abudhabi",
    "dubai",
    "dubai_yellow",
    "rasalkhimma",
    "fujairah",
    "ajman",
    "ummalquain",
    "sharjah",
  ];

  const PLATE_IMAGES = {
    abudhabi: "abudhabi.jpg",
    dubai: "dubai.jpg",
    dubai_yellow: "dubai_classic.jpg",
    rasalkhimma: "rasalkhimma.jpg",
    fujairah: "fujairah.jpg",
    ajman: "ajman.jpg",
    ummalquain: "ummalquain.jpg",
    sharjah: "sharjah.jpg",
  };

  const CLASS_BY_TYPE = {
    abudhabi: "abudhabi",
    dubai: "dubai",
    dubai_yellow: "dubai-yellow",
    rasalkhimma: "rasalkhimma",
    fujairah: "fujairah",
    ajman: "ajman",
    ummalquain: "ummalquain",
    sharjah: "sharjah",
  };

  const els = {
    frame: document.getElementById("nld-plate-frame"),
    idleLabel: document.getElementById("nld-idle-label"),
    plateGlow: document.getElementById("nld-plate-glow"),
    timerWrap: document.querySelector(".nld-timer-wrap"),
    timer: document.getElementById("nld-timer"),
    timerState: document.getElementById("nld-timer-state"),
    timerProgress: document.getElementById("nld-timer-progress-bar"),
    price: document.getElementById("nld-price"),
    priceValue: document.getElementById("nld-price-value"),
    alert: document.getElementById("nld-alert"),
    alertText: document.getElementById("nld-alert-text"),
    ticker: document.getElementById("nld-ticker"),
    tickerTrack: document.getElementById("nld-ticker-track"),
    logoWrap: document.querySelector(".nld-logo-wrap"),
    customLogo: document.getElementById("nld-custom-logo"),
    soldOverlay: document.getElementById("nld-sold-overlay"),
    soldPlate: document.getElementById("nld-sold-plate"),
    soldPrice: document.getElementById("nld-sold-price"),
    confetti: document.getElementById("nld-confetti"),
  };

  let state = config.state || {};
  let spinnerIndex = 0;
  let spinnerTimer = null;
  let lastPrice = "";
  let soldTimer = null;
  let soldRunning = false;

  function normalizeType(plateType) {
    return PLATE_TYPES.includes(plateType) ? plateType : "dubai";
  }

  function classForType(plateType) {
    return CLASS_BY_TYPE[normalizeType(plateType)] || "dubai";
  }

  function isPlateEmpty(currentState) {
    return !String(currentState.code || "").trim() && !String(currentState.number || "").trim();
  }

  function getDisplayType(currentState) {
    if (isPlateEmpty(currentState)) {
      const idx = ((spinnerIndex % PLATE_TYPES.length) + PLATE_TYPES.length) % PLATE_TYPES.length;
      return PLATE_TYPES[idx];
    }
    return normalizeType(currentState.plate_type);
  }

  function startSpinner() {
    if (spinnerTimer) return;
    spinnerTimer = setInterval(() => {
      spinnerIndex = (spinnerIndex + 1) % PLATE_TYPES.length;
      renderPlate();
    }, 2000);
  }

  function stopSpinner() {
    if (!spinnerTimer) return;
    clearInterval(spinnerTimer);
    spinnerTimer = null;
  }

  function syncSpinner() {
    if (isPlateEmpty(state)) {
      startSpinner();
      els.idleLabel?.classList.add("visible");
    } else {
      stopSpinner();
      spinnerIndex = 0;
      els.idleLabel?.classList.remove("visible");
    }
  }

  function renderPlate(targetFrame, plateType, code, number, options = {}) {
    const frame = targetFrame || els.frame;
    if (!frame) return;

    const type = normalizeType(plateType || getDisplayType(state));
    const fileName = PLATE_IMAGES[type] || PLATE_IMAGES.dubai;
    const className = classForType(type);
    const renderKey = [type, fileName, IMAGE_BASE, IMAGE_VERSION].join("|");

    if (frame.dataset.newPlateRenderKey === renderKey) {
      const codeEl = frame.querySelector(".nld-plate-code");
      const numberEl = frame.querySelector(".nld-plate-number");
      if (codeEl) codeEl.textContent = code || "";
      if (numberEl) numberEl.textContent = number || "";
      return;
    }

    frame.innerHTML = "";
    frame.dataset.newPlateRenderKey = renderKey;

    const slide = document.createElement("div");
    slide.className = `nld-plate-slide plate-type-${className}`;
    slide.dataset.plateType = type;

    const canvas = document.createElement("div");
    canvas.className = "nld-plate-canvas";

    const img = document.createElement("img");
    img.className = "nld-plate-image";
    img.alt = "Plate";
    img.src = `${IMAGE_BASE}${fileName}?v=${IMAGE_VERSION}`;
    canvas.appendChild(img);

    const codeOverlay = document.createElement("div");
    codeOverlay.className = "nld-plate-text-overlay nld-plate-code-overlay";
    const codeEl = document.createElement("div");
    codeEl.className = "nld-plate-code";
    codeEl.textContent = code || "";
    codeOverlay.appendChild(codeEl);
    canvas.appendChild(codeOverlay);

    const numberOverlay = document.createElement("div");
    numberOverlay.className = "nld-plate-text-overlay nld-plate-number-overlay";
    const numberEl = document.createElement("div");
    numberEl.className = "nld-plate-number";
    numberEl.textContent = number || "";
    numberOverlay.appendChild(numberEl);
    canvas.appendChild(numberOverlay);

    slide.appendChild(canvas);
    frame.appendChild(slide);

    if (options.sold) {
      frame.dataset.newPlateRenderKey = `${renderKey}|sold`;
    }
  }

  function renderCurrentPlate() {
    const type = getDisplayType(state);
    renderPlate(els.frame, type, state.code, state.number);
  }

  function formatTimer(seconds) {
    const safe = Math.max(0, Math.floor(Number(seconds) || 0));
    const minutes = Math.floor(safe / 60);
    const rest = safe % 60;
    return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
  }

  function renderTimer() {
    const remaining = Math.max(0, Number(state.timer_remaining_seconds) || 0);
    const total = Math.max(1, Number(state.timer_seconds) || 1);
    const active = Boolean(state.timer_active);
    const urgent = active && remaining <= 10 && remaining > 0;
    const expired = active && remaining === 0;
    const progress = Math.max(0, Math.min(100, (remaining / total) * 100));

    if (els.timer) els.timer.textContent = formatTimer(remaining);
    if (els.timerProgress) els.timerProgress.style.width = `${progress}%`;
    if (els.timerState) {
      els.timerState.textContent = expired ? "CLOSED" : urgent ? "CLOSING" : active ? "COUNTDOWN" : "STANDBY";
    }
    if (els.timerWrap) {
      els.timerWrap.classList.toggle("urgent", urgent);
      els.timerWrap.classList.toggle("expired", expired);
    }
    els.plateGlow?.classList.toggle("urgent", urgent);
    els.frame?.classList.toggle("urgent", urgent);
  }

  function formatPrice(value) {
    if (value === null || value === undefined || value === "") return "";
    const cleaned = String(value).replace(/[^\d.]/g, "");
    if (!cleaned) return "";
    const number = Math.floor(parseFloat(cleaned));
    if (Number.isNaN(number)) return String(value);
    return number.toLocaleString("en-AE");
  }

  function renderPrice() {
    const formatted = formatPrice(state.price);
    if (!formatted) {
      els.price?.classList.remove("visible", "price-changed");
      lastPrice = "";
      return;
    }

    if (els.priceValue) els.priceValue.textContent = formatted;
    els.price?.classList.add("visible");
    if (lastPrice && lastPrice !== formatted && els.price) {
      els.price.classList.remove("price-changed");
      void els.price.offsetWidth;
      els.price.classList.add("price-changed");
    }
    lastPrice = formatted;
  }

  function renderAlert() {
    const message = String(state.alert_message || "").trim();
    if (!message) {
      els.alert?.classList.remove("visible");
      if (els.alertText) els.alertText.textContent = "";
      return;
    }

    if (els.alertText && els.alertText.textContent !== message) {
      els.alertText.textContent = message;
    }
    els.alert?.classList.add("visible");
  }

  function renderTicker() {
    const message = String(state.message || "").trim();
    if (!message) {
      els.ticker?.classList.remove("visible");
      if (els.tickerTrack) {
        els.tickerTrack.dataset.message = "";
        els.tickerTrack.innerHTML = "";
        els.tickerTrack.style.animation = "";
      }
      return;
    }

    if (!els.tickerTrack || !els.ticker) return;
    if (els.tickerTrack.dataset.message !== message) {
      els.tickerTrack.dataset.message = message;
      els.tickerTrack.innerHTML = "";
      for (let i = 0; i < 2; i += 1) {
        const span = document.createElement("span");
        span.className = "nld-ticker-text";
        span.textContent = message;
        if (i === 1) span.setAttribute("aria-hidden", "true");
        els.tickerTrack.appendChild(span);
      }
      const duration = Math.max(18, 18 + Math.max(0, message.length - 40) * 0.15);
      els.tickerTrack.style.animation = "none";
      void els.tickerTrack.offsetWidth;
      els.tickerTrack.style.animation = `nld-ticker-rtl ${duration}s linear infinite`;
    }
    els.ticker.classList.add("visible");
  }

  function renderLogo() {
    const logoUrl = String(state.logo_url || "").trim();
    if (!els.logoWrap || !els.customLogo) return;

    if (logoUrl) {
      if (els.customLogo.getAttribute("src") !== logoUrl) {
        els.customLogo.src = logoUrl;
      }
      els.logoWrap.classList.add("has-custom");
    } else {
      els.customLogo.removeAttribute("src");
      els.logoWrap.classList.remove("has-custom");
    }
  }

  function renderAll() {
    syncSpinner();
    renderCurrentPlate();
    renderTimer();
    renderPrice();
    renderAlert();
    renderTicker();
    renderLogo();
  }

  async function pollState() {
    try {
      const res = await fetch(`${API_URL}?token=${encodeURIComponent(TOKEN)}`, {
        headers: { Accept: "application/json" },
      });
      if (!res.ok) return;
      state = await res.json();
      renderAll();
    } catch (err) {
      // Keep the last rendered state if the network blips during a broadcast.
      console.warn("Live display poll failed", err);
    }
  }

  function makeConfetti() {
    if (!els.confetti) return;
    const colors = ["#c9a535", "#edd97a", "#f0e0a0", "#7c3aed", "#a78bfa", "#dc2626", "#ffffff"];
    els.confetti.innerHTML = "";
    for (let i = 0; i < 60; i += 1) {
      const piece = document.createElement("span");
      piece.className = "nld-confetti-piece";
      const size = 4 + Math.random() * 10;
      piece.style.left = `${5 + Math.random() * 90}%`;
      piece.style.top = `${5 + Math.random() * 60}%`;
      piece.style.width = `${size * 0.7}px`;
      piece.style.height = `${size * 1.4}px`;
      piece.style.background = colors[Math.floor(Math.random() * colors.length)];
      piece.style.borderRadius = Math.random() > 0.65 ? "50%" : "2px";
      piece.style.setProperty("--delay", `${Math.random() * 1.5}s`);
      piece.style.setProperty("--duration", `${1.8 + Math.random() * 1.4}s`);
      els.confetti.appendChild(piece);
    }
  }

  window.triggerSoldCelebration = function (details = {}) {
    if (soldRunning) {
      clearTimeout(soldTimer);
      els.soldOverlay?.classList.remove("visible");
      void els.soldOverlay?.offsetWidth;
    }

    soldRunning = true;
    const detail = {
      plateType: details.plateType || details.plate_type || state.plate_type || getDisplayType(state),
      code: details.code !== undefined ? details.code : state.code,
      number: details.number !== undefined ? details.number : state.number,
      price: details.price !== undefined ? details.price : state.price,
    };

    renderPlate(els.soldPlate, detail.plateType, detail.code, detail.number, { sold: true });
    if (els.soldPrice) {
      const price = formatPrice(detail.price);
      els.soldPrice.textContent = price ? `AED ${price}` : "";
    }
    makeConfetti();
    els.soldOverlay?.classList.add("visible");

    soldTimer = setTimeout(() => {
      els.soldOverlay?.classList.remove("visible");
      soldRunning = false;
    }, 5000);
  };

  window.addEventListener("auction:sold", function (event) {
    window.triggerSoldCelebration(event.detail || {});
  });

  renderAll();
  setInterval(pollState, 1000);
})();
