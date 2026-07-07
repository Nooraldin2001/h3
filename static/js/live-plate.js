/**
 * Render plate with code/number overlays — same technique as draw_plate.html
 * Uses emirate-1..7 classes and percentage-based overlay positioning.
 */
const LIVE_PLATE_TYPE_TO_EMIRATE = {
  abudhabi: "1",
  dubai: "2",
  dubai_yellow: "2",
  rasalkhimma: "3",
  fujairah: "4",
  ajman: "5",
  ummalquain: "6",
  sharjah: "7",
};

const LIVE_PLATE_IMAGES = {
  "1": "Abu_Dhabi.jpg",
  "2": "dubai.jpg",
  "3": "Ras_Alkhima.jpg",
  "4": "Al_fujjairah.jpg",
  "5": "ajman.jpg",
  "6": "om_qaun.jpg",
  "7": "sharjah.jpg",
};

function renderLivePlate({ plateType, code, number, imageBaseUrl, container }) {
  if (!container) return;

  const emirate = LIVE_PLATE_TYPE_TO_EMIRATE[plateType] || "1";
  const fileName = LIVE_PLATE_IMAGES[emirate];

  container.innerHTML = "";

  const slide = document.createElement("div");
  slide.className = `plate-slide emirate-${emirate} active`;

  const img = document.createElement("img");
  img.className = "plate-image";
  img.alt = "Plate";
  img.src = imageBaseUrl + fileName + "?v=" + (window.PLATE_IMAGE_VERSION || "1");
  slide.appendChild(img);

  const codeOverlay = document.createElement("div");
  codeOverlay.className = "plate-text-overlay plate-code-overlay";
  const codeEl = document.createElement("div");
  codeEl.className = "plate-code";
  codeEl.textContent = code || "";
  codeOverlay.appendChild(codeEl);
  slide.appendChild(codeOverlay);

  const numberOverlay = document.createElement("div");
  numberOverlay.className = "plate-text-overlay plate-number-overlay";
  const numberEl = document.createElement("div");
  numberEl.className = "plate-number";
  numberEl.textContent = number || "---";
  numberOverlay.appendChild(numberEl);
  slide.appendChild(numberOverlay);

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
