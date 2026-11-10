/**
 * H2 Live V4 — Django /live/api/state/ adapter (production).
 * Replaces SyncBus when window.H2V4_DJANGO is present.
 *
 * Control PATCH → API, then BroadcastChannel/localStorage pulse so an already-open
 * display paints Live Text immediately (no page refresh). Poll remains source of truth.
 */
(function (global) {
  const cfg = global.H2V4_DJANGO;
  if (!cfg || !cfg.stateUrl) return;

  const MODE = cfg.mode === "control" ? "control" : "display";
  const POLL_MS = Math.max(200, Number(cfg.pollMs) || 400);
  const PUSH_CHANNEL = "h2v4-django-state-push-v1";
  const PUSH_STORAGE_KEY = "h2v4_django_state_push_v1";
  let lastJson = "";
  let polling = false;
  let seeded = false;
  /** Bumps on every PATCH so in-flight polls cannot overwrite a fresher write. */
  let writeEpoch = 0;
  let patchInFlight = 0;
  /** Server live_text_rev — never apply an older live-text payload over a newer one. */
  let appliedLiveTextRev = -1;
  let pushBc = null;
  try {
    pushBc = new BroadcastChannel(PUSH_CHANNEL);
  } catch (e) {
    pushBc = null;
  }

  function csrfToken() {
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function liveTextFromServer(server) {
    const ns = (server && server.new_style) || {};
    // Prefer top-level fields (including explicit "") so Clear Line works on first click
    const line1 =
      server && Object.prototype.hasOwnProperty.call(server, "live_text_line1")
        ? server.live_text_line1
        : ns.live_text_line1;
    const line2 =
      server && Object.prototype.hasOwnProperty.call(server, "live_text_line2")
        ? server.live_text_line2
        : ns.live_text_line2;
    return {
      live_text_line1: String(line1 ?? ""),
      live_text_line2: String(line2 ?? ""),
    };
  }

  function notifyStateApplied(server) {
    global.dispatchEvent(new CustomEvent("h2v4:django-state", { detail: server }));
  }

  function publishPush(server) {
    if (!server) return;
    const envelope = { at: Date.now(), state: server };
    try {
      pushBc?.postMessage(envelope);
    } catch (e) {
      /* ignore */
    }
    try {
      localStorage.setItem(PUSH_STORAGE_KEY, JSON.stringify(envelope));
    } catch (e) {
      /* ignore */
    }
  }

  function serverLiveTextRev(server) {
    const ns = (server && server.new_style) || {};
    const rev = server && server.live_text_rev != null ? server.live_text_rev : ns.live_text_rev;
    return Number(rev) || 0;
  }

  function applyServerState(server, { seedOnly } = {}) {
    if (!server || !global.H2V4State) return;
    const ns = server.new_style || {};
    const live = liveTextFromServer(server);
    const rev = serverLiveTextRev(server);
    const stNow = global.H2V4State.getState();
    // Ignore stale live-text from an older in-flight GET (rev went backwards)
    const useLive = appliedLiveTextRev < 0 || rev >= appliedLiveTextRev;
    if (useLive) appliedLiveTextRev = Math.max(appliedLiveTextRev, rev);
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
      live_text_line1: useLive ? live.live_text_line1 : stNow.live_text_line1 || "",
      live_text_line2: useLive ? live.live_text_line2 : stNow.live_text_line2 || "",
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
      // Seed must still paint Live Text / plate — otherwise display stays blank until refresh
      notifyStateApplied(server);
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
    patchInFlight += 1;
    writeEpoch += 1;
    const epochAtSend = writeEpoch;
    try {
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
      // Only apply if no newer PATCH started while we waited
      if (epochAtSend === writeEpoch) {
        applyServerState(state);
        lastJson = JSON.stringify(state);
        notifyStateApplied(state);
        // Instant cross-tab/display update (open broadcast paints without waiting for poll)
        publishPush(state);
      }
      return state;
    } finally {
      patchInFlight = Math.max(0, patchInFlight - 1);
    }
  }

  function acceptPushedState(server) {
    if (!server || !global.H2V4State) return;
    // Control tab already applied its own PATCH; display tabs need the push.
    if (MODE === "control" || patchInFlight > 0) return;
    writeEpoch += 1;
    lastJson = JSON.stringify(server);
    if (!seeded) applyServerState(server, { seedOnly: true });
    else applyServerState(server);
    notifyStateApplied(server);
  }

  async function pollOnce() {
    if (polling) return;
    // Skip polls while a PATCH is in flight — prevents stale GET stomping a fresh write
    // (classic "Live Text needs two Apply clicks" race).
    if (patchInFlight > 0) return;
    polling = true;
    const epochAtStart = writeEpoch;
    try {
      const state = await fetchState();
      if (epochAtStart !== writeEpoch || patchInFlight > 0) return;
      const raw = JSON.stringify(state);
      if (raw === lastJson) return;
      lastJson = raw;
      if (!seeded) applyServerState(state, { seedOnly: true });
      else applyServerState(state);
      notifyStateApplied(state);
    } catch (e) {
      console.warn("[H2V4 django-bridge]", e);
    } finally {
      polling = false;
    }
  }

  function onPushMessage(envelope) {
    const server = envelope && envelope.state;
    if (!server) return;
    acceptPushedState(server);
  }

  function boot() {
    if (pushBc) {
      pushBc.onmessage = (ev) => onPushMessage(ev?.data);
    }
    global.addEventListener("storage", (ev) => {
      if (ev.key !== PUSH_STORAGE_KEY || !ev.newValue) return;
      try {
        onPushMessage(JSON.parse(ev.newValue));
      } catch (e) {
        /* ignore */
      }
    });

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
