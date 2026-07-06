/**
 * Render a plate with code/number overlays into a container.
 * @param {Object} opts
 * @param {string} opts.plateType - slug: abudhabi, dubai, etc.
 * @param {string} opts.code
 * @param {string} opts.number
 * @param {string} opts.imageBaseUrl - static base path e.g. /static/plates/live/
 * @param {HTMLElement} opts.container
 */
function renderLivePlate({ plateType, code, number, imageBaseUrl, container }) {
  if (!container) return;

  const imageMap = {
    abudhabi: "abudhabi.jpeg",
    dubai: "dubai.jpeg",
    dubai_yellow: "dubai_yellow.jpeg",
    sharjah: "sharjah.jpeg",
    ajman: "ajman.jpeg",
    rasalkhimma: "rasalkhimma.jpeg",
    ummalquain: "ummalquain.jpeg",
    fujairah: "fujairah.jpeg",
  };

  const emirateClass = "emirate-" + (plateType || "abudhabi").replace(/_/g, "-");
  const fileName = imageMap[plateType] || imageMap.abudhabi;

  container.innerHTML = "";

  const slide = document.createElement("div");
  slide.className = "live-plate-slide " + emirateClass;

  const img = document.createElement("img");
  img.className = "live-plate-image";
  img.alt = "Plate";
  img.src = imageBaseUrl + fileName;
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
