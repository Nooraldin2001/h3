/**
 * H2 Live V4 — plate type registry + renderer.
 * Overlay boxes ported from New Style live-display-new.css (% of shell),
 * remapped after lossless padding trim on Sharjah / Dubai Yellow.
 * Phone maps use Classic RGBA frames (du.png / etisalat.png).
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
    du: "./assets/plates/du.png",
    etisalat: "./assets/plates/etisalat.png",
  };

  /** Native art aspect (width/height) from measured trimmed V4 assets. */
  const PLATE_ASPECT = {
    abudhabi: 4.86,
    dubai: 4.764,
    dubai_yellow: 4.395,
    rasalkhimma: 4.72,
    fujairah: 4.7,
    ajman: 5.033,
    ummalquain: 5.063,
    sharjah: 4.616,
    du: 4.382,
    etisalat: 3.725,
  };

  const PHONE_TYPES = new Set(["du", "etisalat"]);

  /**
   * Geometry registry: boxes as % of plate-shell (physical artwork bounds).
   * Sharjah / dubai_yellow remapped from New Style after canvas padding trim.
   */
  const GEOMETRY = {
    abudhabi: {
      codeBox: { top: 30, left: 2, width: 12, height: 35, font: 56 },
      numberBox: { top: 25, left: 52, width: 42, height: 45, font: 72 },
    },
    dubai: {
      codeBox: { top: 48, left: 9, width: 12, height: 34, font: 56 },
      numberBox: { top: 30, left: 38, width: 52, height: 42, font: 84 },
    },
    dubai_yellow: {
      /* Sit in yellow panel number well; keep above CLASSIC watermark */
      codeBox: { top: 48, left: 6.5, width: 12.3, height: 28, font: 48 },
      numberBox: { top: 30.6, left: 37.3, width: 53.4, height: 42.6, font: 80 },
    },
    rasalkhimma: {
      codeBox: { top: 33, left: 32, width: 14, height: 35, font: 64 },
      numberBox: { top: 25, left: 52, width: 44, height: 45, font: 72 },
    },
    fujairah: {
      codeBox: { top: 20, left: 3, width: 12, height: 38, font: 64 },
      numberBox: { top: 23, left: 45, width: 48, height: 45, font: 72 },
    },
    ajman: {
      codeBox: { top: 38, left: 7, width: 10, height: 24, font: 48 },
      numberBox: { top: 32, left: 24, width: 38, height: 36, font: 64 },
    },
    ummalquain: {
      codeBox: { top: 35, left: 3, width: 14, height: 35, font: 64 },
      numberBox: { top: 25, left: 48, width: 48, height: 45, font: 72 },
    },
    sharjah: {
      codeBox: { top: 16.3, left: 18.5, width: 10.6, height: 54.9, font: 64 },
      numberBox: { top: 31.5, left: 60.9, width: 36.0, height: 27.5, font: 72 },
    },
    du: {
      phoneBox: { top: 14, left: 3.5, width: 70, height: 72, font: 56 },
    },
    etisalat: {
      phoneBox: { top: 14, left: 3.5, width: 70, height: 72, font: 56 },
    },
  };

  function classNameFor(type) {
    return type === "dubai_yellow" ? "dubai-yellow" : type;
  }

  function isPhone(type) {
    return PHONE_TYPES.has(type);
  }

  /** Scale glyph size by character count so short/long regs fill the box. */
  function scaledFont(baseFont, text) {
    const len = String(text || "").replace(/\s+/g, "").length;
    let scale = 1;
    if (len <= 1) scale = 1.12;
    else if (len === 2) scale = 1.06;
    else if (len === 3) scale = 1.0;
    else if (len === 4) scale = 0.94;
    else if (len === 5) scale = 0.84;
    else if (len === 6) scale = 0.76;
    else if (len === 7) scale = 0.68;
    else scale = 0.6;
    return Math.max(18, Math.round((baseFont || 64) * scale));
  }

  function applyBox(el, box, text) {
    if (!el || !box) return;
    el.style.top = `${box.top}%`;
    el.style.left = `${box.left}%`;
    el.style.width = `${box.width}%`;
    el.style.height = `${box.height}%`;
    if (box.font) {
      el.style.fontSize = `${scaledFont(box.font, text != null ? text : el.textContent)}px`;
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
      const codeText = phoneMode ? "" : state.code || "";
      code.textContent = codeText;
      applyBox(code, geo.codeBox, codeText);
    }
    if (number) {
      number.hidden = phoneMode;
      const numberText = phoneMode ? "" : state.number || "";
      number.textContent = numberText;
      applyBox(number, geo.numberBox, numberText);
    }
    if (phone) {
      phone.hidden = !phoneMode;
      const phoneText = phoneMode ? state.phone_number || "" : "";
      phone.textContent = phoneText;
      applyBox(phone, geo.phoneBox, phoneText);
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
    scaledFont,
  };
})(window);
