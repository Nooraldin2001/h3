/**
 * H2 Live V4 — temporary 2D character controller.
 * IDLE → ENTERING → ACTING → EXITING → IDLE
 *
 * Entrance: cinematic perspective approach from studio center-depth
 * (small → grow toward camera). Exit retreats to the same depth point.
 * Side effects use status:"estimated" cues. Compatible with future WebM swap via media adapter.
 */
(function (global) {
  const FX_ACTIONS = ["point", "yellow", "red", "sold_stamp"];

  let state = "IDLE";
  let busy = false;
  let currentAction = null;
  let loadedAsset = null;
  let lastError = "";
  let cueStatus = "none";
  let timers = [];
  let raf = 0;
  let holding = false;
  let listeners = new Set();

  function media() {
    return global.H2V4CharacterPrototypeMedia;
  }

  function anchors() {
    return (
      media()?.ANCHORS || {
        entryFeet: { x: 960, y: 688 },
        entryScale: 0.15,
        stopFeet: { x: 960, y: 1105 },
        stopScale: 1,
        exitFeet: { x: 960, y: 688 },
        exitScale: 0.12,
        display: { w: 360, h: 520 },
        gestureTarget: { x: 960, y: 520 },
      }
    );
  }

  function timing() {
    return media()?.TIMING || { enter_ms: 2800, hold_ms: 1300, exit_ms: 2200 };
  }

  function layer() {
    return document.getElementById("character");
  }

  function spriteEl() {
    return document.getElementById("character-sprite");
  }

  function videoEl() {
    return document.getElementById("character-video");
  }

  function missingEl() {
    return document.getElementById("character-missing");
  }

  function hud() {
    return {
      state,
      action: currentAction,
      loadedAsset,
      tier: loadedAsset?.tier || "none",
      quality: loadedAsset?.quality || "none",
      cueStatus,
      busy,
      holding,
      error: lastError,
      usableAlpha: !!loadedAsset?.usableAlpha,
      perspectiveNote: loadedAsset?.perspectiveNote || "",
      mode: loadedAsset?.mode || "none",
    };
  }

  function emitHud() {
    const snap = hud();
    listeners.forEach((fn) => {
      try {
        fn(snap);
      } catch (e) {
        /* ignore */
      }
    });
    const lyr = layer();
    if (lyr) lyr.dataset.charState = state;
  }

  function clearTimers() {
    timers.forEach(clearTimeout);
    timers = [];
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
  }

  function after(ms, fn) {
    const id = setTimeout(fn, Math.max(0, ms));
    timers.push(id);
    return id;
  }

  /**
   * Place character by feet (bottom-center) with optional perspective scale.
   * transform-origin is feet (50% 100%) so scale grows/shrinks from the floor.
   */
  function placeFeet(feet, scale) {
    const lyr = layer();
    const a = anchors();
    if (!lyr || !feet) return;
    const w = a.display.w;
    const h = a.display.h;
    const s =
      scale != null && Number.isFinite(Number(scale))
        ? Math.max(0.04, Number(scale))
        : Number(lyr.dataset.scale) || 1;
    lyr.style.width = `${w}px`;
    lyr.style.height = `${h}px`;
    lyr.style.left = `${feet.x - w / 2}px`;
    lyr.style.top = `${feet.y - h}px`;
    lyr.style.right = "auto";
    lyr.style.bottom = "auto";
    lyr.style.transformOrigin = "50% 100%";
    lyr.style.transform = Math.abs(s - 1) < 0.001 ? "none" : `scale(${s})`;
    lyr.dataset.feetX = String(feet.x);
    lyr.dataset.feetY = String(feet.y);
    lyr.dataset.scale = String(s);
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  /** Smooth approach — decelerates into final stance. */
  function easeOutQuint(t) {
    return 1 - Math.pow(1 - t, 5);
  }

  /** Scale grows faster as the figure nears the camera (cheap perspective feel). */
  function easeInCubic(t) {
    return t * t * t;
  }

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function showLayer(on) {
    const lyr = layer();
    if (!lyr) return;
    lyr.classList.toggle("playing", !!on);
    lyr.classList.toggle("exiting", false);
    lyr.classList.toggle("approaching", false);
    lyr.setAttribute("aria-hidden", on ? "false" : "true");
    if (!on) {
      lyr.classList.remove("playing", "approaching", "exiting");
      lyr.style.transform = "none";
      lyr.style.opacity = "";
      lyr.dataset.scale = "1";
      const spr = spriteEl();
      if (spr) {
        spr.hidden = true;
        spr.removeAttribute("src");
      }
      const video = videoEl();
      if (video) {
        try {
          video.pause();
        } catch (e) {
          /* ignore */
        }
        video.hidden = true;
        video.removeAttribute("src");
        video.load();
      }
      const miss = missingEl();
      if (miss) {
        miss.hidden = true;
        miss.setAttribute("aria-hidden", "true");
      }
    }
  }

  function setSprite(src) {
    const spr = spriteEl();
    const video = videoEl();
    if (video) video.hidden = true;
    if (!spr) return;
    if (!src) {
      spr.hidden = true;
      return;
    }
    spr.hidden = false;
    spr.style.objectFit = "contain";
    spr.style.objectPosition = "bottom center";
    if (spr.getAttribute("src") !== src) spr.src = src;
  }

  /**
   * Animate feet + perspective scale together.
   * from/to: { x, y, scale }
   */
  function animatePath(from, to, ms, easingFn, onDone, scaleEasingFn) {
    const t0 = performance.now();
    const ease = easingFn || easeOutCubic;
    const scaleEase = scaleEasingFn || ease;
    const fromScale = from.scale != null ? Number(from.scale) : 1;
    const toScale = to.scale != null ? Number(to.scale) : 1;
    function step(now) {
      const t = Math.min(1, (now - t0) / Math.max(1, ms));
      const e = ease(t);
      const es = scaleEase(t);
      placeFeet(
        {
          x: lerp(from.x, to.x, e),
          y: lerp(from.y, to.y, e),
        },
        lerp(fromScale, toScale, es),
      );
      if (t < 1) raf = requestAnimationFrame(step);
      else {
        placeFeet({ x: to.x, y: to.y }, toScale);
        onDone?.();
      }
    }
    raf = requestAnimationFrame(step);
  }

  function fitRim() {
    const plate = document.getElementById("plate");
    const shell = document.getElementById("plate-shell");
    const rim = document.getElementById("plate-rim");
    if (!plate || !shell || !rim) return;
    const pr = plate.getBoundingClientRect();
    const sr = shell.getBoundingClientRect();
    const scale = global.H2V4Geom?.getStageScale?.() || 1;
    const pad = 10;
    rim.style.left = `${(sr.left - pr.left) / scale - pad}px`;
    rim.style.top = `${(sr.top - pr.top) / scale - pad}px`;
    rim.style.width = `${sr.width / scale + pad * 2}px`;
    rim.style.height = `${sr.height / scale + pad * 2}px`;
    rim.style.right = "auto";
    rim.style.bottom = "auto";
    rim.style.inset = "auto";
  }

  function clearFxSoft() {
    global.H2V4BeamDropFx?.setYellow?.(false);
    const rim = document.getElementById("plate-rim");
    if (rim && !rim.classList.contains("red")) {
      rim.classList.remove("yellow");
      rim.setAttribute("aria-hidden", "true");
    } else if (rim) {
      rim.classList.remove("yellow");
    }
    const plate = document.getElementById("plate");
    plate?.classList.remove("yellow-card", "yellow-illuminate", "plate-impact-shake");
    if (plate) {
      plate.style.transform = "";
    }
  }

  function fireYellowCue() {
    // Gesture cue (~280ms into Yellow pose) — after cinematic entrance has finished
    fitRim();
    const plate = document.getElementById("plate");
    if (plate) {
      plate.classList.remove("yellow-card", "yellow-illuminate");
      void plate.offsetWidth;
    }
    global.H2V4BeamDropFx?.setYellow?.(true);
    if (plate) {
      plate.classList.add("yellow-card");
    }
    after(1600, () => {
      global.H2V4BeamDropFx?.setYellow?.(false);
      if (plate) {
        plate.classList.remove("yellow-card", "yellow-illuminate");
        plate.style.transform = "";
      }
    });
  }

  function fireRedCue() {
    fitRim();
    global.H2V4BeamDropFx?.setRed?.(true);
    global.H2V4State?.patch?.({ ns_hide_number: true });
  }

  function fireSoldCue() {
    global.H2V4SoldFx?.triggerSoldLocal?.({
      imprint: true,
      fireworks: true,
      shake: true,
    });
  }

  function finishToIdle() {
    clearTimers();
    showLayer(false);
    clearFxSoft();
    state = "IDLE";
    busy = false;
    holding = false;
    currentAction = null;
    loadedAsset = null;
    cueStatus = "none";
    emitHud();
  }

  function runExit(thenIdle) {
    state = "EXITING";
    emitHud();
    const a = anchors();
    const clip = loadedAsset || media()?.get(currentAction) || media()?.get("exit");
    const exitMs = clip?.exit_ms || timing().exit_ms;
    const lyr = layer();
    const feetNow = {
      x: Number(lyr?.dataset.feetX) || a.stopFeet.x,
      y: Number(lyr?.dataset.feetY) || a.stopFeet.y,
      scale: Number(lyr?.dataset.scale) || a.stopScale || 1,
    };
    const dest = {
      x: a.exitFeet.x,
      y: a.exitFeet.y,
      scale: a.exitScale != null ? a.exitScale : a.entryScale || 0.12,
    };
    lyr?.classList.add("exiting");
    lyr?.classList.remove("approaching");
    // Same easing for feet + scale so the figure retreats along the floor plane
    animatePath(feetNow, dest, exitMs, easeInOutCubic, () => {
      if (thenIdle !== false) finishToIdle();
    }, easeInOutCubic);
  }

  function runEnter(onArrived) {
    state = "ENTERING";
    emitHud();
    const a = anchors();
    const clip = loadedAsset || media()?.get(currentAction) || media()?.get("enter");
    const enterMs = clip?.enter_ms || timing().enter_ms;
    const start = {
      x: a.entryFeet.x,
      y: a.entryFeet.y,
      scale: a.entryScale != null ? a.entryScale : 0.15,
    };
    const end = {
      x: a.stopFeet.x,
      y: a.stopFeet.y,
      scale: a.stopScale != null ? a.stopScale : 1,
    };
    const lyr = layer();
    showLayer(true);
    lyr?.classList.add("approaching");
    lyr?.classList.remove("exiting");
    placeFeet({ x: start.x, y: start.y }, start.scale);
    if (clip?.sprite) setSprite(clip.sprite);
    // Same easing for feet + scale keeps feet grounded on the studio floor plane
    // while perspective size grows (no teleport / scale-only pop at the bottom).
    animatePath(start, end, enterMs, easeInOutCubic, () => {
      lyr?.classList.remove("approaching", "exiting");
      if (lyr) lyr.style.opacity = "1";
      placeFeet({ x: end.x, y: end.y }, end.scale);
      onArrived?.();
    }, easeInOutCubic);
  }

  function runAct(action, extras) {
    state = "ACTING";
    currentAction = action;
    const clip = media()?.get(action);
    loadedAsset = clip;
    cueStatus = clip?.status === "estimated" ? "estimated" : clip?.status || "none";
    emitHud();

    if (clip?.sprite) {
      setSprite(clip.sprite);
    } else if (clip?.frames?.length) {
      setSprite(clip.frames[clip.frames.length - 1]);
    } else if (clip?.gif) {
      setSprite(clip.gif);
    } else {
      lastError = clip?.missing
        ? `Missing standalone 2D sprite for ${action}`
        : `No usable prototype media for ${action}`;
      const miss = missingEl();
      if (miss) {
        miss.hidden = false;
        miss.textContent = lastError;
        miss.setAttribute("aria-hidden", "false");
      }
    }

    const holdMs = clip?.duration_ms || timing().hold_ms;
    const cues = clip?.cues || {};
    const a = anchors();

    if (action === "yellow" && extras.yellowRim !== false) {
      after(cues.gesture_ms ?? 280, fireYellowCue);
    }
    if (action === "red" && extras.redFx !== false) {
      after(cues.gesture_ms ?? 280, fireRedCue);
    }
    if (action === "sold_stamp" && extras.soldStamp !== false) {
      after(cues.contact_ms ?? 400, fireSoldCue);
    }

    after(holdMs, () => {
      if (extras.hold) {
        holding = true;
        state = "IDLE";
        busy = false;
        placeFeet(a.stopFeet, a.stopScale != null ? a.stopScale : 1);
        emitHud();
        return;
      }
      runExit(true);
    });
  }

  function play(action, extras = {}) {
    if (action === "reset") {
      reset();
      return { ok: true, reset: true };
    }
    // Prevent duplicate overlapping entrances on rapid clicks
    if (busy && action !== "exit") {
      return { ok: false, reason: "busy", state };
    }

    const clip = media()?.get(action);
    if (!clip && action !== "exit" && action !== "enter") {
      lastError = `Unknown action ${action}`;
      emitHud();
      return { ok: false, reason: "unknown" };
    }

    busy = true;
    currentAction = action;
    lastError = "";
    clearTimers();

    if (action === "exit") {
      if (state === "IDLE" && !holding) {
        busy = false;
        return { ok: false, reason: "already_idle" };
      }
      loadedAsset = clip || media()?.get("exit");
      runExit(true);
      return { ok: true, incomplete: true, estimated: true };
    }

    if (action === "enter") {
      loadedAsset = clip;
      runEnter(() => {
        holding = true;
        state = "IDLE";
        busy = false;
        const a = anchors();
        placeFeet(a.stopFeet, a.stopScale != null ? a.stopScale : 1);
        emitHud();
      });
      return { ok: true, incomplete: true, estimated: true, tier: "prototype_2d" };
    }

    loadedAsset = clip;
    if (clip?.sprite) setSprite(clip.sprite);

    const startAct = () => runAct(action, extras);
    if (holding && state === "IDLE") {
      // Already on stage — swap pose and act without re-entering
      const a = anchors();
      placeFeet(a.stopFeet, a.stopScale != null ? a.stopScale : 1);
      startAct();
    } else {
      runEnter(startAct);
    }

    return {
      ok: true,
      measured: false,
      estimated: true,
      incomplete: true,
      assetPresent: !!clip?.sprite,
      tier: clip?.tier || "prototype_2d",
      cueStatus: "estimated",
      mode: "static_2d",
    };
  }

  function reset() {
    clearTimers();
    clearFxSoft();
    const rim = document.getElementById("plate-rim");
    rim?.classList.remove("yellow", "red");
    rim?.setAttribute("aria-hidden", "true");
    const plate = document.getElementById("plate");
    plate?.classList.remove("yellow-card", "yellow-illuminate", "plate-impact-shake", "red-card");
    if (plate) plate.style.transform = "";
    showLayer(false);
    state = "IDLE";
    busy = false;
    holding = false;
    currentAction = null;
    loadedAsset = null;
    cueStatus = "none";
    lastError = "";
    emitHud();
  }

  function probeAll() {
    return Promise.resolve(
      FX_ACTIONS.map((a) => {
        const c = media()?.get(a);
        return { action: a, present: !!c?.sprite, tier: c?.tier };
      }),
    );
  }

  function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  }

  function getAnchorsLive() {
    const a = anchors();
    return {
      ...a,
      feetNow: {
        x: Number(layer()?.dataset.feetX) || null,
        y: Number(layer()?.dataset.feetY) || null,
      },
      scaleNow: Number(layer()?.dataset.scale) || null,
      gestureTarget: a.gestureTarget || { x: 960, y: 520 },
    };
  }

  function boot() {
    reset();
    const lyr = layer();
    if (lyr) lyr.dataset.entry = anchors().entryMode || "studio_depth";
  }

  global.H2V4Character = {
    ACTIONS: FX_ACTIONS,
    probeAll,
    play,
    reset,
    boot,
    metaReady: () => false,
    getPresence: () => {
      const o = {};
      FX_ACTIONS.forEach((a) => {
        const c = media()?.get(a);
        o[a] = !!c?.sprite;
      });
      return o;
    },
    getMeta: () => {
      const o = {};
      FX_ACTIONS.forEach((a) => {
        const c = media()?.get(a);
        o[a] = c
          ? { status: c.status, cues: c.cues, duration_ms: c.duration_ms, tier: c.tier, mode: c.mode }
          : { status: "missing" };
      });
      return o;
    },
    getHud: hud,
    subscribe,
    isBusy: () => busy,
    getState: () => state,
    getAnchorsLive,
    fitRim,
    ASSET_STATUS: "prototype_2d_temporary_not_production",
  };
})(window);
