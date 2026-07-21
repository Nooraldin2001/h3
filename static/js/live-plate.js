/**
 * Render plate with code/number overlays.
 * Positioning/sizing is conditional: CSS in live-plate.css targets .plate-type-{slug}.
 * Changing plate type rebuilds the slide so the correct overlay rules apply.
 */
const LIVE_EMIRATE_PLATE_TYPES = [
  "abudhabi",
  "dubai",
  "dubai_yellow",
  "rasalkhimma",
  "fujairah",
  "ajman",
  "ummalquain",
  "sharjah",
];

const LIVE_PHONE_PLATE_TYPES = ["du", "etisalat"];

const LIVE_PLATE_TYPES = LIVE_EMIRATE_PLATE_TYPES.concat(LIVE_PHONE_PLATE_TYPES);

const LIVE_PLATE_IMAGES = {
  abudhabi: "Abu_Dhabi.jpg",
  dubai: "dubai.jpg",
  dubai_yellow: "dubai_classic.jpg",
  rasalkhimma: "Ras_Alkhima.jpg",
  fujairah: "Al_fujjairah.jpg",
  ajman: "ajman.jpg",
  ummalquain: "om_qaun.jpg",
  sharjah: "sharjah.jpg",
  du: "du.jpeg",
  etisalat: "etisalat.jpeg",
};

function isLivePhonePlateType(plateType) {
  return LIVE_PHONE_PLATE_TYPES.includes(plateType);
}

function renderLivePlate({ plateType, code, number, phoneNumber, imageBaseUrl, container }) {
  if (!container) return;

  const type = LIVE_PLATE_TYPES.includes(plateType) ? plateType : "abudhabi";
  const fileName = LIVE_PLATE_IMAGES[type] || LIVE_PLATE_IMAGES.abudhabi;
  const version = window.PLATE_IMAGE_VERSION || "1";
  const isPhone = isLivePhonePlateType(type);
  const renderKey = [type, fileName, imageBaseUrl, version, isPhone ? "phone" : "plate"].join("|");

  if (container.dataset.livePlateRenderKey === renderKey) {
    if (isPhone) {
      const phoneEl = container.querySelector(".plate-phone");
      if (phoneEl) phoneEl.textContent = phoneNumber || "";
    } else {
      const codeEl = container.querySelector(".plate-code");
      const numberEl = container.querySelector(".plate-number");
      if (codeEl) codeEl.textContent = code || "";
      if (numberEl) numberEl.textContent = number || "---";
    }
    return;
  }

  container.innerHTML = "";
  container.dataset.livePlateRenderKey = renderKey;

  const slide = document.createElement("div");
  slide.className = `plate-slide plate-type-${type} active`;
  slide.dataset.plateType = type;

  const canvas = document.createElement("div");
  canvas.className = "plate-canvas";

  const img = document.createElement("img");
  img.className = "plate-image";
  img.alt = isPhone ? "Phone number" : "Plate";
  img.src = imageBaseUrl + fileName + "?v=" + version;
  canvas.appendChild(img);

  if (isPhone) {
    const phoneOverlay = document.createElement("div");
    phoneOverlay.className = "plate-text-overlay plate-phone-overlay";
    const phoneEl = document.createElement("div");
    phoneEl.className = "plate-phone";
    phoneEl.textContent = phoneNumber || "";
    phoneOverlay.appendChild(phoneEl);
    canvas.appendChild(phoneOverlay);
  } else {
    const codeOverlay = document.createElement("div");
    codeOverlay.className = "plate-text-overlay plate-code-overlay";
    const codeEl = document.createElement("div");
    codeEl.className = "plate-code";
    codeEl.textContent = code || "";
    codeOverlay.appendChild(codeEl);
    canvas.appendChild(codeOverlay);

    const numberOverlay = document.createElement("div");
    numberOverlay.className = "plate-text-overlay plate-number-overlay";
    const numberEl = document.createElement("div");
    numberEl.className = "plate-number";
    numberEl.textContent = number || "---";
    numberOverlay.appendChild(numberEl);
    canvas.appendChild(numberOverlay);
  }

  slide.appendChild(canvas);
  container.appendChild(slide);
}

function formatLivePrice(value) {
  if (value === null || value === undefined || value === "") return "0";
  const cleaned = String(value).replace(/[^\d.]/g, "");
  if (!cleaned) return "0";
  const num = Math.floor(parseFloat(cleaned));
  if (isNaN(num)) return "0";
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function formatTimer(seconds) {
  const s = Math.max(0, Math.floor(seconds || 0));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return String(m).padStart(2, "0") + ":" + String(r).padStart(2, "0");
}

function isLivePlateEmpty(code, number, plateType, phoneNumber) {
  if (isLivePhonePlateType(plateType)) {
    return !String(phoneNumber || "").trim();
  }
  return !String(code || "").trim() && !String(number || "").trim();
}

function getLiveDisplayPlateType(plateType, code, number, spinnerIndex, phoneNumber) {
  if (isLivePhonePlateType(plateType)) {
    return plateType;
  }
  if (isLivePlateEmpty(code, number, plateType, phoneNumber)) {
    const idx =
      ((spinnerIndex % LIVE_EMIRATE_PLATE_TYPES.length) + LIVE_EMIRATE_PLATE_TYPES.length) %
      LIVE_EMIRATE_PLATE_TYPES.length;
    return LIVE_EMIRATE_PLATE_TYPES[idx];
  }
  return LIVE_PLATE_TYPES.includes(plateType) ? plateType : "abudhabi";
}

function createLivePlateSpinner(onTick, intervalMs) {
  let timer = null;
  const ms = intervalMs || 2000;

  return {
    start() {
      if (timer) return;
      timer = setInterval(onTick, ms);
    },
    stop() {
      if (!timer) return;
      clearInterval(timer);
      timer = null;
    },
    isRunning() {
      return timer !== null;
    },
  };
}
