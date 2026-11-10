(function () {
  const config = window.LIVE_DISPLAY_NEW_CONFIG || {};
  const TOKEN = config.token || "";
  const API_URL = config.apiUrl || "/live/api/state/";
  const IMAGE_BASE = config.imageBaseUrl || "/static/live_new/plates/";
  const IMAGE_VERSION = config.plateImageVersion || "1";
  const BG_PLATES_BASE = config.bgPlatesBaseUrl || "/static/live_new/v3/bg_plates/";
  const SOLD_STAMP_URL = config.soldStampUrl || "/static/live_new/v3/sold/stamp.png";
  const CHAR_ASSETS = Object.assign({
    point: "/static/live_new/v3/character/point.webm",
    yellow: "/static/live_new/v3/character/yellow.webm",
    red: "/static/live_new/v3/character/red.webm",
    sold_stamp: "/static/live_new/v3/character/sold_stamp.webm",
  }, config.characterAssets || {});
  const DEBUG_CHAR_STUB = Boolean(config.debugCharacterStub);
  const M1_PREVIEW = Boolean(config.m1Preview);
  const REDUCE_MOTION = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const LETTER_CODES = (function () {
    const single = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    return single.concat(single.map((ch) => ch + ch));
  })();

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
    plateRim: document.getElementById("nld-plate-rim"),
    redSmoke: document.getElementById("nld-red-smoke"),
    plateStage: document.querySelector(".nld-plate-stage"),
    timerWrap: document.querySelector(".nld-timer-capsule") || document.querySelector(".nld-timer-wrap"),
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
    soldStamp: document.getElementById("nld-sold-stamp"),
    confetti: document.getElementById("nld-confetti"),
    fireworks: document.getElementById("nld-fireworks"),
    plateFw: document.getElementById("nld-plate-fw"),
    beamLayer: document.getElementById("nld-beam-layer"),
    beamArm: document.getElementById("nld-beam-arm"),
    beamTag: document.getElementById("nld-beam-tag"),
    agingFx: document.getElementById("nld-aging-fx"),
    wmH2: document.getElementById("nld-wm-h2"),
    bgPlates: document.getElementById("nld-bg-plates-layer"),
    characterLayer: document.getElementById("nld-character-layer"),
    characterVideo: document.getElementById("nld-character-video"),
    characterStub: document.getElementById("nld-character-debug-stub"),
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
  let characterBusy = false;
  let agingRaf = null;
  let fireworksRaf = null;
  let plateFwRaf = null;
  let bgPlatesRaf = null;
  let agingProgress = 0;
  let agingFragments = [];
  let clockOffsetMs = 0;
  let bgSprites = [];
  let bgBuilt = false;
  let tabHidden = document.hidden;
  let assetPresence = { point: null, yellow: null, red: null, sold_stamp: null };

  function ns() {
    return state.new_style || {};
  }

  function events() {
    return (ns().events) || {};
  }

  function characterPrefs() {
    const c = ns().character || {};
    const k = ns().kandura || {};
    return {
      entry: (c.entry || k.entry) === "right" ? "right" : "left",
      speed: Math.max(0.25, Number(c.speed != null ? c.speed : k.speed) || 1),
    };
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
    if (M1_PREVIEW) return true;
    return ns().number_visible !== false;
  }

  function applyNumberVisibility(playReveal) {
    // M1 preview always shows full code/number — never honor persisted hide/red-card state.
    const visible = numberVisible();
    const overlays = els.frame?.querySelectorAll(".nld-plate-text-overlay") || [];
    overlays.forEach((el) => {
      if (M1_PREVIEW || visible) {
        el.classList.remove("nld-number-hidden");
      } else {
        el.classList.add("nld-number-hidden");
      }
      if (playReveal && visible && !M1_PREVIEW) {
        el.classList.remove("nld-reveal-play", "nld-reveal-cinematic");
        void el.offsetWidth;
        el.classList.add("nld-reveal-play", "nld-reveal-cinematic");
      }
    });
    if (M1_PREVIEW) {
      els.plateStage?.classList.remove(
        "nld-number-hidden-stage",
        "nld-yellow-card",
        "nld-red-card",
        "nld-local-shake",
        "nld-reveal-flash",
      );
      els.redSmoke?.classList.remove("active");
      if (els.redSmoke) els.redSmoke.setAttribute("aria-hidden", "true");
      els.plateRim?.classList.remove("yellow", "red");
      return;
    }
    els.plateStage?.classList.toggle("nld-number-hidden-stage", !visible);
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

    const rustOverlay = document.createElement("div");
    rustOverlay.className = "nld-aging-rust";
    rustOverlay.setAttribute("aria-hidden", "true");
    canvas.appendChild(rustOverlay);

    const crackSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    crackSvg.setAttribute("class", "nld-aging-cracks");
    crackSvg.setAttribute("viewBox", "0 0 100 100");
    crackSvg.setAttribute("preserveAspectRatio", "none");
    crackSvg.innerHTML = `
      <path class="nld-crack nld-crack-1" d="M10 16 L26 30 L18 48 L36 66 L28 84" />
      <path class="nld-crack nld-crack-2" d="M82 12 L64 28 L72 46 L54 64 L66 86" />
      <path class="nld-crack nld-crack-3" d="M48 6 L52 24 L44 42 L60 58 L46 78 L58 94" />
      <path class="nld-crack nld-crack-4" d="M16 80 L34 70 L52 78 L74 58 L88 68" />
      <path class="nld-crack nld-crack-5" d="M30 10 L38 22 L34 40 L48 52" />
      <path class="nld-crack nld-crack-6" d="M70 20 L58 36 L66 50 L50 70" />
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

    // #region agent log
    (function () {
      const endMs = state.timer_ends_at ? Date.parse(state.timer_ends_at) : NaN;
      const localFromEnds = Number.isFinite(endMs)
        ? Math.max(0, Math.floor((endMs - nowMs()) / 1000))
        : null;
      const painted = els.timer ? els.timer.textContent : null;
      fetch('http://127.0.0.1:7650/ingest/6effd724-0433-4a9b-be69-34787675ecdc',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ddcc38'},body:JSON.stringify({sessionId:'ddcc38',runId:'pre-fix',hypothesisId:'B',location:'live-display-new.js:renderTimer',message:'timer paint',data:{active:active,remainingFromState:remaining,localFromEndsAt:localFromEnds,lagSeconds:(localFromEnds==null?null:(remaining-localFromEnds)),timerEndsAt:state.timer_ends_at||null,clockOffsetMs:clockOffsetMs,paintedBefore:painted,source:'poll-or-renderAll'},timestamp:Date.now()})}).catch(()=>{});
    })();
    // #endregion

    if (els.timer) els.timer.textContent = formatTimer(remaining);
    if (els.timerProgress) els.timerProgress.style.width = `${progress}%`;
    if (els.timerState) {
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
    if (M1_PREVIEW) {
      els.alert?.classList.remove("visible");
      if (els.alertText) els.alertText.textContent = "";
      return;
    }
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
    const title = String(state.event_title || "").trim();
    if (!title) {
      els.eventTitle.hidden = true;
      els.eventTitle.textContent = "";
      return;
    }
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
    if (!els.logoWrap || !els.customLogo) return;
    const logoUrl = String(state.logo_url || "").trim();
    const logoVisible = state.header_logo_visible !== false;
    els.header?.classList.toggle("logo-hidden", !logoVisible);
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
  }

  /* ---- M2 background floating letter plates ---- */
  function pickLetterCode(seed) {
    const idx = Math.abs(Math.floor(seed)) % LETTER_CODES.length;
    return LETTER_CODES[idx];
  }

  function densityCount(density) {
    const d = Math.max(0.25, Math.min(2, Number(density) || 1));
    return Math.max(4, Math.round(10 * d));
  }

  function buildBgPlates(force) {
    if (!els.bgPlates) return;
    if (M1_PREVIEW || ns().bg_motion_enabled === false) {
      els.bgPlates.innerHTML = "";
      bgSprites = [];
      bgBuilt = false;
      delete els.bgPlates.dataset.densityKey;
      return;
    }
    const density = ns().bg_density != null ? ns().bg_density : 1;
    const count = densityCount(density);
    const key = `${count}|${BG_PLATES_BASE}`;
    if (!force && bgBuilt && els.bgPlates.dataset.densityKey === key) return;
    els.bgPlates.innerHTML = "";
    bgSprites = [];
    for (let i = 0; i < count; i += 1) {
      const code = pickLetterCode(i * 17 + count * 3);
      if (/\d/.test(code)) continue;
      const layer = 1 + (i % 3);
      const el = document.createElement("img");
      el.className = `nld-bg-plate nld-bg-layer-${layer}`;
      el.alt = "";
      el.decoding = "async";
      el.src = `${BG_PLATES_BASE}${code}.svg?v=v3-m2`;
      el.dataset.code = code;
      const sprite = {
        el,
        layer,
        x: Math.random() * 100,
        y: Math.random() * 100,
        driftX: (Math.random() - 0.5) * (0.008 + layer * 0.004),
        driftY: (Math.random() - 0.5) * (0.006 + layer * 0.003),
        rot: (Math.random() - 0.5) * 18,
        scale: 0.45 + Math.random() * 0.55 + layer * 0.08,
        opacity: 0.12 + layer * 0.08,
      };
      el.style.opacity = String(sprite.opacity);
      els.bgPlates.appendChild(el);
      bgSprites.push(sprite);
    }
    els.bgPlates.dataset.densityKey = key;
    bgBuilt = true;
    positionBgSprites();
  }

  function positionBgSprites() {
    bgSprites.forEach((s) => {
      s.el.style.transform = `translate(${s.x}vw, ${s.y}vh) rotate(${s.rot}deg) scale(${s.scale})`;
    });
  }

  function bgMotionEnabled() {
    if (M1_PREVIEW) return false;
    if (tabHidden) return false;
    if (REDUCE_MOTION) return false;
    return Boolean(ns().bg_motion_enabled);
  }

  function tickBgPlates() {
    const enabled = bgMotionEnabled();
    els.bgPlates?.classList.toggle("paused", !enabled);
    if (enabled) {
      const speed = Math.max(0.25, Math.min(3, Number(ns().bg_speed) || 1));
      bgSprites.forEach((s) => {
        const layerMul = s.layer * 0.55;
        s.x += s.driftX * speed * (0.6 + layerMul);
        s.y += s.driftY * speed * (0.6 + layerMul);
        s.rot += 0.01 * speed * (s.layer * 0.4);
        if (s.x < -20) s.x = 110;
        if (s.x > 110) s.x = -20;
        if (s.y < -20) s.y = 110;
        if (s.y > 110) s.y = -20;
      });
      positionBgSprites();
    }
    bgPlatesRaf = requestAnimationFrame(tickBgPlates);
  }

  function startBgPlatesLoop() {
    buildBgPlates(false);
    if (!bgPlatesRaf) bgPlatesRaf = requestAnimationFrame(tickBgPlates);
  }

  function syncBgPlatesPrefs() {
    buildBgPlates(false);
  }

  document.addEventListener("visibilitychange", () => {
    tabHidden = document.hidden;
  });

  /* ---- Aging ---- */
  function computeAgingProgress() {
    if (M1_PREVIEW) return 0;
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
    agingProgress = M1_PREVIEW ? 0 : Math.max(0, Math.min(1, t));
    const slide = els.frame?.querySelector(".nld-plate-slide");
    const canvas = els.frame?.querySelector(".nld-plate-canvas");
    const overlay = els.frame?.querySelector(".nld-aging-overlay");
    const rust = els.frame?.querySelector(".nld-aging-rust");
    const cracks = els.frame?.querySelector(".nld-aging-cracks");
    if (!slide || !canvas) return;
    if (M1_PREVIEW) {
      canvas.style.filter = "";
      slide.style.transform = "";
      slide.classList.remove("nld-aging-shake");
      if (overlay) overlay.style.opacity = "0";
      if (rust) rust.style.opacity = "0";
      if (cracks) {
        cracks.style.opacity = "0";
        cracks.querySelectorAll(".nld-crack").forEach((path) => {
          path.style.opacity = "0";
        });
      }
      const ctx = ensureAgingCanvas();
      if (ctx && els.agingFx) ctx.clearRect(0, 0, els.agingFx.width, els.agingFx.height);
      agingFragments = [];
      return;
    }

    const fade = Math.min(1, agingProgress / 0.28);
    const deform = Math.max(0, Math.min(1, (agingProgress - 0.28) / 0.32));
    const crack = Math.max(0, Math.min(1, (agingProgress - 0.55) / 0.3));
    const finale = Math.max(0, Math.min(1, (agingProgress - 0.88) / 0.12));

    const scale = 1 - deform * 0.14 - finale * 0.05;
    const rot = (deform * 2.2 + finale * 2.8) * (agingProgress > 0.5 ? 1 : -1);
    const skew = deform * 3.2;
    const warpY = deform * 5 + finale * 4;

    canvas.style.filter = agingProgress <= 0
      ? ""
      : `saturate(${1 - fade * 0.65}) brightness(${1 - fade * 0.22}) contrast(${1 + fade * 0.2 + crack * 0.18}) sepia(${fade * 0.35})`;
    slide.style.transform = agingProgress <= 0
      ? ""
      : `scale(${scale}) rotate(${rot}deg) skewX(${skew * 0.22}deg) translateY(${warpY}px)`;
    slide.classList.toggle("nld-aging-shake", finale > 0 && finale < 1);
    slide.classList.toggle("nld-aging-final", finale >= 1);

    if (overlay) {
      overlay.style.opacity = String(fade * 0.62 + deform * 0.28);
    }
    if (rust) {
      rust.style.opacity = String(fade * 0.45 + deform * 0.4 + crack * 0.25);
    }
    if (cracks) {
      cracks.style.opacity = String(Math.max(crack * 0.98, finale));
      cracks.querySelectorAll(".nld-crack").forEach((path, idx) => {
        const threshold = idx * 0.12;
        const local = Math.max(0, Math.min(1, (crack - threshold) / 0.5));
        path.style.strokeDashoffset = String(140 * (1 - local));
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

    const targetCount = Math.floor(crack * 26 + finale * 16);
    while (agingFragments.length < targetCount) {
      agingFragments.push({
        x: els.agingFx.width * (0.18 + Math.random() * 0.64),
        y: els.agingFx.height * (0.22 + Math.random() * 0.45),
        vx: (Math.random() - 0.5) * 1.8,
        vy: 0.5 + Math.random() * 2.2,
        r: 2 + Math.random() * 6,
        rot: Math.random() * Math.PI,
        vr: (Math.random() - 0.5) * 0.28,
        life: 1,
        tone: Math.random(),
      });
    }

    agingFragments.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.055;
      p.rot += p.vr;
      p.life -= 0.0035;
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.globalAlpha = Math.max(0, p.life) * (0.4 + crack * 0.55);
      ctx.fillStyle = finale > 0
        ? (p.tone > 0.5 ? "#a87848" : "#6b4a2e")
        : (p.tone > 0.5 ? "#8a7050" : "#5c4632");
      ctx.fillRect(-p.r, -p.r * 0.55, p.r * 2, p.r * 1.15);
      ctx.restore();
    });
    agingFragments = agingFragments.filter((p) => p.life > 0 && p.y < els.agingFx.height + 24);
  }

  function tickAging() {
    applyAgingVisual(computeAgingProgress());
    agingRaf = requestAnimationFrame(tickAging);
  }

  function startAgingLoop() {
    if (agingRaf) return;
    agingRaf = requestAnimationFrame(tickAging);
  }

  /* ---- Reveal / beam / drop ---- */
  function playReveal() {
    if (revealPlaying || REDUCE_MOTION) {
      applyNumberVisibility(false);
      return;
    }
    revealPlaying = true;
    els.plateStage?.classList.add("nld-reveal-flash");
    applyNumberVisibility(true);
    setTimeout(() => {
      els.plateStage?.classList.remove("nld-reveal-flash");
      revealPlaying = false;
      const overlays = els.frame?.querySelectorAll(".nld-plate-text-overlay") || [];
      overlays.forEach((el) => el.classList.remove("nld-reveal-play", "nld-reveal-cinematic"));
    }, 1100);
  }

  function playBeam() {
    if (!els.beamLayer || beamPlaying) return;
    beamPlaying = true;
    els.beamLayer.classList.remove("playing", "tag");
    void els.beamLayer.offsetWidth;
    els.beamLayer.classList.add("playing");
    els.beamLayer.setAttribute("aria-hidden", "false");
    const orbitsMs = REDUCE_MOTION ? 700 : 2200;
    setTimeout(() => {
      els.beamLayer?.classList.add("tag");
    }, orbitsMs);
    setTimeout(() => {
      els.beamLayer?.classList.remove("playing", "tag");
      els.beamLayer?.setAttribute("aria-hidden", "true");
      beamPlaying = false;
    }, orbitsMs + 650);
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
      clone.style.setProperty("--drop-delay", `${idx * 35}ms`);
      overlay.parentElement?.appendChild(clone);
      overlay.classList.add("nld-number-hidden");
      setTimeout(() => clone.remove(), 1300);
    });
    setTimeout(() => {
      els.plateStage?.classList.remove("nld-local-shake");
      dropPlaying = false;
      applyNumberVisibility(false);
    }, 1400);
  }

  /* ---- Character harness (M4–M7) ---- */
  function probeAsset(key) {
    const url = CHAR_ASSETS[key];
    if (!url) {
      assetPresence[key] = false;
      return Promise.resolve(false);
    }
    return fetch(url, { method: "HEAD", cache: "no-store" })
      .then((res) => {
        assetPresence[key] = Boolean(res.ok);
        return assetPresence[key];
      })
      .catch(() => {
        assetPresence[key] = false;
        return false;
      });
  }

  function ensureAssetsProbed() {
    return Promise.all(["point", "yellow", "red", "sold_stamp"].map(probeAsset));
  }

  function clearCharacterVideo() {
    const video = els.characterVideo;
    if (!video) return;
    try {
      video.pause();
    } catch (e) { /* ignore */ }
    video.hidden = true;
    video.removeAttribute("src");
    video.load();
  }

  function showDebugStub(kind) {
    if (!DEBUG_CHAR_STUB || !els.characterStub) return;
    els.characterStub.hidden = false;
    els.characterStub.dataset.kind = kind;
    els.characterStub.setAttribute("aria-hidden", "false");
    els.characterStub.textContent = `debug:${kind}`;
  }

  function hideDebugStub() {
    if (!els.characterStub) return;
    els.characterStub.hidden = true;
    els.characterStub.setAttribute("aria-hidden", "true");
    els.characterStub.textContent = "";
  }

  function playCharacter(kind, extras = {}) {
    if (M1_PREVIEW) return;
    if (characterBusy) return;
    characterBusy = true;
    const prefs = characterPrefs();
    const entry = prefs.entry;
    const speed = prefs.speed;
    const layer = els.characterLayer;
    if (layer) {
      layer.dataset.entry = entry;
      layer.style.setProperty("--char-speed", String(speed));
      layer.setAttribute("aria-hidden", "false");
      layer.classList.remove("playing", "exiting", "kind-point", "kind-yellow", "kind-red", "kind-sold_stamp");
      layer.classList.add("playing", `kind-${kind}`);
    }

    if (extras.yellowRim) {
      els.plateStage?.classList.add("nld-yellow-card");
      els.plateRim?.classList.add("yellow");
    }
    if (extras.redFx) {
      els.plateStage?.classList.add("nld-red-card");
      els.redSmoke?.classList.add("active");
      applyNumberVisibility(false);
    }
    if (extras.soldStamp) {
      showSoldStampImprint();
      playPlateFireworks(4200);
    }

    const url = CHAR_ASSETS[kind];
    const video = els.characterVideo;
    const present = assetPresence[kind];
    let usedVideo = false;

    const finishMs = (REDUCE_MOTION ? 900 : 2800) / speed;

    function finish() {
      layer?.classList.add("exiting");
      setTimeout(() => {
        layer?.classList.remove("playing", "exiting", "kind-point", "kind-yellow", "kind-red", "kind-sold_stamp");
        layer?.setAttribute("aria-hidden", "true");
        clearCharacterVideo();
        hideDebugStub();
        if (extras.yellowRim) {
          els.plateStage?.classList.remove("nld-yellow-card");
          els.plateRim?.classList.remove("yellow");
        }
        if (extras.redFx) {
          els.plateStage?.classList.remove("nld-red-card");
          els.redSmoke?.classList.remove("active");
        }
        characterBusy = false;
      }, REDUCE_MOTION ? 200 : 500);
    }

    const startFinishTimer = (ms) => setTimeout(finish, ms);

    if (present && video && url) {
      video.hidden = false;
      video.muted = true;
      video.src = url;
      const playPromise = video.play();
      if (playPromise && typeof playPromise.then === "function") {
        playPromise.then(() => {
          usedVideo = true;
          const dur = Number.isFinite(video.duration) && video.duration > 0
            ? (video.duration * 1000) / speed
            : finishMs;
          video.onended = finish;
          startFinishTimer(Math.min(Math.max(dur, 800), 12000));
        }).catch(() => {
          showDebugStub(kind);
          startFinishTimer(finishMs);
        });
      } else {
        showDebugStub(kind);
        startFinishTimer(finishMs);
      }
    } else {
      // Missing asset: no CSS mannequin as production output.
      showDebugStub(kind);
      startFinishTimer(finishMs);
    }
    void usedVideo;
  }

  function showSoldStampImprint() {
    if (!els.soldStamp) return;
    els.soldStamp.hidden = false;
    els.soldStamp.setAttribute("aria-hidden", "false");
    els.soldStamp.classList.remove("imprint");
    void els.soldStamp.offsetWidth;
    els.soldStamp.classList.add("imprint");
  }

  function hideSoldStampImprint() {
    if (!els.soldStamp) return;
    els.soldStamp.classList.remove("imprint");
    els.soldStamp.hidden = true;
    els.soldStamp.setAttribute("aria-hidden", "true");
  }

  function ensurePlateFwCanvas() {
    if (!els.plateFw || !els.plateStage) return null;
    const rect = els.plateStage.getBoundingClientRect();
    const w = Math.max(1, Math.floor(rect.width));
    const h = Math.max(1, Math.floor(rect.height));
    if (els.plateFw.width !== w || els.plateFw.height !== h) {
      els.plateFw.width = w;
      els.plateFw.height = h;
    }
    return els.plateFw.getContext("2d");
  }

  function stopPlateFireworks() {
    if (plateFwRaf) {
      cancelAnimationFrame(plateFwRaf);
      plateFwRaf = null;
    }
    if (els.plateFw) {
      const ctx = els.plateFw.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, els.plateFw.width, els.plateFw.height);
    }
  }

  function playPlateFireworks(durationMs) {
    const ctx = ensurePlateFwCanvas();
    if (!ctx || !els.plateFw) return;
    const canvas = els.plateFw;
    const particles = [];
    const bursts = [];
    const golds = ["#f0d78c", "#d4af37", "#fff4c8", "#c9a535", "#ffe9a0", "#fff", "#e8c15a"];
    const start = performance.now();
    let lastBurst = 0;

    function spawnBurst() {
      const cx = canvas.width * (0.2 + Math.random() * 0.6);
      const cy = canvas.height * (0.15 + Math.random() * 0.45);
      const count = REDUCE_MOTION ? 16 : 36;
      for (let i = 0; i < count; i += 1) {
        const angle = (Math.PI * 2 * i) / count + Math.random() * 0.15;
        const speed = 1.6 + Math.random() * 4.2;
        particles.push({
          x: cx,
          y: cy,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 1,
          color: golds[Math.floor(Math.random() * golds.length)],
          size: 1.4 + Math.random() * 2.4,
        });
      }
      bursts.push({ x: cx, y: cy, r: 0, life: 1 });
    }

    function frame(now) {
      const elapsed = now - start;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (elapsed - lastBurst > (REDUCE_MOTION ? 480 : 300) && elapsed < durationMs - 700) {
        spawnBurst();
        lastBurst = elapsed;
      }
      bursts.forEach((b) => {
        b.r += 3.5;
        b.life -= 0.035;
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(240, 215, 140, ${Math.max(0, b.life) * 0.4})`;
        ctx.lineWidth = 2;
        ctx.stroke();
      });
      for (let i = bursts.length - 1; i >= 0; i -= 1) {
        if (bursts[i].life <= 0) bursts.splice(i, 1);
      }
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.035;
        p.vx *= 0.99;
        p.life -= 0.011;
        ctx.globalAlpha = Math.max(0, p.life);
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      });
      for (let i = particles.length - 1; i >= 0; i -= 1) {
        if (particles[i].life <= 0) particles.splice(i, 1);
      }
      ctx.globalAlpha = 1;
      if (elapsed < durationMs) {
        plateFwRaf = requestAnimationFrame(frame);
      } else {
        stopPlateFireworks();
      }
    }

    stopPlateFireworks();
    spawnBurst();
    plateFwRaf = requestAnimationFrame(frame);
  }

  function handleNewStyleEvents() {
    const next = events();
    const prev = lastEvents || {};
    if (M1_PREVIEW) {
      lastEvents = Object.assign({}, next);
      return;
    }

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

    const pointBump = Math.max(
      Number(next.char_point_event_id) || 0,
      Number(next.kandura_event_id) || 0,
    );
    const prevPoint = Math.max(
      Number(prev.char_point_event_id) || 0,
      Number(prev.kandura_event_id) || 0,
    );
    if (pointBump > prevPoint) {
      playCharacter("point");
    }
    if ((Number(next.char_yellow_event_id) || 0) > (Number(prev.char_yellow_event_id) || 0)) {
      playCharacter("yellow", { yellowRim: true });
    }
    if ((Number(next.char_red_event_id) || 0) > (Number(prev.char_red_event_id) || 0)) {
      playCharacter("red", { redFx: true });
    }
    if ((Number(next.char_sold_stamp_event_id) || 0) > (Number(prev.char_sold_stamp_event_id) || 0)) {
      // If sold_event_id already drove plate-local stamp/FW this tick, only play character video.
      const soldAlsoBumped = (Number(state.sold_event_id) || 0) >= lastSoldEventId && soldRunning;
      playCharacter("sold_stamp", { soldStamp: !soldAlsoBumped });
    }

    lastEvents = Object.assign({}, next);
  }

  function renderAll() {
    syncClockOffset();
    syncSpinner();
    renderBackground();
    syncBgPlatesPrefs();
    renderCurrentPlate();
    renderTimer();
    renderPrice();
    renderAlert();
    renderEventTitle();
    renderTicker();
    renderLogo();
    renderWatermarks();
    applyAgingVisual(computeAgingProgress());
    if (M1_PREVIEW) {
      applyNumberVisibility(false);
      if (els.bgPlates && els.bgPlates.children.length) {
        els.bgPlates.innerHTML = "";
        bgSprites = [];
        bgBuilt = false;
      }
    }
  }

  function handleSoldEvent() {
    if (M1_PREVIEW) {
      lastSoldEventId = Number(state.sold_event_id) || lastSoldEventId;
      return;
    }
    const soldEventId = Number(state.sold_event_id) || 0;
    if (!soldEventId || soldEventId <= lastSoldEventId) return;
    lastSoldEventId = soldEventId;
    // Plate-local SOLD is primary for New Style V3 (no large banner).
    window.triggerSoldCelebration({
      plateType: state.plate_type,
      code: state.code,
      number: state.number,
      phoneNumber: state.phone_number,
      price: state.price,
      style: state.sold_style,
      name: state.sold_name,
      plateLocal: true,
    });
  }

  async function pollState() {
    // #region agent log
    const _pollStarted = Date.now();
    // #endregion
    try {
      const res = await fetch(`${API_URL}?token=${encodeURIComponent(TOKEN)}`, {
        headers: { Accept: "application/json" },
      });
      if (!res.ok) return;
      state = await res.json();
      // #region agent log
      (function () {
        const endMs = state.timer_ends_at ? Date.parse(state.timer_ends_at) : NaN;
        const localFromEnds = Number.isFinite(endMs)
          ? Math.max(0, Math.floor((endMs - (Date.now() + clockOffsetMs)) / 1000))
          : null;
        fetch('http://127.0.0.1:7650/ingest/6effd724-0433-4a9b-be69-34787675ecdc',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ddcc38'},body:JSON.stringify({sessionId:'ddcc38',runId:'pre-fix',hypothesisId:'C',location:'live-display-new.js:pollState',message:'poll completed',data:{pollMs:Date.now()-_pollStarted,timerActive:!!state.timer_active,remaining:state.timer_remaining_seconds,localFromEndsAt:localFromEnds,serverNow:state.server_now||null,timerEndsAt:state.timer_ends_at||null,hasLocalTick:false},timestamp:Date.now()})}).catch(()=>{});
      })();
      // #endregion
      renderAll();
      handleSoldEvent();
      handleNewStyleEvents();
    } catch (err) {
      console.warn("Live display poll failed", err);
      // #region agent log
      fetch('http://127.0.0.1:7650/ingest/6effd724-0433-4a9b-be69-34787675ecdc',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ddcc38'},body:JSON.stringify({sessionId:'ddcc38',runId:'pre-fix',hypothesisId:'C',location:'live-display-new.js:pollState',message:'poll failed',data:{pollMs:Date.now()-_pollStarted,error:String(err&&err.message||err)},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
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
    if (style === "gavel") return "fireworks";
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
    if (M1_PREVIEW) return;
    if (soldRunning) {
      clearTimeout(soldTimer);
      stopFireworks();
      stopPlateFireworks();
      els.soldOverlay?.classList.remove("visible", "sold-style-gavel", "sold-style-confetti", "sold-style-fireworks");
      void els.soldOverlay?.offsetWidth;
    }

    soldRunning = true;
    const style = normalizeSoldStyle(details.style || details.sold_style || state.sold_style);
    const plateLocal = details.plateLocal !== false;

    if (plateLocal) {
      // Primary V3 path: imprint + gold fireworks behind plate; keep timer/bid intact.
      showSoldStampImprint();
      playPlateFireworks(style === "confetti" ? 3800 : 4800);
      if (style === "confetti") makeConfetti();
      // Keep legacy overlay hidden.
      els.soldOverlay?.classList.remove("visible");
      els.soldOverlay?.setAttribute("aria-hidden", "true");
      soldTimer = setTimeout(() => {
        hideSoldStampImprint();
        stopPlateFireworks();
        if (els.confetti) els.confetti.innerHTML = "";
        soldRunning = false;
      }, style === "confetti" ? 4200 : 5200);
      return;
    }

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

  if (els.soldStamp && SOLD_STAMP_URL) {
    els.soldStamp.src = SOLD_STAMP_URL;
  }

  lastEvents = Object.assign({}, events());
  ensureAssetsProbed().finally(() => {
    renderAll();
    if (!M1_PREVIEW) {
      startAgingLoop();
      startBgPlatesLoop();
    } else {
      // Seed lastSold so live sold events never fire after leaving preview mid-session poll.
      lastSoldEventId = Number(state.sold_event_id) || 0;
      applyAgingVisual(0);
      if (els.bgPlates) {
        els.bgPlates.innerHTML = "";
      }
      els.plateStage?.classList.remove("nld-yellow-card", "nld-red-card", "nld-local-shake");
      els.soldStamp?.classList.remove("imprint");
      if (els.soldStamp) els.soldStamp.hidden = true;
    }
    setInterval(pollState, 1000);
    // #region agent log
    // Sample between polls: compare painted text vs ends_at wall clock (proves lag without local tick).
    let _dbgLastPainted = null;
    let _dbgSampleCount = 0;
    setInterval(() => {
      if (!state || !state.timer_active || !state.timer_ends_at) return;
      _dbgSampleCount += 1;
      if (_dbgSampleCount % 2 !== 0) return; // ~400ms effective after every other 200ms tick
      const endMs = Date.parse(state.timer_ends_at);
      if (!Number.isFinite(endMs)) return;
      const localFromEnds = Math.max(0, Math.floor((endMs - nowMs()) / 1000));
      const painted = els.timer ? els.timer.textContent : null;
      const stateRem = Math.max(0, Number(state.timer_remaining_seconds) || 0);
      if (painted === _dbgLastPainted && stateRem === localFromEnds) return;
      const changed = painted !== _dbgLastPainted;
      _dbgLastPainted = painted;
      fetch('http://127.0.0.1:7650/ingest/6effd724-0433-4a9b-be69-34787675ecdc',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ddcc38'},body:JSON.stringify({sessionId:'ddcc38',runId:'pre-fix',hypothesisId:'A',location:'live-display-new.js:lagSampler',message:'between-poll sample',data:{painted:painted,paintedChanged:changed,stateRemaining:stateRem,localFromEndsAt:localFromEnds,lagSeconds:stateRem-localFromEnds,agingRaf:!!agingRaf,bgPlatesRaf:!!bgPlatesRaf},timestamp:Date.now()})}).catch(()=>{});
    }, 200);
    // #endregion
  });
})();
