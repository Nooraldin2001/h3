/**
 * H2 Live V4 — mock countdown timer (authoritative ends_at).
 * Independent of aging. Single interval. No auto-start unless explicitly started.
 *
 * Cause of prior freeze: broadcast only painted static timer_remaining_seconds once;
 * there was no ends_at clock or tick loop.
 */
(function (global) {
  const STORAGE_KEY = "h2v4_timer_v1";
  let tickId = 0;
  let lastPaintedSecond = null;

  function state() {
    return global.H2V4State?.getState?.();
  }

  function nowMs() {
    return global.H2V4State?.nowMs?.() || Date.now();
  }

  function clampRemaining(sec) {
    return Math.max(0, Math.floor(Number(sec) || 0));
  }

  function computeRemaining(s) {
    if (!s) return 0;
    if (s.timer_active && s.timer_ends_at) {
      const end = Date.parse(s.timer_ends_at);
      if (Number.isFinite(end)) {
        return clampRemaining((end - nowMs()) / 1000);
      }
    }
    if (s.timer_paused_remaining != null) {
      return clampRemaining(s.timer_paused_remaining);
    }
    return clampRemaining(s.timer_remaining_seconds);
  }

  function persist() {
    const s = state();
    if (!s) return;
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          timer_seconds: s.timer_seconds,
          timer_remaining_seconds: s.timer_remaining_seconds,
          timer_active: s.timer_active,
          timer_ends_at: s.timer_ends_at || null,
          timer_paused_remaining: s.timer_paused_remaining ?? null,
        }),
      );
    } catch (e) {
      /* ignore quota */
    }
  }

  function restoreFromSession() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return false;
      const data = JSON.parse(raw);
      if (!data || typeof data !== "object") return false;
      global.H2V4State.patch({
        timer_seconds: Math.max(1, Number(data.timer_seconds) || 60),
        timer_remaining_seconds: clampRemaining(data.timer_remaining_seconds),
        timer_active: Boolean(data.timer_active),
        timer_ends_at: data.timer_ends_at || null,
        timer_paused_remaining: data.timer_paused_remaining,
        _timerInternal: true,
      });
      // Recompute from ends_at after refresh (handles tab throttle / OBS reload)
      syncComputed();
      return true;
    } catch (e) {
      return false;
    }
  }

  function syncComputed() {
    const s = state();
    if (!s) return 0;
    const rem = computeRemaining(s);
    s.timer_remaining_seconds = rem;
    if (s.timer_active && rem <= 0) {
      s.timer_active = false;
      s.timer_ends_at = null;
      s.timer_paused_remaining = 0;
      s.timer_remaining_seconds = 0;
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
      wrap.classList.toggle("urgent", s.timer_active && rem <= 10 && rem > 0);
      wrap.classList.toggle("expired", rem === 0 && !s.timer_active && s.timer_paused_remaining === 0);
      wrap.classList.toggle("running", Boolean(s.timer_active));
      wrap.classList.toggle("paused", !s.timer_active && s.timer_paused_remaining != null && rem > 0);
    }
    if (rem !== lastPaintedSecond) {
      lastPaintedSecond = rem;
      persist();
      global.H2V4State?.emitTimerTick?.(rem);
    }
  }

  function startTick() {
    if (tickId) return;
    tickId = window.setInterval(() => {
      paintTimerOnly();
    }, 200);
  }

  function stopTick() {
    if (tickId) {
      clearInterval(tickId);
      tickId = 0;
    }
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
    }
    paintTimerOnly();
    persist();
  }

  function start() {
    const s = state();
    if (!s) return;
    let rem = computeRemaining(s);
    if (rem <= 0) rem = Math.max(1, Number(s.timer_seconds) || 60);
    s.timer_active = true;
    s.timer_paused_remaining = null;
    s.timer_ends_at = new Date(nowMs() + rem * 1000).toISOString();
    s.timer_remaining_seconds = rem;
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
    paintTimerOnly();
    persist();
  }

  function resume() {
    const s = state();
    if (!s) return;
    if (s.timer_active) return;
    let rem = s.timer_paused_remaining != null
      ? clampRemaining(s.timer_paused_remaining)
      : clampRemaining(s.timer_remaining_seconds);
    if (rem <= 0) return;
    s.timer_active = true;
    s.timer_paused_remaining = null;
    s.timer_ends_at = new Date(nowMs() + rem * 1000).toISOString();
    s.timer_remaining_seconds = rem;
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
    paintTimerOnly();
    persist();
  }

  function clearStorage() {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch (e) { /* ignore */ }
  }

  function boot() {
    const params = new URLSearchParams(location.search);
    const restored = restoreFromSession();
    if (!restored) {
      // Explicit idle reset — do not pretend server state existed
      reset();
      clearStorage();
    }
    paintTimerOnly();
    startTick(); // always tick so active timers update; idle is cheap
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
    STORAGE_KEY,
    CAUSE: "Frozen because remaining was painted once from mock with no ends_at tick loop.",
  };
})(window);
