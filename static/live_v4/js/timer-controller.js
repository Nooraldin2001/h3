/**
 * H2 Live V4 — countdown timer (authoritative ends_at + local anchor).
 * Independent of aging. Display must not paint polled timer_remaining_seconds.
 *
 * Cause of lag/jumps (55→56→55): django poll overwrote remaining every ~300ms
 * and broadcast painted that stale integer. Tablet Safari also choked on
 * Django 6-digit microsecond ISO timestamps.
 */
(function (global) {
  const STORAGE_KEY = "h2v4_timer_v1";
  let tickId = 0;
  let rafId = 0;
  let lastPaintedSecond = null;
  let timerAnchor = null; // { endsAtMs, clientAtMs, startRemaining }
  const TIMER_DEBUG = /(?:\?|&)timer_debug=1(?:&|$)/.test(location.search || "");
  const debugSeq = [];

  function state() {
    return global.H2V4State?.getState?.();
  }

  function clampRemaining(sec) {
    return Math.max(0, Math.floor(Number(sec) || 0));
  }

  function parseServerDate(iso) {
    if (!iso) return NaN;
    let s = String(iso).trim();
    // Safari/iPad: Django isoformat uses 6-digit micros — truncate to millis.
    s = s.replace(/\.(\d{3})\d+(?=(Z|[+-]\d{2}:?\d{2})$)/, ".$1");
    let ms = Date.parse(s);
    if (!Number.isFinite(ms)) {
      ms = Date.parse(s.replace(/([+-]\d{2}):(\d{2})$/, "$1$2"));
    }
    return ms;
  }

  function syncAnchor(s) {
    if (!(s && s.timer_active && s.timer_ends_at)) {
      timerAnchor = null;
      return;
    }
    const endsAtMs = parseServerDate(s.timer_ends_at);
    if (!Number.isFinite(endsAtMs)) {
      timerAnchor = null;
      return;
    }
    if (timerAnchor && Math.abs(timerAnchor.endsAtMs - endsAtMs) < 250) {
      return;
    }
    const clientAtMs = Date.now();
    timerAnchor = {
      endsAtMs: endsAtMs,
      clientAtMs: clientAtMs,
      startRemaining: Math.max(0, Math.floor((endsAtMs - clientAtMs) / 1000)),
    };
    lastPaintedSecond = null;
  }

  function computeRemaining(s) {
    if (!s) return 0;
    syncAnchor(s);
    let rem;
    if (s.timer_active && timerAnchor) {
      const elapsed = Math.floor((Date.now() - timerAnchor.clientAtMs) / 1000);
      rem = Math.max(0, timerAnchor.startRemaining - elapsed);
    } else if (s.timer_active && s.timer_ends_at) {
      const end = parseServerDate(s.timer_ends_at);
      if (Number.isFinite(end)) {
        rem = clampRemaining((end - Date.now()) / 1000);
      } else if (s.timer_paused_remaining != null) {
        rem = clampRemaining(s.timer_paused_remaining);
      } else {
        rem = clampRemaining(s.timer_remaining_seconds);
      }
    } else if (s.timer_paused_remaining != null) {
      rem = clampRemaining(s.timer_paused_remaining);
    } else {
      rem = clampRemaining(s.timer_remaining_seconds);
    }
    // Monotonic: never jump upward while the same ends_at is running.
    if (s.timer_active && lastPaintedSecond != null && rem > lastPaintedSecond) {
      return lastPaintedSecond;
    }
    return rem;
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
    const s = state();
    if (!s) return;
    const payload = timerPayload(s);
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (e) {
      /* ignore quota */
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
      timer_remaining_seconds: clampRemaining(data.timer_remaining_seconds),
      timer_active: Boolean(data.timer_active),
      timer_ends_at: data.timer_ends_at || null,
      timer_paused_remaining: data.timer_paused_remaining,
      _timerInternal: true,
    });
    syncComputed();
    return true;
  }

  function restoreFromSession() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw);
        if (applyTimerData(data)) return true;
      }
    } catch (e) {
      /* fall through to shared */
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
    const rem = computeRemaining(s);
    s.timer_remaining_seconds = rem;
    if (s.timer_active && rem <= 0) {
      s.timer_active = false;
      s.timer_ends_at = null;
      s.timer_paused_remaining = 0;
      s.timer_remaining_seconds = 0;
      timerAnchor = null;
    }
    return rem;
  }

  function ensureDebugHud() {
    if (!TIMER_DEBUG) return null;
    let hud = document.getElementById("h2v4-timer-debug-hud");
    if (!hud) {
      hud = document.createElement("div");
      hud.id = "h2v4-timer-debug-hud";
      hud.style.cssText =
        "position:fixed;left:8px;bottom:8px;z-index:99999;max-width:92vw;padding:8px 10px;border-radius:8px;background:rgba(0,0,0,.75);color:#0f0;font:12px/1.35 monospace;white-space:pre-wrap;pointer-events:none;";
      document.body.appendChild(hud);
    }
    return hud;
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

    // #region agent log
    if (rem !== lastPaintedSecond) {
      const parseOk = !s.timer_ends_at || Number.isFinite(parseServerDate(s.timer_ends_at));
      const payload = {
        sessionId: "ddcc38",
        runId: "post-fix",
        hypothesisId: "V4",
        location: "live_v4/timer-controller.js:paintTimerOnly",
        message: "v4 timer paint",
        data: {
          rem: rem,
          prev: lastPaintedSecond,
          jumpedUp: lastPaintedSecond != null && rem > lastPaintedSecond,
          parseOk: parseOk,
          hasAnchor: !!timerAnchor,
          active: !!s.timer_active,
          endsAt: s.timer_ends_at || null,
        },
        timestamp: Date.now(),
      };
      fetch("http://127.0.0.1:7650/ingest/6effd724-0433-4a9b-be69-34787675ecdc", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "ddcc38" },
        body: JSON.stringify(payload),
      }).catch(() => {});
      try {
        (global.__timerDebugLogs = global.__timerDebugLogs || []).push(payload);
        if (TIMER_DEBUG) {
          debugSeq.push(rem);
          if (debugSeq.length > 24) debugSeq.shift();
          const hud = ensureDebugHud();
          if (hud) {
            hud.textContent =
              "V4 seq " +
              debugSeq.join(">") +
              "\nparseOk=" +
              parseOk +
              " anchor=" +
              !!timerAnchor +
              " active=" +
              !!s.timer_active;
          }
        }
      } catch (e) {
        /* ignore */
      }
    }
    // #endregion

    if (rem !== lastPaintedSecond) {
      lastPaintedSecond = rem;
      persist();
      global.H2V4State?.emitTimerTick?.(rem);
    }
  }

  function startTick() {
    if (rafId || tickId) return;
    const tick = () => {
      rafId = window.requestAnimationFrame(tick);
      const s = state();
      if (s && s.timer_active && (timerAnchor || s.timer_ends_at)) {
        paintTimerOnly();
      }
    };
    rafId = window.requestAnimationFrame(tick);
    tickId = rafId;
  }

  function stopTick() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = 0;
    }
    if (tickId && !rafId) {
      clearInterval(tickId);
    }
    tickId = 0;
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
      timerAnchor = null;
      lastPaintedSecond = null;
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
    s.timer_ends_at = new Date(Date.now() + rem * 1000).toISOString();
    s.timer_remaining_seconds = rem;
    timerAnchor = null;
    lastPaintedSecond = null;
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
    timerAnchor = null;
    paintTimerOnly();
    persist();
  }

  function resume() {
    const s = state();
    if (!s) return;
    if (s.timer_active) return;
    let rem =
      s.timer_paused_remaining != null
        ? clampRemaining(s.timer_paused_remaining)
        : clampRemaining(s.timer_remaining_seconds);
    if (rem <= 0) return;
    s.timer_active = true;
    s.timer_paused_remaining = null;
    s.timer_ends_at = new Date(Date.now() + rem * 1000).toISOString();
    s.timer_remaining_seconds = rem;
    timerAnchor = null;
    lastPaintedSecond = null;
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
    timerAnchor = null;
    lastPaintedSecond = null;
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
    STORAGE_KEY,
    CAUSE: "Poll painted timer_remaining_seconds over local ends_at tick.",
  };
})(window);
