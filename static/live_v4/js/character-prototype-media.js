/**
 * H2 Live V4 — temporary 2D character media adapter.
 *
 * Uses static transparent PNGs under assets/character/prototype_2d/.
 * Cue times are status:"estimated" only — never "measured".
 * Future production WebMs can replace `sprite` / add `webm` without changing the controller API.
 */
(function (global) {
  const ROOT = "./assets/character/prototype_2d";

  /**
   * Shared display scale for all temporary 2D poses (Point / Yellow / Red).
   * 1.0 = prior baseline (300×430). Aspect ratio preserved via object-fit:contain.
   */
  const CHARACTER_SCALE = 1.3;
  const BASE_DISPLAY = { w: 300, h: 430 };

  /**
   * Stage-space anchors (1920×1080 CSS px). Feet = bottom-center of sprite box.
   * stopFeet lowered with scale so head stays under the bid row (no logo/timer/plate/bid cover).
   */
  const ANCHORS = {
    stage: { w: 1920, h: 1080 },
    entryFeet: { x: 960, y: 1450 },
    // ~+30% on-screen presence; character stays under stack (z) so plate/bid/timer stay readable
    stopFeet: { x: 960, y: 1105 },
    exitFeet: { x: 960, y: 1470 },
    gestureTarget: { x: 960, y: 520 },
    display: {
      w: Math.round(BASE_DISPLAY.w * CHARACTER_SCALE),
      h: Math.round(BASE_DISPLAY.h * CHARACTER_SCALE),
    },
    characterScale: CHARACTER_SCALE,
  };

  const TIMING = {
    enter_ms: 650,
    hold_ms: 1500,
    exit_ms: 500,
  };

  const CATALOG = {
    point: {
      action: "point",
      tier: "prototype_2d",
      quality: "static_png_rgba",
      usableAlpha: true,
      mode: "static_2d",
      perspectiveNote: "Temporary 2D slide — not a production walk",
      sprite: `${ROOT}/point.png`,
      frames: null,
      gif: null,
      webm: null,
      webmUsableAlpha: false,
      fps: 1,
      duration_ms: TIMING.hold_ms,
      enter_ms: TIMING.enter_ms,
      exit_ms: TIMING.exit_ms,
      status: "estimated",
      cues: { gesture_ms: 200, contact_ms: null, release_ms: 1100 },
    },
    yellow: {
      action: "yellow",
      tier: "prototype_2d",
      quality: "static_png_rgba",
      usableAlpha: true,
      mode: "static_2d",
      perspectiveNote: "Temporary 2D yellow-card hold — not production footage",
      sprite: `${ROOT}/yellow.png`,
      frames: null,
      gif: null,
      webm: null,
      webmUsableAlpha: false,
      fps: 1,
      duration_ms: TIMING.hold_ms,
      enter_ms: TIMING.enter_ms,
      exit_ms: TIMING.exit_ms,
      status: "estimated",
      cues: { gesture_ms: 280, contact_ms: null, release_ms: 1200 },
    },
    red: {
      action: "red",
      tier: "prototype_2d",
      quality: "static_png_rgba",
      usableAlpha: true,
      mode: "static_2d",
      perspectiveNote: "Temporary 2D red-card hold; framing differs from point/yellow source",
      sprite: `${ROOT}/red.png`,
      frames: null,
      gif: null,
      webm: null,
      webmUsableAlpha: false,
      fps: 1,
      duration_ms: TIMING.hold_ms,
      enter_ms: TIMING.enter_ms,
      exit_ms: TIMING.exit_ms,
      status: "estimated",
      cues: { gesture_ms: 280, contact_ms: null, release_ms: 1200 },
    },
    // Kept for API compatibility; 2D flow does not play separate enter/exit clips
    enter: {
      action: "enter",
      tier: "prototype_2d",
      quality: "static_png_rgba",
      usableAlpha: true,
      mode: "static_2d",
      sprite: `${ROOT}/point.png`,
      frames: null,
      duration_ms: TIMING.enter_ms,
      enter_ms: TIMING.enter_ms,
      status: "estimated",
      cues: { gesture_ms: null, contact_ms: null, release_ms: null },
    },
    exit: {
      action: "exit",
      tier: "prototype_2d",
      quality: "static_png_rgba",
      usableAlpha: true,
      mode: "static_2d",
      sprite: null,
      frames: null,
      duration_ms: TIMING.exit_ms,
      exit_ms: TIMING.exit_ms,
      status: "estimated",
      cues: { gesture_ms: null, contact_ms: null, release_ms: null },
    },
    sold_stamp: {
      action: "sold_stamp",
      tier: "prototype_2d",
      quality: "missing_standalone_sprite",
      usableAlpha: false,
      mode: "static_2d",
      perspectiveNote: "No dedicated 2D sold-stamp sprite in this temporary pack",
      sprite: null,
      frames: null,
      gif: null,
      webm: null,
      duration_ms: TIMING.hold_ms,
      enter_ms: TIMING.enter_ms,
      exit_ms: TIMING.exit_ms,
      status: "estimated",
      cues: { gesture_ms: null, contact_ms: 400, release_ms: 1100 },
      missing: true,
    },
  };

  function get(action) {
    return CATALOG[action] || null;
  }

  function list() {
    return Object.keys(CATALOG);
  }

  global.H2V4CharacterPrototypeMedia = {
    PREVIEW_ROOT: ROOT,
    ANCHORS,
    TIMING,
    CHARACTER_SCALE,
    BASE_DISPLAY,
    CATALOG,
    get,
    list,
    ASSET_TIER: "prototype_2d_temporary",
    MEASURED: false,
  };
})(window);
