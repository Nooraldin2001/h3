/**
 * H2 Live V4 — mock broadcast state bus.
 * Mirrors production event counter names + plate_identity lot semantics.
 * Seeds one-shot IDs on load so refresh never replays animations.
 */
(function (global) {
  function defaultEvents() {
    return {
      reveal_event_id: 0,
      hide_event_id: 0,
      reveal_replay_event_id: 0,
      beam_event_id: 0,
      drop_event_id: 0,
      aging_reset_event_id: 0,
      aging_replay_event_id: 0,
      kandura_event_id: 0,
      char_point_event_id: 0,
      char_yellow_event_id: 0,
      char_red_event_id: 0,
      char_sold_stamp_event_id: 0,
    };
  }

  function plateIdentity(s) {
    return [
      s.plate_type || "",
      (s.code || "").trim(),
      (s.number || "").trim(),
      (s.phone_number || "").trim(),
    ].join("|");
  }

  function createInitialState() {
    const now = Date.now();
    return {
      plate_type: "dubai",
      code: "AA",
      number: "7777",
      phone_number: "",
      price: "1250000",
      timer_seconds: 60,
      timer_remaining_seconds: 60,
      timer_active: false,
      timer_ends_at: null,
      timer_paused_remaining: null,
      sold_event_id: 0,
      sold_style: "fireworks",
      sold_name: "",
      // Live screen text (between logo and timer) — plain text only
      live_text_line1: "",
      live_text_line2: "",
      server_now: new Date(now).toISOString(),
      new_style: {
        number_visible: true,
        bg_motion_enabled: false,
        bg_motion_playing: true,
        bg_speed: 0.65,
        bg_density: 16,
        aging: {
          // Independent of auction timer. Default OFF — start only on explicit action.
          enabled: false,
          running: false,
          paused: false,
          completed: false,
          total_duration_seconds: 60,
          started_at: null,
          elapsed_ms: 0,
          // Legacy mirrors (derived from 60s stage proportions)
          fresh_delay_seconds: 50,
          aging_duration_seconds: 10,
          paused_elapsed_seconds: 0,
        },
        character: { entry: "left", speed: 1 },
        events: defaultEvents(),
      },
    };
  }

  const LIVE_TEXT_KEY = "h2v4_live_screen_text";
  const LIVE_TEXT_MAX = 100;

  const listeners = new Set();
  let state = createInitialState();
  let lastSoldEventId = 0;
  let lastEvents = defaultEvents();
  let lastIdentity = plateIdentity(state);
  let seeded = false;
  let clockOffsetMs = 0;

  function sanitizeLiveText(v) {
    if (v == null) return "";
    return String(v).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "").slice(0, LIVE_TEXT_MAX);
  }

  function persistLiveText() {
    const payload = {
      live_text_line1: state.live_text_line1 || "",
      live_text_line2: state.live_text_line2 || "",
    };
    try {
      sessionStorage.setItem(LIVE_TEXT_KEY, JSON.stringify(payload));
    } catch (e) {
      /* ignore quota / private mode */
    }
    try {
      const sharedKey = global.H2V4SyncBus?.LIVE_TEXT_SHARED_KEY || "h2v4_live_text_shared_v1";
      localStorage.setItem(sharedKey, JSON.stringify(payload));
    } catch (e) {
      /* ignore */
    }
  }

  function applyLiveTextData(data) {
    if (!data || typeof data !== "object") return;
    if (data.live_text_line1 != null) state.live_text_line1 = sanitizeLiveText(data.live_text_line1);
    if (data.live_text_line2 != null) state.live_text_line2 = sanitizeLiveText(data.live_text_line2);
  }

  function restoreLiveText() {
    try {
      const raw = sessionStorage.getItem(LIVE_TEXT_KEY);
      if (raw) {
        applyLiveTextData(JSON.parse(raw));
        return;
      }
    } catch (e) {
      /* fall through */
    }
    try {
      const shared = global.H2V4SyncBus?.loadSharedLiveText?.();
      if (shared) applyLiveTextData(shared);
    } catch (e) {
      /* ignore */
    }
  }

  function emit(kind, detail) {
    listeners.forEach((fn) => {
      try {
        fn(kind, detail, state);
      } catch (e) {
        console.error("[H2V4 state]", e);
      }
    });
  }

  function seedFromState() {
    lastSoldEventId = Number(state.sold_event_id) || 0;
    lastEvents = Object.assign({}, state.new_style.events);
    lastIdentity = plateIdentity(state);
    seeded = true;
  }

  function bump(eventKey) {
    const ev = state.new_style.events;
    ev[eventKey] = (Number(ev[eventKey]) || 0) + 1;
    processEdges();
    emit("state", { reason: "bump", eventKey });
  }

  function processEdges() {
    if (!seeded) {
      seedFromState();
      return;
    }

    const identity = plateIdentity(state);
    if (identity !== lastIdentity) {
      lastIdentity = identity;
      emit("lot_change", { identity });
      // Keep counters; do not rewind — prevents replay of old one-shots.
    }

    const next = state.new_style.events;
    const prev = lastEvents;

    const edge = (key) => (Number(next[key]) || 0) > (Number(prev[key]) || 0);

    if (edge("reveal_event_id") || edge("reveal_replay_event_id")) {
      state.new_style.number_visible = true;
      emit("reveal", {});
    }
    if (edge("hide_event_id")) {
      state.new_style.number_visible = false;
      emit("hide", {});
    }
    if (edge("beam_event_id")) emit("beam", {});
    if (edge("drop_event_id")) emit("drop", {});
    if (edge("aging_reset_event_id")) {
      global.H2V4AgingFx?.resetAging?.();
      emit("aging_reset", {});
    }
    if (edge("aging_replay_event_id")) {
      // Replay = enable + start from pristine (normalized timeline)
      global.H2V4AgingFx?.enable?.();
      global.H2V4AgingFx?.resetAging?.();
      global.H2V4AgingFx?.startAging?.();
      emit("aging_replay", {});
    }

    const pointBump = Math.max(
      Number(next.char_point_event_id) || 0,
      Number(next.kandura_event_id) || 0,
    );
    const prevPoint = Math.max(
      Number(prev.char_point_event_id) || 0,
      Number(prev.kandura_event_id) || 0,
    );
    if (pointBump > prevPoint) emit("char_point", {});
    if (edge("char_yellow_event_id")) emit("char_yellow", {});
    if (edge("char_red_event_id")) {
      state.new_style.number_visible = false;
      emit("char_red", {});
    }

    const soldId = Number(state.sold_event_id) || 0;
    const soldBumped = soldId > lastSoldEventId;
    if (edge("char_sold_stamp_event_id")) {
      emit("char_sold_stamp", { soldAlsoBumped: soldBumped });
    }
    if (soldBumped) {
      lastSoldEventId = soldId;
      emit("sold", { style: state.sold_style, name: state.sold_name });
    }

    lastEvents = Object.assign({}, next);
  }

  function patch(partial) {
    if (!partial || typeof partial !== "object") return state;
    const keys = [
      "plate_type", "code", "number", "phone_number", "price",
      "timer_seconds", "timer_remaining_seconds", "timer_active",
      "timer_ends_at", "timer_paused_remaining",
      "sold_style", "sold_name",
    ];
    keys.forEach((k) => {
      if (partial[k] !== undefined) state[k] = partial[k];
    });

    let liveTextChanged = false;
    if (partial.live_text_line1 !== undefined) {
      state.live_text_line1 = sanitizeLiveText(partial.live_text_line1);
      liveTextChanged = true;
    }
    if (partial.live_text_line2 !== undefined) {
      state.live_text_line2 = sanitizeLiveText(partial.live_text_line2);
      liveTextChanged = true;
    }
    if (liveTextChanged) persistLiveText();

    // Timer command aliases (sandbox / future API parity)
    // Apply duration before start so Start+duration in one patch uses the requested length
    if (partial.timer_seconds != null && !partial._timerInternal) {
      global.H2V4Timer?.setDuration?.(partial.timer_seconds);
    }
    if (partial.start_timer) {
      global.H2V4Timer?.start?.();
    }
    if (partial.pause_timer) {
      global.H2V4Timer?.pause?.();
    }
    if (partial.resume_timer) {
      global.H2V4Timer?.resume?.();
    }
    if (partial.stop_timer || partial.reset_timer) {
      global.H2V4Timer?.reset?.();
    }

    if (partial.trigger_sold) {
      state.sold_event_id = (Number(state.sold_event_id) || 0) + 1;
      if (partial.sold_style) state.sold_style = partial.sold_style;
      if (partial.sold_name !== undefined) state.sold_name = partial.sold_name;
    }
    if (partial.new_style && typeof partial.new_style === "object") {
      Object.assign(state.new_style, partial.new_style);
      if (partial.new_style.events) {
        Object.assign(state.new_style.events, partial.new_style.events);
      }
      if (partial.new_style.aging) {
        Object.assign(state.new_style.aging, partial.new_style.aging);
        if (partial.new_style.aging.total_duration_seconds != null) {
          global.H2V4AgingFx?.setDuration?.(partial.new_style.aging.total_duration_seconds);
        }
      }
      if (partial.new_style.character) {
        Object.assign(state.new_style.character, partial.new_style.character);
      }
    }
    if (partial.aging_duration_seconds != null) {
      global.H2V4AgingFx?.setDuration?.(partial.aging_duration_seconds);
    }
    // One-shot command aliases (mirror control panel flags)
    const cmds = {
      ns_show_number: () => { state.new_style.number_visible = true; bump("reveal_event_id"); },
      ns_hide_number: () => { state.new_style.number_visible = false; bump("hide_event_id"); },
      ns_replay_reveal: () => { state.new_style.number_visible = true; bump("reveal_replay_event_id"); },
      ns_beam: () => bump("beam_event_id"),
      ns_drop: () => bump("drop_event_id"),
      ns_aging_reset: () => bump("aging_reset_event_id"),
      ns_aging_replay: () => bump("aging_replay_event_id"),
      aging_enable: () => global.H2V4AgingFx?.enable?.(),
      aging_disable: () => global.H2V4AgingFx?.disable?.(),
      aging_start: () => global.H2V4AgingFx?.startAging?.(),
      aging_pause: () => global.H2V4AgingFx?.pauseAging?.(),
      aging_resume: () => global.H2V4AgingFx?.resumeAging?.(),
      aging_reset: () => global.H2V4AgingFx?.resetAging?.(),
      ns_char_point: () => bump("char_point_event_id"),
      ns_char_yellow: () => bump("char_yellow_event_id"),
      ns_char_red: () => bump("char_red_event_id"),
      ns_char_sold_stamp: () => {
        if (!partial.trigger_sold) {
          state.sold_event_id = (Number(state.sold_event_id) || 0) + 1;
          state.sold_style = "fireworks";
        }
        bump("char_sold_stamp_event_id");
      },
    };
    Object.keys(cmds).forEach((flag) => {
      if (partial[flag]) cmds[flag]();
    });

    if (!partial.ns_char_sold_stamp && !Object.keys(cmds).some((f) => partial[f] && f.startsWith("ns_"))) {
      processEdges();
    } else if (partial.trigger_sold && !partial.ns_char_sold_stamp) {
      processEdges();
    }

    emit("state", { reason: "patch" });
    return state;
  }

  function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  }

  function getState() {
    return state;
  }

  function nowMs() {
    return Date.now() + clockOffsetMs;
  }

  // Public mock control for QA / debug panel
  global.H2V4State = {
    getState,
    patch,
    subscribe,
    seedFromState,
    plateIdentity: () => plateIdentity(state),
    bump,
    nowMs,
    _resetForTests() {
      state = createInitialState();
      seeded = false;
      seedFromState();
      emit("state", { reason: "reset" });
    },
  };

  restoreLiveText();
  seedFromState();
})(window);
