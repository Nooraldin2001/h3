/**
 * Render plate with code/number overlays — same technique as draw_plate.html
 * Each plate type has its own CSS positioning in live-plate.css (.plate-type-*).
 */
const LIVE_PLATE_IMAGES = {
  abudhabi: "Abu_Dhabi.jpg",
  dubai: "dubai.jpg",
  dubai_yellow: "dubai.jpg",
  rasalkhimma: "Ras_Alkhima.jpg",
  fujairah: "Al_fujjairah.jpg",
  ajman: "ajman.jpg",
  ummalquain: "om_qaun.jpg",
  sharjah: "sharjah.jpg",
};

function renderLivePlate({ plateType, code, number, imageBaseUrl, container }) {
  if (!container) return;

  const type = plateType || "abudhabi";
  const fileName = LIVE_PLATE_IMAGES[type] || LIVE_PLATE_IMAGES.abudhabi;

  container.innerHTML = "";

  const slide = document.createElement("div");
  slide.className = `plate-slide plate-type-${type} active`;

  const canvas = document.createElement("div");
  canvas.className = "plate-canvas";

  const img = document.createElement("img");
  img.className = "plate-image";
  img.alt = "Plate";
  img.src = imageBaseUrl + fileName + "?v=" + (window.PLATE_IMAGE_VERSION || "1");
  canvas.appendChild(img);

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
