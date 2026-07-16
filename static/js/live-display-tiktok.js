(function () {
  const config = window.LIVE_DISPLAY_TIKTOK_CONFIG || {};
  const TOKEN = config.token || "";
  const API_URL = config.apiUrl || "/live/api/state/";
  const IMAGE_BASE = config.imageBaseUrl || "/static/live_new/plates/";
  const IMAGE_VERSION = config.plateImageVersion || "1";
  const LOGO_URL = config.logoUrl || "/static/live_new/images/h3-logo.jpeg?v=3";
  const WATERMARK_URL = config.watermarkUrl || "/static/live_new/images/watermark.jpeg?v=1";
  const DEFAULT_TITLE = "مزاد علني مباشر لبيع وشراء الأرقام المميزة";

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
    frame: document.getElementById("tld-plate-frame"),
    timerWrap: document.getElementById("tld-timer-wrap"),
    timer: document.getElementById("tld-timer"),
    price: document.getElementById("tld-price"),
    priceValue: document.getElementById("tld-price-value"),
    alert: document.getElementById("tld-alert"),
    alertText: document.getElementById("tld-alert-text"),
    eventTitle: document.getElementById("tld-event-title"),
    ticker: document.getElementById("tld-ticker"),
    tickerTrack: document.getElementById("tld-ticker-track"),
    logoWrap: document.getElementById("tld-logo-wrap") || document.querySelector(".tld-logo-wrap"),
    customLogo: document.getElementById("tld-custom-logo"),
    defaultLogo: document.getElementById("tld-default-logo"),
    root: document.getElementById("tld-root") || document.querySelector(".tld-root"),
    bgWatermark: document.getElementById("tld-bg-watermark"),
    bgWatermarkImg: document.getElementById("tld-bg-watermark-img"),
    soldOverlay: document.getElementById("tld-sold-overlay"),
    soldPlate: document.getElementById("tld-sold-plate"),
    soldPrice: document.getElementById("tld-sold-price"),
    soldName: document.getElementById("tld-sold-name"),
    confetti: document.getElementById("tld-confetti"),
    gavelStage: document.getElementById("tld-gavel-stage"),
    gavelSparks: document.getElementById("tld-gavel-sparks"),
  };

  let state = config.state || {};
  let spinnerIndex = 0;
  let spinnerTimer = null;
  let lastPrice = "";
  let soldTimer = null;
  let soldRunning = false;
  let lastSoldEventId = Number(state.sold_event_id) || 0;

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
      renderCurrentPlate();
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
    } else {
      stopSpinner();
      spinnerIndex = 0;
    }
  }

  function renderPlate(targetFrame, plateType, code, number, options = {}) {
    const frame = targetFrame || els.frame;
    if (!frame) return;

    const type = normalizeType(plateType || getDisplayType(state));
    const fileName = PLATE_IMAGES[type] || PLATE_IMAGES.dubai;
    const className = classForType(type);
    const renderKey = [type, fileName, IMAGE_BASE, IMAGE_VERSION].join("|");

    if (frame.dataset.tiktokPlateRenderKey === renderKey) {
      const codeEl = frame.querySelector(".tld-plate-code");
      const numberEl = frame.querySelector(".tld-plate-number");
      if (codeEl) codeEl.textContent = code || "";
      if (numberEl) numberEl.textContent = number || "";
      return;
    }

    frame.innerHTML = "";
    frame.dataset.tiktokPlateRenderKey = options.sold ? `${renderKey}|sold` : renderKey;

    const slide = document.createElement("div");
    slide.className = `tld-plate-slide plate-type-${className}`;
    slide.dataset.plateType = type;

    const canvas = document.createElement("div");
    canvas.className = "tld-plate-canvas";

    const img = document.createElement("img");
    img.className = "tld-plate-image";
    img.alt = "Plate";
    img.src = `${IMAGE_BASE}${fileName}?v=${IMAGE_VERSION}`;
    canvas.appendChild(img);

    const codeOverlay = document.createElement("div");
    codeOverlay.className = "tld-plate-text-overlay tld-plate-code-overlay";
    const codeEl = document.createElement("div");
    codeEl.className = "tld-plate-code";
    codeEl.textContent = code || "";
    codeOverlay.appendChild(codeEl);
    canvas.appendChild(codeOverlay);

    const numberOverlay = document.createElement("div");
    numberOverlay.className = "tld-plate-text-overlay tld-plate-number-overlay";
    const numberEl = document.createElement("div");
    numberEl.className = "tld-plate-number";
    numberEl.textContent = number || "";
    numberOverlay.appendChild(numberEl);
    canvas.appendChild(numberOverlay);

    slide.appendChild(canvas);
    frame.appendChild(slide);
  }

  function renderCurrentPlate() {
    renderPlate(els.frame, getDisplayType(state), state.code, state.number);
  }

  function formatTimer(seconds) {
    const safe = Math.max(0, Math.floor(Number(seconds) || 0));
    const minutes = Math.floor(safe / 60);
    const rest = safe % 60;
    return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
  }

  function renderTimer() {
    const active = Boolean(state.timer_active);
    if (!els.timerWrap) return;

    if (!active) {
      els.timerWrap.classList.remove("visible", "urgent");
      return;
    }

    const remaining = Math.max(0, Number(state.timer_remaining_seconds) || 0);
    const urgent = remaining <= 10 && remaining > 0;
    if (els.timer) els.timer.textContent = formatTimer(remaining);
    els.timerWrap.classList.add("visible");
    els.timerWrap.classList.toggle("urgent", urgent);
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

  function renderEventTitle() {
    if (!els.eventTitle) return;
    const title = String(state.event_title || "").trim() || DEFAULT_TITLE;
    if (els.eventTitle.textContent !== title) {
      els.eventTitle.textContent = title;
    }
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
        const unit = document.createElement("span");
        unit.className = "tld-ticker-unit";
        if (i === 1) unit.setAttribute("aria-hidden", "true");

        const badge = document.createElement("span");
        badge.className = "tld-ticker-live-badge";
        badge.setAttribute("aria-hidden", "true");
        badge.appendChild(document.createTextNode("LIVE"));
        const dot = document.createElement("span");
        dot.className = "tld-ticker-live-dot";
        badge.appendChild(dot);

        const msg = document.createElement("span");
        msg.className = "tld-ticker-msg";
        msg.textContent = message;

        unit.appendChild(badge);
        unit.appendChild(msg);
        els.tickerTrack.appendChild(unit);
      }
      const duration = Math.max(8, 8 + message.length * 0.08);
      els.tickerTrack.style.animation = "none";
      void els.tickerTrack.offsetWidth;
      els.tickerTrack.style.animation = `tld-ticker-rtl ${duration}s linear infinite`;
    }
    els.ticker.classList.add("visible");
  }

  function renderBrand() {
    const raw = String(state.tiktok_brand_mode || "logo").trim();
    const mode = raw === "watermark" || raw === "empty" ? raw : "logo";
    const useWatermark = mode === "watermark";
    const useLogo = mode === "logo";

    els.root?.classList.toggle("is-watermark", useWatermark);
    els.root?.classList.toggle("is-logo", useLogo);
    els.root?.classList.toggle("is-empty", mode === "empty");

    // Header always uses the H3 logo asset (shown only in logo mode via CSS).
    if (els.defaultLogo && els.defaultLogo.getAttribute("src") !== LOGO_URL) {
      els.defaultLogo.src = LOGO_URL;
    }
    els.customLogo?.removeAttribute("src");
    els.logoWrap?.classList.remove("has-custom");

    if (els.bgWatermarkImg && els.bgWatermarkImg.getAttribute("src") !== WATERMARK_URL) {
      els.bgWatermarkImg.src = WATERMARK_URL;
    }
    if (els.bgWatermark) {
      els.bgWatermark.setAttribute("aria-hidden", useWatermark ? "false" : "true");
    }
  }

  function renderAll() {
    syncSpinner();
    renderCurrentPlate();
    renderTimer();
    renderPrice();
    renderAlert();
    renderEventTitle();
    renderTicker();
    renderBrand();
  }

  function handleSoldEvent() {
    const soldEventId = Number(state.sold_event_id) || 0;
    if (!soldEventId || soldEventId <= lastSoldEventId) return;
    lastSoldEventId = soldEventId;
    window.triggerSoldCelebration({
      plateType: state.plate_type,
      code: state.code,
      number: state.number,
      price: state.price,
      style: state.sold_style,
      name: state.sold_name,
    });
  }

  async function pollState() {
    try {
      const res = await fetch(`${API_URL}?token=${encodeURIComponent(TOKEN)}`, {
        headers: { Accept: "application/json" },
      });
      if (!res.ok) return;
      state = await res.json();
      renderAll();
      handleSoldEvent();
    } catch (err) {
      console.warn("TikTok live display poll failed", err);
    }
  }

  function makeConfetti() {
    if (!els.confetti) return;
    const colors = ["#c9a535", "#edd97a", "#f0e0a0", "#7c3aed", "#a78bfa", "#dc2626", "#ffffff"];
    els.confetti.innerHTML = "";
    for (let i = 0; i < 60; i += 1) {
      const piece = document.createElement("span");
      piece.className = "tld-confetti-piece";
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

  function normalizeSoldStyle(style) {
    return style === "gavel" ? "gavel" : "confetti";
  }

  function makeGavelSparks() {
    if (!els.gavelSparks) return;
    const colors = ["#edd97a", "#c9a535", "#f0e0a0", "#ffffff", "#ffe9a0"];
    els.gavelSparks.innerHTML = "";
    for (let i = 0; i < 28; i += 1) {
      const piece = document.createElement("span");
      piece.className = "tld-gavel-spark";
      const angle = (Math.PI * 2 * i) / 28 + (Math.random() * 0.4 - 0.2);
      const dist = 40 + Math.random() * 90;
      piece.style.setProperty("--dx", `${Math.cos(angle) * dist}px`);
      piece.style.setProperty("--dy", `${Math.sin(angle) * dist * 0.55 - 20}px`);
      piece.style.setProperty("--delay", `${0.72 + Math.random() * 0.18}s`);
      piece.style.setProperty("--size", `${3 + Math.random() * 5}px`);
      piece.style.background = colors[Math.floor(Math.random() * colors.length)];
      els.gavelSparks.appendChild(piece);
    }
  }

  window.triggerSoldCelebration = function (details = {}) {
    if (soldRunning) {
      clearTimeout(soldTimer);
      els.soldOverlay?.classList.remove("visible", "sold-style-gavel", "sold-style-confetti");
      void els.soldOverlay?.offsetWidth;
    }

    soldRunning = true;
    const style = normalizeSoldStyle(details.style || details.sold_style || state.sold_style);
    const detail = {
      plateType: details.plateType || details.plate_type || state.plate_type || getDisplayType(state),
      code: details.code !== undefined ? details.code : state.code,
      number: details.number !== undefined ? details.number : state.number,
      price: details.price !== undefined ? details.price : state.price,
      name: details.name !== undefined ? details.name : (details.sold_name !== undefined ? details.sold_name : state.sold_name),
    };

    els.soldOverlay?.classList.remove("sold-style-gavel", "sold-style-confetti");
    els.soldOverlay?.classList.add(style === "gavel" ? "sold-style-gavel" : "sold-style-confetti");

    renderPlate(els.soldPlate, detail.plateType, detail.code, detail.number, { sold: true });
    if (els.soldName) {
      const name = String(detail.name || "").trim();
      els.soldName.textContent = name;
      els.soldName.hidden = !name;
    }
    if (els.soldPrice) {
      const price = formatPrice(detail.price);
      els.soldPrice.textContent = price ? `AED ${price}` : "";
    }

    if (style === "gavel") {
      if (els.confetti) els.confetti.innerHTML = "";
      makeGavelSparks();
      els.gavelStage?.setAttribute("aria-hidden", "false");
    } else {
      els.gavelStage?.setAttribute("aria-hidden", "true");
      makeConfetti();
    }

    els.soldOverlay?.classList.add("visible");
    els.soldOverlay?.setAttribute("aria-hidden", "false");

    soldTimer = setTimeout(() => {
      els.soldOverlay?.classList.remove("visible", "sold-style-gavel", "sold-style-confetti");
      els.soldOverlay?.setAttribute("aria-hidden", "true");
      els.gavelStage?.setAttribute("aria-hidden", "true");
      soldRunning = false;
    }, 5000);
  };

  window.addEventListener("auction:sold", function (event) {
    window.triggerSoldCelebration(event.detail || {});
  });

  renderAll();
  setInterval(pollState, 1000);
})();
