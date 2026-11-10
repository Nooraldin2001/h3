/**
 * H2 Live V4 — temporary display flags (Django + sandbox).
 *
 * Restore the main auction plate later by setting:
 *   SHOW_MAIN_PLATE = true
 * then hard-reload the broadcast page.
 *
 * Optional URL override for local QA only:
 *   ?show_plate=1  → force plate visible
 *   ?show_plate=0  → force plate hidden
 *
 * Active Django display loads this via templates/plates/live_display_v4.html
 * (static/live_v4/js/display-config.js) — NOT the sandbox h2_live_v4/ tree alone.
 */
(function (global) {
  const params = new URLSearchParams(location.search);
  const urlOverride = params.get("show_plate");

  /** @type {boolean} Set false to hide the main plate while refining the studio. */
  let SHOW_MAIN_PLATE = false;

  if (urlOverride === "1" || urlOverride === "true") SHOW_MAIN_PLATE = true;
  if (urlOverride === "0" || urlOverride === "false") SHOW_MAIN_PLATE = false;

  function plateRoots() {
    // Prefer independent layer (sandbox refactor); fall back to #plate (Django template).
    const layer = document.getElementById("layer-main-plate");
    if (layer) return [layer];
    const plate = document.getElementById("plate");
    return plate ? [plate] : [];
  }

  function applyMainPlateVisibility() {
    const show = !!SHOW_MAIN_PLATE;
    plateRoots().forEach((el) => {
      el.classList.toggle("is-main-plate-hidden", !show);
      el.classList.toggle("is-hidden", !show);
      el.setAttribute("aria-hidden", show ? "false" : "true");
      el.hidden = !show;
      // Inline styles beat any late CSS that might re-show the plate
      if (!show) {
        el.style.setProperty("display", "none", "important");
        el.style.setProperty("visibility", "hidden", "important");
        el.style.setProperty("opacity", "0", "important");
        el.style.setProperty("pointer-events", "none", "important");
      } else {
        el.style.removeProperty("display");
        el.style.removeProperty("visibility");
        el.style.removeProperty("opacity");
        el.style.removeProperty("pointer-events");
      }
    });
    const slot = document.getElementById("plate-slot");
    if (slot) slot.setAttribute("data-plate-visible", show ? "1" : "0");
  }

  function setShowMainPlate(value) {
    SHOW_MAIN_PLATE = !!value;
    applyMainPlateVisibility();
  }

  // Re-assert after any late paint / FX that might touch the plate node
  function watch() {
    applyMainPlateVisibility();
    const roots = plateRoots();
    if (!roots.length || SHOW_MAIN_PLATE) return;
    const obs = new MutationObserver(() => {
      if (!SHOW_MAIN_PLATE) applyMainPlateVisibility();
    });
    roots.forEach((el) => {
      obs.observe(el, { attributes: true, attributeFilter: ["style", "class", "hidden"] });
    });
    // Also watch parent in case nodes are replaced
    const stage = document.getElementById("stage");
    if (stage) {
      obs.observe(stage, { childList: true, subtree: true });
    }
  }

  global.H2V4DisplayConfig = {
    get SHOW_MAIN_PLATE() {
      return SHOW_MAIN_PLATE;
    },
    setShowMainPlate,
    applyMainPlateVisibility,
    watch,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      applyMainPlateVisibility();
    });
  } else {
    applyMainPlateVisibility();
  }
})(window);
