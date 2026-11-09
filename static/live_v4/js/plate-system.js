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
      codeBox: { top: 30, left: 2, width: 12, height: 35, font: 56 },
      numberBox: { top: 25, left: 52, width: 42, height: 45, font: 72 },
    },
    dubai: {
      codeBox: { top: 48, left: 9, width: 12, height: 34, font: 56 },
      numberBox: { top: 30, left: 38, width: 52, height: 42, font: 84 },
    },
    dubai_yellow: {
      codeBox: { top: 50, left: 8, width: 12, height: 38, font: 52 },
      numberBox: { top: 30, left: 38, width: 52, height: 40, font: 80 },
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
      codeBox: { top: 25, left: 20, width: 10, height: 40, font: 64 },
      numberBox: { top: 36, left: 60, width: 34, height: 20, font: 56 },
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

  function applyBox(el, box) {
    if (!el || !box) return;
    el.style.top = `${box.top}%`;
    el.style.left = `${box.left}%`;
    el.style.width = `${box.width}%`;
    el.style.height = `${box.height}%`;
    if (box.font) el.style.fontSize = `${box.font}px`;
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
      applyBox(code, geo.codeBox);
    }
    if (number) {
      number.hidden = phoneMode;
      number.textContent = phoneMode ? "" : (state.number || "");
      applyBox(number, geo.numberBox);
    }
    if (phone) {
      phone.hidden = !phoneMode;
      phone.textContent = phoneMode ? (state.phone_number || "") : "";
      applyBox(phone, geo.phoneBox);
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
