/**
 * H2 Live V4 — stage-local geometry helpers.
 * Converts viewport getBoundingClientRect() into unscaled #stage CSS pixels
 * even when an ancestor applies transform: scale(...).
 */
(function (global) {
  function stageEl() {
    return document.getElementById("stage");
  }

  /** Visual scale factor: rendered width / layout width (1920). */
  function getStageScale() {
    const stage = stageEl();
    if (!stage) return 1;
    const layoutW = stage.offsetWidth || 1920;
    const visualW = stage.getBoundingClientRect().width;
    if (!layoutW || !visualW) return 1;
    return visualW / layoutW;
  }

  /**
   * Map a DOMRect (viewport) to stage-local CSS px { x, y, w, h }.
   */
  function viewportRectToStage(rect) {
    const stage = stageEl();
    if (!stage || !rect) return { x: 0, y: 0, w: 0, h: 0 };
    const sr = stage.getBoundingClientRect();
    const s = getStageScale() || 1;
    return {
      x: (rect.left - sr.left) / s,
      y: (rect.top - sr.top) / s,
      w: rect.width / s,
      h: rect.height / s,
    };
  }

  function elementStageBox(el) {
    if (!el) return null;
    return viewportRectToStage(el.getBoundingClientRect());
  }

  /** Unscaled content size for canvases (ignores CSS transform scale). */
  function layoutSize(el) {
    if (!el) return { w: 1, h: 1 };
    return {
      w: Math.max(1, Math.round(el.clientWidth || el.offsetWidth || 1)),
      h: Math.max(1, Math.round(el.clientHeight || el.offsetHeight || 1)),
    };
  }

  /**
   * Compare two stage boxes; return max abs error on x/y/w/h in px.
   */
  function boxError(a, b) {
    if (!a || !b) return Infinity;
    return Math.max(
      Math.abs(a.x - b.x),
      Math.abs(a.y - b.y),
      Math.abs(a.w - b.w),
      Math.abs(a.h - b.h),
    );
  }

  global.H2V4Geom = {
    getStageScale,
    viewportRectToStage,
    elementStageBox,
    layoutSize,
    boxError,
  };
})(window);
