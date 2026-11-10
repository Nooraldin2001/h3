/**
 * H2 Live V4 — plate type registry + renderer.
 * Overlay boxes ported from New Style live-display-new.css (% of shell).
 * Phone maps use real .jpeg frames (not Dubai-collision PNGs).
 */
(function (global) {
  const PLATE_IMAGES = {
    abudhabi: "./assets/plates/abudhabi.jpg",
    dubai: "./assets/plates/dubai.jpg",
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
    dubai: 4.729,
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
      codeBox: { top: 28, left: 2, width: 12, height: 40, font: 58 },
      numberBox: { top: 24, left: 52, width: 42, height: 48, font: 78 },
    },
    dubai: {
      codeBox: { top: 48, left: 9, width: 12, height: 34, font: 54 },
      numberBox: { top: 28, left: 38, width: 52, height: 46, font: 90 },
    },
    dubai_yellow: {
      codeBox: { top: 50, left: 8, width: 12, height: 38, font: 50 },
      numberBox: { top: 28, left: 38, width: 52, height: 44, font: 86 },
    },
    rasalkhimma: {
      codeBox: { top: 33, left: 32, width: 14, height: 35, font: 60 },
      numberBox: { top: 24, left: 52, width: 44, height: 48, font: 78 },
    },
    fujairah: {
      codeBox: { top: 20, left: 3, width: 12, height: 38, font: 60 },
      numberBox: { top: 22, left: 45, width: 48, height: 48, font: 78 },
    },
    ajman: {
      codeBox: { top: 38, left: 7, width: 10, height: 24, font: 46 },
      numberBox: { top: 30, left: 24, width: 38, height: 40, font: 70 },
    },
    ummalquain: {
      codeBox: { top: 35, left: 3, width: 14, height: 35, font: 60 },
      numberBox: { top: 24, left: 48, width: 48, height: 48, font: 78 },
    },
    sharjah: {
      codeBox: { top: 25, left: 20, width: 10, height: 40, font: 58 },
      numberBox: { top: 34, left: 58, width: 36, height: 28, font: 62 },
    },
    du: {
      phoneBox: { top: 14, left: 3.5, width: 70, height: 72, font: 58 },
    },
    etisalat: {
      phoneBox: { top: 14, left: 3.5, width: 70, height: 72, font: 58 },
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
      if (len <= 1) scale = 1.06;
      else if (len === 2) scale = 1;
      else if (len === 3) scale = 0.88;
      else scale = Math.max(0.7, 1.05 - len * 0.1);
    } else {
      // registration number
      if (len <= 1) scale = 1.12;
      else if (len === 2) scale = 1.04;
      else if (len === 3) scale = 1;
      else if (len === 4) scale = 0.94;
      else if (len === 5) scale = 0.8;
      else scale = Math.max(0.64, 0.94 - (len - 4) * 0.08);
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

  function getGeometry(type) {
    return GEOMETRY[type] || GEOMETRY.dubai;
  }

  function getPrimaryContentBox(type) {
    const g = getGeometry(type);
    if (isPhone(type)) return g.phoneBox;
    return g.numberBox;
  }

  function getStampTarget(type) {
    const box = getPrimaryContentBox(type);
    if (!box) return { x: 0.5, y: 0.5 };
    return {
      x: (box.left + box.width / 2) / 100,
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
      number.textContent = phoneMode ? "" : (state.number || "");
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
