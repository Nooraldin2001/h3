(function () {
  const config = window.LIVE_DISPLAY_NEW_CONFIG || {};
  const TOKEN = config.token || "";
  const API_URL = config.apiUrl || "/live/api/state/";
  const IMAGE_BASE = config.imageBaseUrl || "/static/live_new/plates/";
  const IMAGE_VERSION = config.plateImageVersion || "1";
  const KANDURA_VIDEO_URL = config.kanduraVideoUrl || "";
  const REDUCE_MOTION = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const EMIRATE_TYPES = [
    "abudhabi", "dubai", "dubai_yellow", "rasalkhimma", "fujairah", "ajman", "ummalquain", "sharjah",
  ];
  const PHONE_TYPES = ["du", "etisalat"];
  const PLATE_TYPES = EMIRATE_TYPES.concat(PHONE_TYPES);
  const PLATE_IMAGES = {
    abudhabi: "abudhabi.jpg", dubai: "dubai.jpg", dubai_yellow: "dubai_classic.jpg",
    rasalkhimma: "rasalkhimma.jpg", fujairah: "fujairah.jpg", ajman: "ajman.jpg",
    ummalquain: "ummalquain.jpg", sharjah: "sharjah.jpg", du: "du.png", etisalat: "etisalat.png",
  };
  const CLASS_BY_TYPE = {
    abudhabi: "abudhabi", dubai: "dubai", dubai_yellow: "dubai-yellow",
    rasalkhimma: "rasalkhimma", fujairah: "fujairah", ajman: "ajman",
    ummalquain: "ummalquain", sharjah: "sharjah", du: "du", etisalat: "etisalat",
  };

  const els = {
    root: document.querySelector(".nld-root"),
    body: document.body,
    frame: document.getElementById("nld-plate-frame"),
    idleLabel: document.getElementById("nld-idle-label"),
    plateGlow: document.getElementById("nld-plate-glow"),
    plateStage: document.querySelector(".nld-plate-stage"),
    timerWrap: document.querySelector(".nld-timer-wrap"),
    timer: document.getElementById("nld-timer"),
    timerState: document.getElementById("nld-timer-state"),
    timerProgress: document.getElementById("nld-timer-progress-bar"),
    price: document.getElementById("nld-price"),
    priceValue: document.getElementById("nld-price-value"),
    alert: document.getElementById("nld-alert"),
    alertText: document.getElementById("nld-alert-text"),
    eventTitle: document.getElementById("nld-event-title"),
    ticker: document.getElementById("nld-ticker"),
    tickerTrack: document.getElementById("nld-ticker-track"),
    header: document.getElementById("nld-header"),
    logoWrap: document.querySelector(".nld-logo-wrap"),
    customLogo: document.getElementById("nld-custom-logo"),
    soldOverlay: document.getElementById("nld-sold-overlay"),
    soldPlate: document.getElementById("nld-sold-plate"),
    soldPrice: document.getElementById("nld-sold-price"),
    soldName: document.getElementById("nld-sold-name"),
    confetti: document.getElementById("nld-confetti"),
    fireworks: document.getElementById("nld-fireworks"),
    beamLayer: document.getElementById("nld-beam-layer"),
    beamArm: document.getElementById("nld-beam-arm"),
    beamTag: document.getElementById("nld-beam-tag"),
    agingFx: document.getElementById("nld-aging-fx"),
    wmH2: document.getElementById("nld-wm-h2"),
    wmSun: document.getElementById("nld-wm-sunmix"),
    kanduraLayer: document.getElementById("nld-kandura-layer"),
    kanduraFigure: document.getElementById("nld-kandura-figure"),
    kanduraArmR: document.getElementById("nld-kandura-arm-r"),
    kanduraVideo: document.getElementById("nld-kandura-video"),
  };

  let state = config.state || {};
  let spinnerIndex = 0;
  let spinnerTimer = null;
  let lastPrice = "";
  let soldTimer = null;
  let soldRunning = false;
  let lastSoldEventId = Number(state.sold_event_id) || 0;
  let lastEvents = Object.assign({}, (state.new_style && state.new_style.events) || {});
  let revealPlaying = false;
  let beamPlaying = false;
  let dropPlaying = false;
  let kanduraPlaying = false;
  let agingRaf = null;
  let fireworksRaf = null;
  let agingProgress = 0;
  let agingFragments = [];
  let clockOffsetMs = 0;

  function ns() {
    return state.new_style || {};
  }

  function events() {
    return (ns().events) || {};
  }

  function normalizeType(plateType) {
    return PLATE_TYPES.includes(plateType) ? plateType : "dubai";
  }

  function classForType(plateType) {
    return CLASS_BY_TYPE[normalizeType(plateType)] || "dubai";
  }

  function isPhoneType(plateType) {
    return PHONE_TYPES.includes(plateType);
  }

  function isPlateEmpty(currentState) {
    if (isPhoneType(currentState.plate_type)) return false;
    return !String(currentState.code || "").trim() && !String(currentState.number || "").trim();
  }

  function getDisplayType(currentState) {
    if (isPhoneType(currentState.plate_type)) return currentState.plate_type;
    if (isPlateEmpty(currentState)) {
      const idx = ((spinnerIndex % EMIRATE_TYPES.length) + EMIRATE_TYPES.length) % EMIRATE_TYPES.length;
      return EMIRATE_TYPES[idx];
    }
    return normalizeType(currentState.plate_type);
  }

  function startSpinner() {
    if (spinnerTimer) return;
    spinnerTimer = setInterval(() => {
      spinnerIndex = (spinnerIndex + 1) % EMIRATE_TYPES.length;
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

  function syncClockOffset() {
    if (!state.server_now) return;
    const serverMs = Date.parse(state.server_now);
    if (!Number.isNaN(serverMs)) {
      clockOffsetMs = serverMs - Date.now();
    }
  }

  function nowMs() {
    return Date.now() + clockOffsetMs;
  }

  function numberVisible() {
    return ns().number_visible !== false;
  }

  function applyNumberVisibility(playReveal) {
    const visible = numberVisible();
    const overlays = els.frame?.querySelectorAll(".nld-plate-text-overlay") || [];
    overlays.forEach((el) => {
      el.classList.toggle("nld-number-hidden", !visible);
      if (playReveal && visible) {
        el.classList.remove("nld-reveal-play");
        void el.offsetWidth;
        el.classList.add("nld-reveal-play");
      }
    });
  }

  function renderPlate(targetFrame, plateType, code, number, options = {}) {
    const frame = targetFrame || els.frame;
    if (!frame) return;

    const type = normalizeType(plateType || getDisplayType(state));
    const fileName = PLATE_IMAGES[type] || PLATE_IMAGES.dubai;
    const className = classForType(type);
    const isPhone = isPhoneType(type);
    const phoneNumber = options.phoneNumber !== undefined ? options.phoneNumber : state.phone_number;
    const renderKey = [type, fileName, IMAGE_BASE, IMAGE_VERSION, isPhone ? "phone" : "plate"].join("|");

    if (frame.dataset.newPlateRenderKey === renderKey) {
      if (isPhone) {
        const phoneEl = frame.querySelector(".nld-plate-phone");
        if (phoneEl) phoneEl.textContent = phoneNumber || "";
      } else {
        const codeEl = frame.querySelector(".nld-plate-code");
        const numberEl = frame.querySelector(".nld-plate-number");
        if (codeEl) codeEl.textContent = code || "";
        if (numberEl) numberEl.textContent = number || "";
      }
      if (!options.sold) applyNumberVisibility(false);
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
    img.alt = isPhone ? "Phone number" : "Plate";
    img.src = `${IMAGE_BASE}${fileName}?v=${IMAGE_VERSION}`;
    canvas.appendChild(img);

    const agingOverlay = document.createElement("div");
    agingOverlay.className = "nld-aging-overlay";
    agingOverlay.setAttribute("aria-hidden", "true");
    canvas.appendChild(agingOverlay);

    const crackSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    crackSvg.setAttribute("class", "nld-aging-cracks");
    crackSvg.setAttribute("viewBox", "0 0 100 100");
    crackSvg.setAttribute("preserveAspectRatio", "none");
    crackSvg.innerHTML = `
      <path class="nld-crack nld-crack-1" d="M12 18 L28 34 L22 52 L40 70" />
      <path class="nld-crack nld-crack-2" d="M78 14 L62 30 L70 48 L55 66 L68 82" />
      <path class="nld-crack nld-crack-3" d="M48 8 L50 28 L44 46 L58 62 L46 84" />
      <path class="nld-crack nld-crack-4" d="M18 78 L34 68 L52 74 L70 60" />
    `;
    canvas.appendChild(crackSvg);

    if (isPhone) {
      const phoneOverlay = document.createElement("div");
      phoneOverlay.className = "nld-plate-text-overlay nld-plate-phone-overlay";
      const phoneEl = document.createElement("div");
      phoneEl.className = "nld-plate-phone";
      phoneEl.textContent = phoneNumber || "";
      phoneOverlay.appendChild(phoneEl);
      canvas.appendChild(phoneOverlay);
    } else {
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
    }

    slide.appendChild(canvas);
    frame.appendChild(slide);

    if (options.sold) {
      frame.dataset.newPlateRenderKey = `${renderKey}|sold`;
    } else {
      applyNumberVisibility(false);
      applyAgingVisual(agingProgress);
    }
  }

  function renderCurrentPlate() {
    const type = getDisplayType(state);
    renderPlate(els.frame, type, state.code, state.number, {
      phoneNumber: state.phone_number,
    });
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
      // Feature B: remove STANDBY / CLOSING labels; only show COUNTDOWN while active.
      if (active && !urgent && !expired) {
        els.timerState.hidden = false;
        els.timerState.textContent = "COUNTDOWN";
      } else if (expired) {
        els.timerState.hidden = false;
        els.timerState.textContent = "CLOSED";
      } else {
        els.timerState.hidden = true;
        els.timerState.textContent = "";
      }
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

  function renderEventTitle() {
    if (!els.eventTitle) return;
    const title = String(state.event_title || "").trim() || "مزاد علني مباشر لبيع وشراء الأرقام المميزة";
    if (els.eventTitle.textContent !== title) els.eventTitle.textContent = title;
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
        span.className = "nld-ticker-msg";
        span.textContent = message;
        if (i === 1) span.setAttribute("aria-hidden", "true");
        els.tickerTrack.appendChild(span);
      }
      const duration = Math.max(24, message.length * 0.55);
      els.tickerTrack.style.animation = "none";
      void els.tickerTrack.offsetWidth;
      els.tickerTrack.style.animation = `nld-ticker-rtl ${duration}s linear infinite`;
    }
    els.ticker.classList.add("visible");
  }

  function renderLogo() {
    const logoUrl = String(state.logo_url || "").trim();
    const logoVisible = state.header_logo_visible !== false;
    els.header?.classList.toggle("logo-hidden", !logoVisible);
    if (!els.logoWrap || !els.customLogo) return;
    if (logoUrl) {
      if (els.customLogo.getAttribute("src") !== logoUrl) els.customLogo.src = logoUrl;
      els.logoWrap.classList.add("has-custom");
    } else {
      els.customLogo.removeAttribute("src");
      els.logoWrap.classList.remove("has-custom");
    }
  }

  function renderBackground() {
    const id = ns().background_id || "stage_dark_01";
    els.body?.setAttribute("data-bg", id);
  }

  function applyWatermark(el, mark) {
    if (!el || !mark) return;
    const visible = Boolean(mark.visible);
    el.hidden = !visible;
    el.setAttribute("aria-hidden", visible ? "false" : "true");
    if (!visible) return;
    const x = Number(mark.x);
    const y = Number(mark.y);
    const scale = Number(mark.scale) || 1;
    el.style.left = `${(Number.isFinite(x) ? x : 0.05) * 100}%`;
    el.style.top = `${(Number.isFinite(y) ? y : 0.9) * 100}%`;
    el.style.transform = `translate(-50%, -50%) scale(${scale})`;
  }

  function renderWatermarks() {
    const marks = ns().watermarks || {};
    applyWatermark(els.wmH2, marks.h2);
    applyWatermark(els.wmSun, marks.sun_mix);
  }

  function computeAgingProgress() {
    const aging = ns().aging || {};
    const startedAt = aging.started_at ? Date.parse(aging.started_at) : NaN;
    if (!startedAt || Number.isNaN(startedAt) || isPlateEmpty(state)) {
      return 0;
    }
    const fresh = Math.max(0, Number(aging.fresh_delay_seconds) || 50);
    const duration = Math.max(1, Number(aging.aging_duration_seconds) || 10);
    let elapsed = (nowMs() - startedAt) / 1000;
    if (aging.paused) {
      elapsed = Number(aging.paused_elapsed_seconds) || 0;
    }
    if (elapsed < fresh) return 0;
    if (elapsed >= fresh + duration) return 1;
    return (elapsed - fresh) / duration;
  }

  function applyAgingVisual(t) {
    agingProgress = Math.max(0, Math.min(1, t));
    const slide = els.frame?.querySelector(".nld-plate-slide");
    const canvas = els.frame?.querySelector(".nld-plate-canvas");
    const overlay = els.frame?.querySelector(".nld-aging-overlay");
    const cracks = els.frame?.querySelector(".nld-aging-cracks");
    if (!slide || !canvas) return;

    const fade = Math.min(1, agingProgress / 0.3);
    const deform = Math.max(0, Math.min(1, (agingProgress - 0.3) / 0.3));
    const crack = Math.max(0, Math.min(1, (agingProgress - 0.6) / 0.3));
    const finale = Math.max(0, Math.min(1, (agingProgress - 0.9) / 0.1));

    const scale = 1 - deform * 0.12 - finale * 0.04;
    const rot = (deform * 1.6 + finale * 2.2) * (agingProgress > 0.5 ? 1 : -1);
    const skew = deform * 2.5;
    const warpY = deform * 4 + finale * 3;

    canvas.style.filter = agingProgress <= 0
      ? ""
      : `saturate(${1 - fade * 0.55}) brightness(${1 - fade * 0.18}) contrast(${1 + fade * 0.15 + crack * 0.1})`;
    slide.style.transform = agingProgress <= 0
      ? ""
      : `scale(${scale}) rotate(${rot}deg) skewX(${skew * 0.2}deg) translateY(${warpY}px)`;
    slide.classList.toggle("nld-aging-shake", finale > 0 && finale < 1);

    if (overlay) {
      overlay.style.opacity = String(fade * 0.55 + deform * 0.25);
    }
    if (cracks) {
      cracks.style.opacity = String(Math.max(crack * 0.95, finale));
      cracks.querySelectorAll(".nld-crack").forEach((path, idx) => {
        const threshold = idx * 0.18;
        const local = Math.max(0, Math.min(1, (crack - threshold) / 0.55));
        path.style.strokeDashoffset = String(120 * (1 - local));
        path.style.opacity = String(local);
      });
    }

    drawAgingFragments(crack, finale);
  }

  function ensureAgingCanvas() {
    if (!els.agingFx || !els.plateStage) return null;
    const rect = els.plateStage.getBoundingClientRect();
    const w = Math.max(1, Math.floor(rect.width));
    const h = Math.max(1, Math.floor(rect.height));
    if (els.agingFx.width !== w || els.agingFx.height !== h) {
      els.agingFx.width = w;
      els.agingFx.height = h;
    }
    return els.agingFx.getContext("2d");
  }

  function drawAgingFragments(crack, finale) {
    const ctx = ensureAgingCanvas();
    if (!ctx || !els.agingFx) return;
    ctx.clearRect(0, 0, els.agingFx.width, els.agingFx.height);
    if (crack <= 0 && finale <= 0) {
      agingFragments = [];
      return;
    }

    const targetCount = Math.floor(crack * 18 + finale * 10);
    while (agingFragments.length < targetCount) {
      agingFragments.push({
        x: els.agingFx.width * (0.2 + Math.random() * 0.6),
        y: els.agingFx.height * (0.25 + Math.random() * 0.4),
        vx: (Math.random() - 0.5) * 1.4,
        vy: 0.4 + Math.random() * 1.8,
        r: 2 + Math.random() * 5,
        rot: Math.random() * Math.PI,
        vr: (Math.random() - 0.5) * 0.2,
        life: 1,
      });
    }

    agingFragments.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.05;
      p.rot += p.vr;
      p.life -= 0.004;
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.globalAlpha = Math.max(0, p.life) * (0.35 + crack * 0.55);
      ctx.fillStyle = finale > 0 ? "#c4b59a" : "#9a8b72";
      ctx.fillRect(-p.r, -p.r * 0.6, p.r * 2, p.r * 1.2);
      ctx.restore();
    });
    agingFragments = agingFragments.filter((p) => p.life > 0 && p.y < els.agingFx.height + 20);
  }

  function tickAging() {
    applyAgingVisual(computeAgingProgress());
    agingRaf = requestAnimationFrame(tickAging);
  }

  function startAgingLoop() {
    if (agingRaf) return;
    agingRaf = requestAnimationFrame(tickAging);
  }

  function playReveal() {
    if (revealPlaying || REDUCE_MOTION) {
      applyNumberVisibility(false);
      return;
    }
    revealPlaying = true;
    applyNumberVisibility(true);
    setTimeout(() => {
      revealPlaying = false;
      const overlays = els.frame?.querySelectorAll(".nld-plate-text-overlay") || [];
      overlays.forEach((el) => el.classList.remove("nld-reveal-play"));
    }, 900);
  }

  function playBeam() {
    if (!els.beamLayer || beamPlaying) return;
    beamPlaying = true;
    els.beamLayer.classList.remove("playing", "tag");
    void els.beamLayer.offsetWidth;
    els.beamLayer.classList.add("playing");
    els.beamLayer.setAttribute("aria-hidden", "false");
    const orbitsMs = REDUCE_MOTION ? 900 : 2400;
    setTimeout(() => {
      els.beamLayer?.classList.add("tag");
    }, orbitsMs);
    setTimeout(() => {
      els.beamLayer?.classList.remove("playing", "tag");
      els.beamLayer?.setAttribute("aria-hidden", "true");
      beamPlaying = false;
    }, orbitsMs + 700);
  }

  function playDrop() {
    if (dropPlaying) return;
    const overlays = Array.from(els.frame?.querySelectorAll(".nld-plate-text-overlay") || []);
    if (!overlays.length) return;
    dropPlaying = true;
    els.plateStage?.classList.add("nld-local-shake");
    overlays.forEach((overlay, idx) => {
      const clone = overlay.cloneNode(true);
      clone.classList.add("nld-drop-clone");
      clone.style.setProperty("--drop-delay", `${idx * 40}ms`);
      overlay.parentElement?.appendChild(clone);
      overlay.classList.add("nld-number-hidden");
      setTimeout(() => clone.remove(), 1200);
    });
    setTimeout(() => {
      els.plateStage?.classList.remove("nld-local-shake");
      dropPlaying = false;
      applyNumberVisibility(false);
    }, 1300);
  }

  function playKandura() {
    if (kanduraPlaying || !els.kanduraLayer) return;
    kanduraPlaying = true;
    const prefs = ns().kandura || {};
    const entry = prefs.entry === "right" ? "right" : "left";
    const speed = Math.max(0.25, Number(prefs.speed) || 1);
    const pointMs = Math.max(200, Number(prefs.point_ms) || 1500);
    els.kanduraLayer.dataset.entry = entry;
    els.kanduraLayer.style.setProperty("--kandura-speed", String(speed));
    els.kanduraLayer.style.setProperty("--kandura-point-ms", `${pointMs}ms`);
    els.kanduraLayer.setAttribute("aria-hidden", "false");
    els.kanduraLayer.classList.remove("playing", "pointing", "exiting");
    void els.kanduraLayer.offsetWidth;

    const video = els.kanduraVideo;
    let usedVideo = false;
    if (video && KANDURA_VIDEO_URL) {
      video.hidden = false;
      els.kanduraFigure?.classList.add("nld-kandura-fallback-hidden");
      video.src = KANDURA_VIDEO_URL;
      const playPromise = video.play();
      if (playPromise && typeof playPromise.then === "function") {
        playPromise.then(() => {
          usedVideo = true;
        }).catch(() => {
          video.hidden = true;
          els.kanduraFigure?.classList.remove("nld-kandura-fallback-hidden");
        });
      }
    } else {
      els.kanduraFigure?.classList.remove("nld-kandura-fallback-hidden");
      if (video) video.hidden = true;
    }

    els.kanduraLayer.classList.add("playing");
    const enterMs = (REDUCE_MOTION ? 600 : 1800) / speed;
    setTimeout(() => {
      els.kanduraLayer?.classList.add("pointing");
    }, enterMs);
    setTimeout(() => {
      els.kanduraLayer?.classList.remove("pointing");
      els.kanduraLayer?.classList.add("exiting");
    }, enterMs + pointMs);
    setTimeout(() => {
      els.kanduraLayer?.classList.remove("playing", "pointing", "exiting");
      els.kanduraLayer?.setAttribute("aria-hidden", "true");
      if (video) {
        video.pause();
        video.hidden = true;
        video.removeAttribute("src");
        video.load();
      }
      els.kanduraFigure?.classList.remove("nld-kandura-fallback-hidden");
      kanduraPlaying = false;
      void usedVideo;
    }, enterMs + pointMs + enterMs + 200);
  }

  function handleNewStyleEvents() {
    const next = events();
    const prev = lastEvents || {};

    if ((Number(next.reveal_event_id) || 0) > (Number(prev.reveal_event_id) || 0)) {
      playReveal();
    }
    if ((Number(next.hide_event_id) || 0) > (Number(prev.hide_event_id) || 0)) {
      applyNumberVisibility(false);
    }
    if ((Number(next.reveal_replay_event_id) || 0) > (Number(prev.reveal_replay_event_id) || 0)) {
      playReveal();
    }
    if ((Number(next.beam_event_id) || 0) > (Number(prev.beam_event_id) || 0)) {
      playBeam();
    }
    if ((Number(next.drop_event_id) || 0) > (Number(prev.drop_event_id) || 0)) {
      playDrop();
    }
    if ((Number(next.kandura_event_id) || 0) > (Number(prev.kandura_event_id) || 0)) {
      playKandura();
    }
    // aging reset/replay: visual clock resyncs via started_at; no one-shot needed beyond progress
    lastEvents = Object.assign({}, next);
  }

  function renderAll() {
    syncClockOffset();
    syncSpinner();
    renderBackground();
    renderCurrentPlate();
    renderTimer();
    renderPrice();
    renderAlert();
    renderEventTitle();
    renderTicker();
    renderLogo();
    renderWatermarks();
    applyAgingVisual(computeAgingProgress());
  }

  function handleSoldEvent() {
    const soldEventId = Number(state.sold_event_id) || 0;
    if (!soldEventId || soldEventId <= lastSoldEventId) return;
    lastSoldEventId = soldEventId;
    window.triggerSoldCelebration({
      plateType: state.plate_type,
      code: state.code,
      number: state.number,
      phoneNumber: state.phone_number,
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
      handleNewStyleEvents();
    } catch (err) {
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

  function normalizeSoldStyle(style) {
    if (style === "gavel") return "fireworks"; // New Style: gavel remapped away
    if (style === "confetti") return "confetti";
    return "fireworks";
  }

  function stopFireworks() {
    if (fireworksRaf) {
      cancelAnimationFrame(fireworksRaf);
      fireworksRaf = null;
    }
    if (els.fireworks) {
      const ctx = els.fireworks.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, els.fireworks.width, els.fireworks.height);
    }
  }

  function playFireworks(durationMs) {
    if (!els.fireworks) {
      makeConfetti();
      return;
    }
    const canvas = els.fireworks;
    const parent = canvas.parentElement;
    const rect = parent ? parent.getBoundingClientRect() : { width: 1920, height: 1080 };
    canvas.width = Math.max(1, Math.floor(rect.width));
    canvas.height = Math.max(1, Math.floor(rect.height));
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      makeConfetti();
      return;
    }

    const particles = [];
    const bursts = [];
    const colors = ["#ff4d6d", "#ffd166", "#7c3aed", "#4cc9f0", "#ffffff", "#f72585", "#b8f2e6"];
    const start = performance.now();
    let lastBurst = 0;

    function spawnBurst() {
      const cx = canvas.width * (0.2 + Math.random() * 0.6);
      const cy = canvas.height * (0.15 + Math.random() * 0.35);
      const count = REDUCE_MOTION ? 18 : 42;
      for (let i = 0; i < count; i += 1) {
        const angle = (Math.PI * 2 * i) / count + Math.random() * 0.2;
        const speed = 2 + Math.random() * 5;
        particles.push({
          x: cx,
          y: cy,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 1,
          color: colors[Math.floor(Math.random() * colors.length)],
          size: 1.5 + Math.random() * 2.5,
          trail: Math.random() > 0.55,
        });
      }
      bursts.push({ x: cx, y: cy, r: 0, life: 1 });
    }

    function frame(now) {
      const elapsed = now - start;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (elapsed - lastBurst > (REDUCE_MOTION ? 420 : 280) && elapsed < durationMs - 800) {
        spawnBurst();
        lastBurst = elapsed;
      }
      bursts.forEach((b) => {
        b.r += 4;
        b.life -= 0.04;
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255,255,255,${Math.max(0, b.life) * 0.35})`;
        ctx.lineWidth = 2;
        ctx.stroke();
      });
      for (let i = bursts.length - 1; i >= 0; i -= 1) {
        if (bursts[i].life <= 0) bursts.splice(i, 1);
      }
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.04;
        p.vx *= 0.99;
        p.life -= 0.012;
        ctx.globalAlpha = Math.max(0, p.life);
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        if (p.trail) {
          ctx.strokeStyle = p.color;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x - p.vx * 3, p.y - p.vy * 3);
          ctx.stroke();
        }
      });
      for (let i = particles.length - 1; i >= 0; i -= 1) {
        if (particles[i].life <= 0) particles.splice(i, 1);
      }
      ctx.globalAlpha = 1;
      if (elapsed < durationMs) {
        fireworksRaf = requestAnimationFrame(frame);
      } else {
        stopFireworks();
      }
    }

    stopFireworks();
    spawnBurst();
    fireworksRaf = requestAnimationFrame(frame);
  }

  window.triggerSoldCelebration = function (details = {}) {
    if (soldRunning) {
      clearTimeout(soldTimer);
      stopFireworks();
      els.soldOverlay?.classList.remove("visible", "sold-style-gavel", "sold-style-confetti", "sold-style-fireworks");
      void els.soldOverlay?.offsetWidth;
    }

    soldRunning = true;
    const style = normalizeSoldStyle(details.style || details.sold_style || state.sold_style);
    const detail = {
      plateType: details.plateType || details.plate_type || state.plate_type || getDisplayType(state),
      code: details.code !== undefined ? details.code : state.code,
      number: details.number !== undefined ? details.number : state.number,
      phoneNumber: details.phoneNumber !== undefined ? details.phoneNumber : (details.phone_number !== undefined ? details.phone_number : state.phone_number),
      price: details.price !== undefined ? details.price : state.price,
      name: details.name !== undefined ? details.name : (details.sold_name !== undefined ? details.sold_name : state.sold_name),
    };

    els.soldOverlay?.classList.remove("sold-style-gavel", "sold-style-confetti", "sold-style-fireworks");
    els.soldOverlay?.classList.add(style === "confetti" ? "sold-style-confetti" : "sold-style-fireworks");

    renderPlate(els.soldPlate, detail.plateType, detail.code, detail.number, {
      sold: true,
      phoneNumber: detail.phoneNumber,
    });
    if (els.soldName) {
      const name = String(detail.name || "").trim();
      els.soldName.textContent = name;
      els.soldName.hidden = !name;
    }
    if (els.soldPrice) {
      const price = formatPrice(detail.price);
      els.soldPrice.textContent = price ? `AED ${price}` : "";
    }

    if (els.confetti) els.confetti.innerHTML = "";
    if (style === "confetti") {
      makeConfetti();
    } else {
      playFireworks(5200);
    }

    els.soldOverlay?.classList.add("visible");
    els.soldOverlay?.setAttribute("aria-hidden", "false");

    soldTimer = setTimeout(() => {
      els.soldOverlay?.classList.remove("visible", "sold-style-gavel", "sold-style-confetti", "sold-style-fireworks");
      els.soldOverlay?.setAttribute("aria-hidden", "true");
      stopFireworks();
      soldRunning = false;
    }, style === "confetti" ? 5000 : 5500);
  };

  window.addEventListener("auction:sold", function (event) {
    window.triggerSoldCelebration(event.detail || {});
  });

  lastEvents = Object.assign({}, events());
  renderAll();
  startAgingLoop();
  setInterval(pollState, 1000);
})();
