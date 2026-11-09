/**
 * H2 Live V4 — Django /live/api/state/ adapter (production).
 * Replaces SyncBus when window.H2V4_DJANGO is present.
 */
(function (global) {
  const cfg = global.H2V4_DJANGO;
  if (!cfg || !cfg.stateUrl) return;

  const MODE = cfg.mode === "control" ? "control" : "display";
  const POLL_MS = Math.max(250, Number(cfg.pollMs) || 500);
  let lastJson = "";
  let polling = false;
  let seeded = false;

  function csrfToken() {
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function applyServerState(server, { seedOnly } = {}) {
    if (!server || !global.H2V4State) return;
    const ns = server.new_style || {};
    const patch = {
      plate_type: server.plate_type,
      code: server.code || "",
      number: server.number || "",
      phone_number: server.phone_number || "",
      price: server.price || "0",
      timer_seconds: server.timer_seconds,
      timer_remaining_seconds: server.timer_remaining_seconds,
      timer_active: !!server.timer_active,
      timer_ends_at: server.timer_ends_at || null,
      timer_paused_remaining: server.timer_paused_remaining,
      sold_event_id: server.sold_event_id || 0,
      sold_style: server.sold_style || "fireworks",
      sold_name: server.sold_name || "",
      live_text_line1: server.live_text_line1 || ns.live_text_line1 || "",
      live_text_line2: server.live_text_line2 || ns.live_text_line2 || "",
      new_style: {
        number_visible: ns.number_visible !== false,
        bg_motion_enabled: !!ns.bg_motion_enabled,
        bg_motion_playing: ns.bg_motion_playing !== false,
        bg_speed: ns.bg_speed,
        bg_density: ns.bg_density,
        character: ns.character || { entry: "bottom_center", speed: 1 },
        aging: ns.aging || {},
        events: ns.events || {},
      },
      _timerInternal: true,
    };

    if (seedOnly) {
      // Assign without firing one-shots, then seed edge counters
      const st = global.H2V4State.getState();
      Object.keys(patch).forEach((k) => {
        if (k === "new_style" || k === "_timerInternal") return;
        if (patch[k] !== undefined) st[k] = patch[k];
      });
      Object.assign(st.new_style, patch.new_style);
      if (patch.new_style.events) {
        st.new_style.events = Object.assign({}, st.new_style.events, patch.new_style.events);
      }
      if (patch.new_style.aging) {
        st.new_style.aging = Object.assign({}, st.new_style.aging, patch.new_style.aging);
      }
      global.H2V4State.seedFromState();
      seeded = true;
      global.H2V4Timer?.paintTimerOnly?.();
      return;
    }

    global.H2V4State.patch(patch);

    // Aging FX follows server flags (display only)
    if (MODE === "display" && global.H2V4AgingFx && ns.aging) {
      const a = ns.aging;
      if (a.enabled) {
        global.H2V4AgingFx.enable?.();
        if (a.total_duration_seconds) global.H2V4AgingFx.setDuration?.(a.total_duration_seconds);
        if (a.running && !a.paused && !a.completed) global.H2V4AgingFx.startAging?.();
        else if (a.paused) {
          global.H2V4AgingFx.startAging?.();
          global.H2V4AgingFx.pauseAging?.();
        }
      } else {
        global.H2V4AgingFx.disable?.();
      }
    }
  }

  async function fetchState() {
    const url =
      MODE === "display" && cfg.token
        ? `${cfg.stateUrl}?token=${encodeURIComponent(cfg.token)}`
        : cfg.stateUrl;
    const res = await fetch(url, {
      credentials: MODE === "control" ? "same-origin" : "omit",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`state ${res.status}`);
    return res.json();
  }

  async function sendPatch(payload) {
    const res = await fetch(cfg.stateUrl, {
      method: "PATCH",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || `patch ${res.status}`);
    }
    const state = await res.json();
    applyServerState(state);
    lastJson = JSON.stringify(state);
    global.dispatchEvent(new CustomEvent("h2v4:django-state", { detail: state }));
    return state;
  }

  async function pollOnce() {
    if (polling) return;
    polling = true;
    try {
      const state = await fetchState();
      const raw = JSON.stringify(state);
      if (raw === lastJson) return;
      lastJson = raw;
      if (!seeded) applyServerState(state, { seedOnly: true });
      else applyServerState(state);
      global.dispatchEvent(new CustomEvent("h2v4:django-state", { detail: state }));
    } catch (e) {
      console.warn("[H2V4 django-bridge]", e);
    } finally {
      polling = false;
    }
  }

  function boot() {
    if (cfg.initialState) {
      applyServerState(cfg.initialState, { seedOnly: true });
      lastJson = JSON.stringify(cfg.initialState);
    }
    pollOnce();
    window.setInterval(pollOnce, POLL_MS);
  }

  global.H2V4DjangoBridge = {
    sendPatch,
    fetchState,
    pollOnce,
    MODE,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(boot, 50));
  } else {
    setTimeout(boot, 50);
  }
})(window);
