/**
 * H2 Live V4 — deadline-based countdown (Django-authoritative ends_at).
 *
 * Display remaining = ceil((ends_at - nowMs) / 1000) while running so a fresh
 * 60s start shows 01:00 (not 00:59 from Math.floor). Completion when ms <= 0.
 *
 * Do not paint polled timer_remaining_seconds over the live tick.
 * Safari: truncate Django 6-digit microsecond ISO timestamps.
 */
(function (global) {
  const STORAGE_KEY = "h2v4_timer_v1";
  let rafId = 0;
  let intervalId = 0;
  let lastPaintedSecond = null;
  let lastEndsAtMs = NaN;
  let visibilityBound = false;

  function isDjangoMode() {
    return !!(global.H2V4_DJANGO && global.H2V4_DJANGO.stateUrl);
  }

  function state() {
    return global.H2V4State?.getState?.();
  }

  function nowMs() {
    return global.H2V4State?.nowMs?.() || Date.now();
  }

  function clampNonNegInt(sec) {
    return Math.max(0, Math.floor(Number(sec) || 0));
  }

  /** Safari-safe parse of Django isoformat (6-digit micros → millis). */
  function parseServerDate(iso) {
    if (!iso) return NaN;
    let s = String(iso).trim();
    s = s.replace(/\.(\d{3})\d+(?=(Z|[+-]\d{2}:?\d{2})$)/, ".$1");
    let ms = Date.parse(s);
    if (!Number.isFinite(ms)) {
      ms = Date.parse(s.replace(/([+-]\d{2}):(\d{2})$/, "$1$2"));
    }
    return ms;
  }

  /**
   * Authoritative remaining seconds for display.
   * Active deadline → ceil so first frame is N, last non-zero second is 1, then 0.
   */
  function computeRemaining(s) {
    if (!s) return 0;

    if (s.timer_active && s.timer_ends_at) {
      const end = parseServerDate(s.timer_ends_at);
      if (Number.isFinite(end)) {
        const ms = end - nowMs();
        if (ms <= 0) return 0;
        return Math.max(0, Math.ceil(ms / 1000));
      }
    }

    if (s.timer_paused_remaining != null) {
      return clampNonNegInt(s.timer_paused_remaining);
    }

    // Completed: past ends_at still on session, inactive
    if (s.timer_ends_at && !s.timer_active) {
      const end = parseServerDate(s.timer_ends_at);
      if (Number.isFinite(end) && end - nowMs() <= 0) return 0;
    }

    if (s.timer_remaining_seconds != null && s.timer_remaining_seconds !== "") {
      return clampNonNegInt(s.timer_remaining_seconds);
    }
    return clampNonNegInt(s.timer_seconds);
  }

  function timerPayload(s) {
    return {
      timer_seconds: s.timer_seconds,
      timer_remaining_seconds: s.timer_remaining_seconds,
      timer_active: s.timer_active,
      timer_ends_at: s.timer_ends_at || null,
      timer_paused_remaining: s.timer_paused_remaining ?? null,
    };
  }

  function persist() {
    if (isDjangoMode()) return;
    const s = state();
    if (!s) return;
    const payload = timerPayload(s);
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (e) {
      /* ignore */
    }
    try {
      const sharedKey = global.H2V4SyncBus?.TIMER_SHARED_KEY || "h2v4_timer_shared_v1";
      localStorage.setItem(sharedKey, JSON.stringify(payload));
    } catch (e) {
      /* ignore */
    }
    try {
      global.H2V4SyncBus?.saveSnapshot?.();
    } catch (e) {
      /* ignore */
    }
  }

  function applyTimerData(data) {
    if (!data || typeof data !== "object") return false;
    global.H2V4State.patch({
      timer_seconds: Math.max(1, Number(data.timer_seconds) || 60),
      timer_remaining_seconds: clampNonNegInt(data.timer_remaining_seconds),
      timer_active: Boolean(data.timer_active),
      timer_ends_at: data.timer_ends_at || null,
      timer_paused_remaining: data.timer_paused_remaining,
      _timerInternal: true,
    });
    lastPaintedSecond = null;
    lastEndsAtMs = NaN;
    syncComputed();
    return true;
  }

  function restoreFromSession() {
    if (isDjangoMode()) return false;
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw);
        if (applyTimerData(data)) return true;
      }
    } catch (e) {
      /* fall through */
    }
    try {
      const shared = global.H2V4SyncBus?.loadSharedTimer?.();
      if (shared && applyTimerData(shared)) return true;
    } catch (e) {
      /* ignore */
    }
    return false;
  }

  function syncComputed() {
    const s = state();
    if (!s) return 0;

    // Reset monotonic/paint tracking when deadline changes (new Start/Resume)
    if (s.timer_ends_at) {
      const end = parseServerDate(s.timer_ends_at);
      if (Number.isFinite(end) && end !== lastEndsAtMs) {
        lastEndsAtMs = end;
        lastPaintedSecond = null;
      }
    } else if (!s.timer_active) {
      lastEndsAtMs = NaN;
    }

    const rem = computeRemaining(s);
    s.timer_remaining_seconds = rem;

    if (s.timer_active && rem <= 0) {
      // Soft-complete for UI; Django owns hard state in django mode
      s.timer_active = false;
      s.timer_remaining_seconds = 0;
      if (!isDjangoMode()) {
        s.timer_ends_at = null;
        s.timer_paused_remaining = 0;
      } else {
        s.timer_paused_remaining = null;
      }
    }
    return rem;
  }

  function paintTimerOnly() {
    const s = state();
    if (!s) return;
    const rem = syncComputed();
    const total = Math.max(1, Number(s.timer_seconds) || 60);
    const timer = document.getElementById("timer-value");
    const bar = document.getElementById("timer-bar");
    const wrap = document.querySelector(".timer");
    if (timer) {
      const m = Math.floor(rem / 60);
      const sec = rem % 60;
      timer.textContent = `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
    }
    if (bar) {
      bar.style.width = `${Math.max(0, Math.min(100, (rem / total) * 100))}%`;
    }
    if (wrap) {
      const paused = !s.timer_active && s.timer_paused_remaining != null && rem > 0;
      const running = Boolean(s.timer_active) && rem > 0;
      wrap.classList.toggle("urgent", running && rem <= 10);
      wrap.classList.toggle("expired", rem === 0 && !running && !paused);
      wrap.classList.toggle("running", running);
      wrap.classList.toggle("paused", paused);
    }

    if (rem !== lastPaintedSecond) {
      lastPaintedSecond = rem;
      persist();
      global.H2V4State?.emitTimerTick?.(rem);
    }
  }

  /**
   * Dual loop: rAF for smooth foreground paint + interval backup so background
   * tab throttling cannot permanently freeze the countdown.
   */
  function startTick() {
    if (!rafId) {
      const loop = () => {
        rafId = window.requestAnimationFrame(loop);
        paintTimerOnly();
      };
      rafId = window.requestAnimationFrame(loop);
    }
    if (!intervalId) {
      intervalId = window.setInterval(() => {
        paintTimerOnly();
      }, 250);
    }
  }

  function stopTick() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = 0;
    }
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = 0;
    }
  }

  function bindVisibility() {
    if (visibilityBound) return;
    visibilityBound = true;
    document.addEventListener("visibilitychange", () => {
      paintTimerOnly();
    });
    window.addEventListener("focus", () => {
      paintTimerOnly();
    });
  }

  function setDuration(seconds) {
    const dur = Math.max(1, Math.floor(Number(seconds) || 60));
    const s = state();
    if (!s) return;
    s.timer_seconds = dur;
    if (!s.timer_active) {
      s.timer_remaining_seconds = dur;
      s.timer_paused_remaining = null;
      s.timer_ends_at = null;
      lastPaintedSecond = null;
      lastEndsAtMs = NaN;
    }
    paintTimerOnly();
    persist();
  }

  function start() {
    const s = state();
    if (!s) return;
    // Fresh countdown from configured duration (never leftover rem)
    const rem = Math.max(1, Number(s.timer_seconds) || 60);
    s.timer_seconds = rem;
    s.timer_active = true;
    s.timer_paused_remaining = null;
    s.timer_ends_at = new Date(nowMs() + rem * 1000).toISOString();
    s.timer_remaining_seconds = rem;
    lastPaintedSecond = null;
    lastEndsAtMs = NaN;
    paintTimerOnly();
    startTick();
    persist();
  }

  function pause() {
    const s = state();
    if (!s || !s.timer_active) return;
    const rem = computeRemaining(s);
    s.timer_active = false;
    s.timer_ends_at = null;
    s.timer_paused_remaining = rem;
    s.timer_remaining_seconds = rem;
    lastEndsAtMs = NaN;
    paintTimerOnly();
    persist();
  }

  function resume() {
    const s = state();
    if (!s) return;
    if (s.timer_active) return;
    let rem =
      s.timer_paused_remaining != null
        ? clampNonNegInt(s.timer_paused_remaining)
        : clampNonNegInt(s.timer_remaining_seconds);
    if (rem <= 0) return;
    s.timer_active = true;
    s.timer_paused_remaining = null;
    s.timer_ends_at = new Date(nowMs() + rem * 1000).toISOString();
    s.timer_remaining_seconds = rem;
    lastPaintedSecond = null;
    lastEndsAtMs = NaN;
    paintTimerOnly();
    startTick();
    persist();
  }

  function reset() {
    const s = state();
    if (!s) return;
    const dur = Math.max(1, Number(s.timer_seconds) || 60);
    s.timer_active = false;
    s.timer_ends_at = null;
    s.timer_paused_remaining = null;
    s.timer_remaining_seconds = dur;
    lastPaintedSecond = null;
    lastEndsAtMs = NaN;
    paintTimerOnly();
    persist();
  }

  function clearStorage() {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      /* ignore */
    }
  }

  function boot() {
    const params = new URLSearchParams(location.search);
    bindVisibility();
    if (isDjangoMode()) {
      syncComputed();
      paintTimerOnly();
      startTick();
      return;
    }
    const restored = restoreFromSession();
    if (!restored) {
      const s = state();
      const hydrated =
        s &&
        (s.timer_active || s.timer_ends_at || s.timer_paused_remaining != null);
      if (hydrated) {
        syncComputed();
        persist();
      } else {
        reset();
        clearStorage();
      }
    }
    paintTimerOnly();
    startTick();
    if (params.get("timer") === "1" && !state()?.timer_active) {
      start();
    }
  }

  global.H2V4Timer = {
    boot,
    start,
    pause,
    resume,
    reset,
    setDuration,
    paintTimerOnly,
    computeRemaining,
    persist,
    parseServerDate,
    STORAGE_KEY,
    stopTick,
    startTick,
  };
})(window);
