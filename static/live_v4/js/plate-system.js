/**
 * H2 Live V4 — plate type registry + renderer.
 * Overlay boxes ported from New Style live-display-new.css (% of shell).
 * Phone maps use real .jpeg frames (not Dubai-collision PNGs).
 */
(function (global) {
  const PLATE_IMAGES = {
    abudhabi: "./assets/plates/abudhabi.jpg",
    dubai: "./assets/plates/dubai-main-final.png",
    dubai_yellow: "./assets/plates/dubai_classic.jpg",
    rasalkhimma: "./assets/plates/rasalkhimma.jpg",
    fujairah: "./assets/plates/fujairah.jpg",
    ajman: "./assets/plates/ajman.jpg",
    ummalquain: "./assets/plates/ummalquain.jpg",
    sharjah: "./assets/plates/sharjah.jpg",
    du: "./assets/plates/du.jpeg",
    etisalat: "./assets/plates/etisalat.jpeg",
  };

  /** Native art aspect (width/height) from measured production assets. */
  const PLATE_ASPECT = {
    abudhabi: 4.848,
    dubai: 4.734,
    dubai_yellow: 4.216,
    rasalkhimma: 4.72,
    fujairah: 4.64,
    ajman: 5.023,
    ummalquain: 5.016,
    sharjah: 3.559,
    du: 4.382,
    etisalat: 3.725,
  };

  const PHONE_TYPES = new Set(["du", "etisalat"]);

  /** Geometry registry: boxes as % of plate-shell. */
  const GEOMETRY = {
    abudhabi: {
      codeBox: { top: 28, left: 2, width: 12, height: 40, font: 64 },
      numberBox: { top: 22, left: 51, width: 44, height: 52, font: 88 },
    },
    dubai: {
      // dubai-main-final.png: logo top-left (~5–24% x, ~13–47% y).
      // Code under logo; number in open right field — logo unobstructed.
      codeBox: { top: 50, left: 5.5, width: 17, height: 38, font: 60 },
      numberBox: { top: 18, left: 30, width: 64, height: 62, font: 112 },
    },
    dubai_yellow: {
      codeBox: { top: 48, left: 7.5, width: 13, height: 40, font: 58 },
      numberBox: { top: 24, left: 36, width: 55, height: 50, font: 102 },
    },
    rasalkhimma: {
      codeBox: { top: 32, left: 31, width: 15, height: 36, font: 66 },
      numberBox: { top: 22, left: 51, width: 45, height: 50, font: 88 },
    },
    fujairah: {
      codeBox: { top: 18, left: 2.5, width: 13, height: 40, font: 66 },
      numberBox: { top: 20, left: 44, width: 50, height: 52, font: 88 },
    },
    ajman: {
      codeBox: { top: 36, left: 6.5, width: 11, height: 26, font: 50 },
      numberBox: { top: 28, left: 23, width: 40, height: 44, font: 78 },
    },
    ummalquain: {
      codeBox: { top: 33, left: 2.5, width: 15, height: 38, font: 66 },
      numberBox: { top: 22, left: 47, width: 50, height: 52, font: 88 },
    },
    sharjah: {
      codeBox: { top: 24, left: 19, width: 11, height: 42, font: 64 },
      numberBox: { top: 32, left: 57, width: 38, height: 32, font: 70 },
    },
    du: {
      phoneBox: { top: 12, left: 3, width: 72, height: 76, font: 64 },
    },
    etisalat: {
      phoneBox: { top: 12, left: 3, width: 72, height: 76, font: 64 },
    },
  };

  function classNameFor(type) {
    return type === "dubai_yellow" ? "dubai-yellow" : type;
  }

  function isPhone(type) {
    return PHONE_TYPES.has(type);
  }

  /** Scale overlay font by glyph count so 1–5 digit / phone strings stay inside the box. */
  function fitOverlayFont(el, baseFontPx, kind) {
    if (!el || el.hidden || !baseFontPx) return;
    const text = String(el.textContent || "").replace(/\s+/g, "");
    const len = Math.max(1, text.length);
    let scale = 1;
    if (kind === "phone") {
      if (len <= 9) scale = 1;
      else if (len === 10) scale = 0.92;
      else if (len === 11) scale = 0.84;
      else scale = Math.max(0.68, 0.92 - (len - 10) * 0.06);
    } else if (kind === "code") {
      if (len <= 1) scale = 1.1;
      else if (len === 2) scale = 1.02;
      else if (len === 3) scale = 0.9;
      else scale = Math.max(0.72, 1.06 - len * 0.1);
    } else {
      // registration number — keep 4-digit plates large; shrink only when needed
      if (len <= 1) scale = 1.14;
      else if (len === 2) scale = 1.06;
      else if (len === 3) scale = 1.02;
      else if (len === 4) scale = 0.98;
      else if (len === 5) scale = 0.82;
      else scale = Math.max(0.66, 0.96 - (len - 4) * 0.08);
    }
    el.style.fontSize = `${Math.round(baseFontPx * scale)}px`;
  }

  function applyBox(el, box, kind) {
    if (!el || !box) return;
    el.style.top = `${box.top}%`;
    el.style.left = `${box.left}%`;
    el.style.width = `${box.width}%`;
    el.style.height = `${box.height}%`;
    if (box.font) {
      el.style.fontSize = `${box.font}px`;
      fitOverlayFont(el, box.font, kind || "number");
    }
  }

  /**
   * Build number glyphs. Digit "1" is a flat-top stem (no Oswald top-left flag)
   * at the same font-size / weight as sibling digits.
   */
  function renderNumberGlyphs(el, text) {
    if (!el) return;
    const raw = String(text || "");
    el.textContent = "";
    if (!raw) {
      el.classList.remove("has-glyphs");
      return;
    }
    el.classList.add("has-glyphs");
    Array.from(raw).forEach((ch) => {
      const span = document.createElement("span");
      span.className = ch === "1" ? "plate-num plate-num-1" : "plate-num";
      span.textContent = ch;
      el.appendChild(span);
    });
  }

  function getGeometry(type) {
    return GEOMETRY[type] || GEOMETRY.dubai;
  }

  function getPrimaryContentBox(type) {
    const g = getGeometry(type);
    if (isPhone(type)) return g.phoneBox;
    return g.numberBox;
  }

  /**
   * SOLD imprint anchor as fractions of plate-shell.
   * For 4-digit plates, bias LEFT so the stamp covers ~first two digits
   * and the last two stay readable (matches approved reference).
   */
  function getStampTarget(type, opts) {
    const box = getPrimaryContentBox(type);
    if (!box) return { x: 0.5, y: 0.5 };
    const digits = Math.max(1, Number(opts?.digitCount) || 4);
    let fracX = 0.5;
    if (isPhone(type)) {
      fracX = 0.3;
    } else if (digits >= 5) {
      fracX = 0.22;
    } else if (digits === 4) {
      /* Center over digits 1–2 so stamp right clears digit 3 */
      fracX = 0.22;
    } else if (digits === 3) {
      fracX = 0.28;
    } else if (digits === 2) {
      fracX = 0.34;
    } else {
      fracX = 0.38;
    }
    return {
      x: (box.left + box.width * fracX) / 100,
      y: (box.top + box.height / 2) / 100,
    };
  }

  function renderPlate(state) {
    const type = PLATE_IMAGES[state.plate_type] ? state.plate_type : "dubai";
    const plate = document.getElementById("plate");
    const shell = document.getElementById("plate-shell");
    const art = document.getElementById("plate-art");
    const code = document.getElementById("plate-code");
    const number = document.getElementById("plate-number");
    const phone = document.getElementById("plate-phone");
    if (!plate || !shell || !art) return type;

    const aspect = PLATE_ASPECT[type] || 4.729;
    plate.style.width = "760px";
    plate.style.aspectRatio = `${aspect} / 1`;
    plate.style.setProperty("--plate-aspect", String(aspect));

    const cls = classNameFor(type);
    shell.className = `plate-shell plate-type-${cls}`;
    art.src = PLATE_IMAGES[type];
    art.alt = type;

    const geo = getGeometry(type);
    const phoneMode = isPhone(type);

    if (code) {
      code.hidden = phoneMode;
      code.textContent = phoneMode ? "" : (state.code || "");
      applyBox(code, geo.codeBox, "code");
    }
    if (number) {
      number.hidden = phoneMode;
      if (phoneMode) {
        number.classList.remove("has-glyphs");
        number.textContent = "";
      } else {
        renderNumberGlyphs(number, state.number || "");
      }
      applyBox(number, geo.numberBox, "number");
    }
    if (phone) {
      phone.hidden = !phoneMode;
      phone.textContent = phoneMode ? (state.phone_number || "") : "";
      applyBox(phone, geo.phoneBox, "phone");
    }

    return type;
  }

  function getPlateShellRect() {
    const shell = document.getElementById("plate-shell");
    return shell ? shell.getBoundingClientRect() : null;
  }

  function plateLocalToStage(x01, y01) {
    const shell = document.getElementById("plate-shell");
    const stage = document.getElementById("stage");
    if (!shell || !stage) return { x: 0, y: 0 };
    const sr = shell.getBoundingClientRect();
    const tr = stage.getBoundingClientRect();
    return {
      x: sr.left - tr.left + sr.width * x01,
      y: sr.top - tr.top + sr.height * y01,
    };
  }

  global.H2PlateSystem = {
    PLATE_IMAGES,
    PLATE_ASPECT,
    GEOMETRY,
    PHONE_TYPES,
    isPhone,
    getGeometry,
    getPrimaryContentBox,
    getStampTarget,
    renderPlate,
    getPlateShellRect,
    plateLocalToStage,
    classNameFor,
  };
})(window);
