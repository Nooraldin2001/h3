/**
 * H2 Live V4 — sandbox cross-tab sync (BroadcastChannel + localStorage snapshot).
 *
 * Sandbox only. Not production Django. OBS Browser Source may run in a separate
 * process/profile and will NOT receive BroadcastChannel or same-origin storage.
 */
(function (global) {
  const CHANNEL = "h2-v4-sandbox-sync";
  const SNAP_KEY = "h2v4_sandbox_snap_v1";
  const PULSE_KEY = "h2v4_sandbox_pulse_v1";
  const TIMER_SHARED_KEY = "h2v4_timer_shared_v1";
  const LIVE_TEXT_SHARED_KEY = "h2v4_live_text_shared_v1";

  let bc = null;
  try {
    bc = new BroadcastChannel(CHANNEL);
  } catch (e) {
    bc = null;
  }

  const listeners = new Set();
  let lastCmdId = "";
  let publishing = false;

  function safeParse(raw) {
    try {
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function cloneJson(v) {
    try {
      return JSON.parse(JSON.stringify(v));
    } catch (e) {
      return null;
    }
  }

  function extractPersistentState(state) {
    if (!state) return null;
    const ns = state.new_style || {};
    return {
      plate_type: state.plate_type,
      code: state.code,
      number: state.number,
      phone_number: state.phone_number,
      price: state.price,
      timer_seconds: state.timer_seconds,
      timer_remaining_seconds: state.timer_remaining_seconds,
      timer_active: state.timer_active,
      timer_ends_at: state.timer_ends_at,
      timer_paused_remaining: state.timer_paused_remaining,
      sold_event_id: state.sold_event_id,
      sold_style: state.sold_style,
      sold_name: state.sold_name,
      live_text_line1: state.live_text_line1 || "",
      live_text_line2: state.live_text_line2 || "",
      new_style: {
        number_visible: ns.number_visible !== false,
        bg_motion_enabled: !!ns.bg_motion_enabled,
        bg_motion_playing: ns.bg_motion_playing !== false,
        bg_speed: ns.bg_speed,
        bg_density: ns.bg_density,
        aging: cloneJson(ns.aging) || {},
        character: cloneJson(ns.character) || { entry: "bottom_center", speed: 1 },
        // Persist counters so reload seeds edges — does NOT replay one-shots
        events: cloneJson(ns.events) || {},
      },
    };
  }

  function saveSnapshot(extras) {
    const state = global.H2V4State?.getState?.();
    if (!state) return null;
    const snap = {
      saved_at: Date.now(),
      state: extractPersistentState(state),
      aging: extras?.aging || global.H2V4AgingFx?.getStatus?.() || null,
    };
    try {
      localStorage.setItem(SNAP_KEY, JSON.stringify(snap));
    } catch (e) {
      /* ignore */
    }
    try {
      localStorage.setItem(
        TIMER_SHARED_KEY,
        JSON.stringify({
          timer_seconds: state.timer_seconds,
          timer_remaining_seconds: state.timer_remaining_seconds,
          timer_active: state.timer_active,
          timer_ends_at: state.timer_ends_at || null,
          timer_paused_remaining: state.timer_paused_remaining ?? null,
        }),
      );
    } catch (e) {
      /* ignore */
    }
    try {
      localStorage.setItem(
        LIVE_TEXT_SHARED_KEY,
        JSON.stringify({
          live_text_line1: state.live_text_line1 || "",
          live_text_line2: state.live_text_line2 || "",
        }),
      );
    } catch (e) {
      /* ignore */
    }
    return snap;
  }

  function loadSnapshot() {
    try {
      return safeParse(localStorage.getItem(SNAP_KEY));
    } catch (e) {
      return null;
    }
  }

  function loadSharedTimer() {
    try {
      return safeParse(localStorage.getItem(TIMER_SHARED_KEY));
    } catch (e) {
      return null;
    }
  }

  function loadSharedLiveText() {
    try {
      return safeParse(localStorage.getItem(LIVE_TEXT_SHARED_KEY));
    } catch (e) {
      return null;
    }
  }

  /**
   * Hydrate broadcast state from snapshot WITHOUT replaying one-shot edges.
   * Call before FX boot / after H2V4State exists / before or with seedFromState.
   */
  function hydrateBroadcastFromSnapshot() {
    const snap = loadSnapshot();
    const state = global.H2V4State?.getState?.();
    if (!state) return { ok: false, reason: "no-state" };

    if (snap?.state) {
      const p = snap.state;
      [
        "plate_type",
        "code",
        "number",
        "phone_number",
        "price",
        "timer_seconds",
        "timer_remaining_seconds",
        "timer_active",
        "timer_ends_at",
        "timer_paused_remaining",
        "sold_event_id",
        "sold_style",
        "sold_name",
        "live_text_line1",
        "live_text_line2",
      ].forEach((k) => {
        if (p[k] !== undefined) state[k] = p[k];
      });
      if (p.new_style) {
        Object.assign(state.new_style, p.new_style);
        if (p.new_style.events) {
          state.new_style.events = Object.assign({}, state.new_style.events, p.new_style.events);
        }
        if (p.new_style.aging) {
          state.new_style.aging = Object.assign({}, state.new_style.aging, p.new_style.aging);
        }
        if (p.new_style.character) {
          state.new_style.character = Object.assign(
            {},
            state.new_style.character,
            p.new_style.character,
          );
        }
      }
    }

    // Shared timer / live text fallbacks (even if full snapshot missing)
    const t = loadSharedTimer();
    if (t && typeof t === "object") {
      if (t.timer_seconds != null) state.timer_seconds = t.timer_seconds;
      if (t.timer_remaining_seconds != null) state.timer_remaining_seconds = t.timer_remaining_seconds;
      if (t.timer_active != null) state.timer_active = !!t.timer_active;
      if (t.timer_ends_at !== undefined) state.timer_ends_at = t.timer_ends_at;
      if (t.timer_paused_remaining !== undefined) {
        state.timer_paused_remaining = t.timer_paused_remaining;
      }
    }
    const lt = loadSharedLiveText();
    if (lt && typeof lt === "object") {
      if (lt.live_text_line1 != null) state.live_text_line1 = String(lt.live_text_line1).slice(0, 100);
      if (lt.live_text_line2 != null) state.live_text_line2 = String(lt.live_text_line2).slice(0, 100);
    }

    // Seed edge counters so SOLD / drop / cards do not replay after refresh
    global.H2V4State.seedFromState?.();
    return { ok: true, snap };
  }

  function restoreAgingFromSnapshot(snap) {
    const a = snap?.state?.new_style?.aging || snap?.aging;
    if (!a || !global.H2V4AgingFx) return;
    const fx = global.H2V4AgingFx;
    const enabled = !!(a.enabled ?? snap?.aging?.enabled);
    if (!enabled) {
      fx.disable?.();
      return;
    }
    fx.enable?.();
    if (a.total_duration_seconds != null) {
      fx.setDuration?.(a.total_duration_seconds);
    }
    // Restore elapsed via seek when we have progress info
    const status = snap?.aging;
    const progress =
      status && typeof status.progress === "number"
        ? status.progress
        : a.completed
          ? 1
          : null;
    if (progress != null && progress > 0) {
      fx.seekProgress?.(progress, { freeze: !(a.running && !a.paused && !a.completed) });
    }
    if (a.running && !a.paused && !a.completed) {
      // Resume independent aging clock from restored elapsed
      fx.startAging?.();
    } else if (a.paused) {
      fx.startAging?.();
      fx.pauseAging?.();
    }
  }

  function publish(msg) {
    if (!msg || typeof msg !== "object") return;
    const envelope = Object.assign(
      {
        bus: "h2v4-sync",
        ts: Date.now(),
        id: msg.id || `m_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      },
      msg,
    );
    publishing = true;
    try {
      bc?.postMessage(envelope);
    } catch (e) {
      /* ignore */
    }
    // storage event fallback for contexts where BC is unavailable
    try {
      localStorage.setItem(PULSE_KEY, JSON.stringify(envelope));
      // Clear quickly so repeated identical payloads still fire storage events
      localStorage.removeItem(PULSE_KEY);
    } catch (e) {
      /* ignore */
    }
    publishing = false;
  }

  function dispatch(msg) {
    if (!msg || msg.bus !== "h2v4-sync") return;
    if (msg.id && msg.id === lastCmdId && msg.type === "cmd") return;
    if (msg.type === "cmd" && msg.id) lastCmdId = msg.id;
    listeners.forEach((fn) => {
      try {
        fn(msg);
      } catch (e) {
        console.error("[H2V4 sync]", e);
      }
    });
  }

  function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  }

  if (bc) {
    bc.addEventListener("message", (ev) => dispatch(ev.data));
  }
  global.addEventListener("storage", (ev) => {
    if (ev.key !== PULSE_KEY || !ev.newValue) return;
    dispatch(safeParse(ev.newValue));
  });

  /** Control → broadcast command */
  function sendCommand(inner) {
    const id = `cmd_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    publish({ type: "cmd", id, role: "control", ...inner });
    return id;
  }

  function sendPatch(payload) {
    return sendCommand({ cmd: "patch", payload });
  }

  function sendCharacter(action, extras) {
    return sendCommand({ cmd: "character", action, extras: extras || {} });
  }

  function sendCharacterReset() {
    return sendCommand({ cmd: "characterReset" });
  }

  function sendAgingSeek(progress) {
    return sendCommand({ cmd: "agingSeek", progress });
  }

  function requestStatus() {
    return sendCommand({ cmd: "getStatus" });
  }

  function publishStatus() {
    if (publishing) return;
    const state = global.H2V4State?.getState?.();
    if (!state) return;
    saveSnapshot({ aging: global.H2V4AgingFx?.getStatus?.() });
    publish({
      type: "status",
      role: "broadcast",
      state: cloneJson(state),
      aging: global.H2V4AgingFx?.getStatus?.() || null,
      character: global.H2V4Character?.getHud?.() || null,
    });
  }

  global.H2V4SyncBus = {
    CHANNEL,
    SNAP_KEY,
    TIMER_SHARED_KEY,
    LIVE_TEXT_SHARED_KEY,
    publish,
    subscribe,
    sendCommand,
    sendPatch,
    sendCharacter,
    sendCharacterReset,
    sendAgingSeek,
    requestStatus,
    publishStatus,
    saveSnapshot,
    loadSnapshot,
    loadSharedTimer,
    loadSharedLiveText,
    hydrateBroadcastFromSnapshot,
    restoreAgingFromSnapshot,
    extractPersistentState,
    HAS_BROADCAST_CHANNEL: !!bc,
    LIMITATION:
      "BroadcastChannel + localStorage sync only within the same browser profile/origin. OBS Browser Source often uses a separate Chromium process and will not receive these messages. Production must use Django session/API.",
  };
})(window);
