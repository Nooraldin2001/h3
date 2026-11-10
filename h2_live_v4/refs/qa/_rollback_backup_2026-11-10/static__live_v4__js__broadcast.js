/**
 * H2 Auctions Live V4 — broadcast orchestrator (sandbox).
 * Mock state only. No Django API (Phase 8 excluded).
 */
(function () {
  const params = new URLSearchParams(location.search);

  function formatTimer(totalSeconds) {
    const safe = Math.max(0, Math.floor(Number(totalSeconds) || 0));
    const m = Math.floor(safe / 60);
    const s = safe % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }

  function formatBid(value) {
    const n = Number(String(value).replace(/,/g, ""));
    return Math.floor(Number.isFinite(n) ? n : 0).toLocaleString("en-AE");
  }

  function applyPreviewScale() {
    // Scale the wrapper, NOT #stage, so stage CSS px stay 1920×1080
    // and overlays/canvases keep a stable local coordinate system.
    const scaler = document.getElementById("stage-scaler");
    const wrap = document.querySelector(".stage-scale");
    if (!scaler) return;
    const sx = window.innerWidth / 1920;
    const sy = window.innerHeight / 1080;
    const s = Math.min(1, sx, sy);
    scaler.style.width = "1920px";
    scaler.style.height = "1080px";
    scaler.style.transformOrigin = "top center";
    scaler.style.transform = s < 0.999 ? `scale(${s})` : "none";
    if (wrap) {
      wrap.style.height = `${Math.ceil(1080 * s)}px`;
      wrap.style.overflow = "hidden";
    }
  }

  function paintPersistent() {
    const state = window.H2V4State.getState();
    // Skip plate glyph rewrite while sequential Number Drop owns the digit spans
    if (!window.H2V4BeamDropFx?.isDropBusy?.()) {
      window.H2PlateSystem.renderPlate(state);
    }
    // Studio-refinement flag: keep plate force-hidden even after state paints
    window.H2V4DisplayConfig?.applyMainPlateVisibility?.();

    const bid = document.getElementById("bid-amount");
    const timer = document.getElementById("timer-value");
    const bar = document.getElementById("timer-bar");
    if (bid) bid.textContent = formatBid(state.price);
    if (timer) timer.textContent = formatTimer(state.timer_remaining_seconds);
    if (bar) {
      const total = Math.max(1, Number(state.timer_seconds) || 60);
      const rem = Math.max(0, Number(state.timer_remaining_seconds) || 0);
      bar.style.width = `${Math.max(0, Math.min(100, (rem / total) * 100))}%`;
    }

    const visible = state.new_style?.number_visible !== false;
    window.H2V4BeamDropFx?.applyNumberVisibility(visible);

    paintLiveText(state);
  }

  function paintLiveText(state) {
    const line1 = document.getElementById("live-text-line-1");
    const line2 = document.getElementById("live-text-line-2");
    const wrap = document.getElementById("live-screen-text");
    const t1 = String(state.live_text_line1 || "").trim();
    const t2 = String(state.live_text_line2 || "").trim();

    function setLine(el, text) {
      if (!el) return;
      // Plain text only — never HTML
      el.textContent = text;
      el.dir = "auto";
      if (text) {
        el.hidden = false;
        el.removeAttribute("hidden");
      } else {
        el.hidden = true;
        el.setAttribute("hidden", "");
      }
    }

    setLine(line1, t1);
    setLine(line2, t2);
    if (wrap) {
      wrap.setAttribute("aria-hidden", t1 || t2 ? "false" : "true");
      wrap.classList.toggle("has-text", !!(t1 || t2));
    }
  }

  function onEvent(kind, detail) {
    if (kind === "state" || kind === "lot_change") {
      paintPersistent();
      if (kind === "lot_change") {
        window.H2V4SoldFx?.clearSoldVisuals();
        window.H2V4BeamDropFx?.clearCardFx();
        window.H2V4AgingFx?.onPlateChange?.();
        window.H2V4Character?.reset?.();
      }
      return;
    }
    if (kind === "reveal") window.H2V4BeamDropFx?.playReveal();
    if (kind === "hide") window.H2V4BeamDropFx?.applyNumberVisibility(false);
    if (kind === "beam") window.H2V4BeamDropFx?.playBeam();
    if (kind === "drop") window.H2V4BeamDropFx?.playDrop();
    if (kind === "aging_reset") {
      window.H2V4AgingFx?.resetAging?.();
    }
    // aging_replay handled in state-controller via AgingFx directly
    if (kind === "char_point") window.H2V4Character?.play("point");
    if (kind === "char_yellow") window.H2V4Character?.play("yellow", { yellowRim: true });
    if (kind === "char_red") window.H2V4Character?.play("red", { redFx: true });
    if (kind === "char_sold_stamp") {
      // Prototype estimated contact cue drives imprint inside character timeline.
      // Skip duplicate sold path when character owns the stamp beat.
      window.H2V4Character?.play("sold_stamp", {
        soldStamp: true,
      });
    }
    if (kind === "sold") {
      // Immediate celebration — never wait on character WebM / busy lock
      window.H2V4SoldFx?.triggerSoldLocal({
        imprint: true,
        fireworks: true,
        shake: true,
        delayMs: 0,
      });
    }
  }

  function applyQueryOverrides() {
    const type = params.get("plate_type");
    const patch = {};
    if (type) patch.plate_type = type;
    if (params.get("code")) patch.code = params.get("code");
    if (params.get("number")) patch.number = params.get("number");
    if (params.get("phone")) patch.phone_number = params.get("phone");
    if (params.get("price")) patch.price = params.get("price");
    if (params.get("bg") === "1") {
      patch.new_style = {
        bg_motion_enabled: true,
        bg_motion_playing: true,
        bg_density: Number(params.get("bg_density") || 16) || 16,
        bg_speed: Number(params.get("bg_speed") || 0.65) || 0.65,
      };
    }
    if (Object.keys(patch).length) window.H2V4State.patch(patch);

    // Demo: enable aging and seek into a mid stage (does not auto-run from load otherwise)
    if (params.get("aging") === "1") {
      window.H2V4AgingFx?.enable?.();
      window.H2V4AgingFx?.setDuration?.(60);
      window.H2V4AgingFx?.seekProgress?.(54 / 60, { freeze: true });
    }
  }

  function wireQaHotkeys() {
    // Keyboard helpers for local QA only (not production OBS)
    window.addEventListener("keydown", (e) => {
      if (!e.altKey) return;
      const map = {
        b: { ns_beam: true },
        d: { ns_drop: true },
        r: { ns_replay_reveal: true },
        h: { ns_hide_number: true },
        y: { ns_char_yellow: true },
        e: { ns_char_red: true },
        p: { ns_char_point: true },
        s: { ns_char_sold_stamp: true },
        f: { trigger_sold: true, sold_style: "fireworks" },
        g: {
          new_style: {
            bg_motion_enabled: true,
            bg_motion_playing: true,
            bg_density: 16,
            bg_speed: 0.65,
          },
        },
      };
      const payload = map[e.key.toLowerCase()];
      if (payload) {
        e.preventDefault();
        window.H2V4State.patch(payload);
      }
    });
  }

  function isEmbedded() {
    try {
      return window.parent && window.parent !== window;
    } catch (e) {
      return true;
    }
  }

  function handleAdminCommand(data) {
    if (!data) return;
    if (data.type === "patch" && data.payload) {
      window.H2V4State.patch(data.payload);
    }
    if (data.type === "character" && data.action) {
      window.H2V4Character?.play?.(data.action, data.extras || {});
    }
    if (data.type === "characterReset") {
      window.H2V4Character?.reset?.();
    }
    if (data.type === "agingSeek" && data.progress != null) {
      window.H2V4AgingFx?.seekProgress?.(Number(data.progress), { freeze: true });
    }
  }

  function handleSyncCommand(msg) {
    if (!msg || msg.type !== "cmd") return;
    if (msg.cmd === "patch" && msg.payload) {
      window.H2V4State.patch(msg.payload);
      window.H2V4SyncBus?.publishStatus?.();
      return;
    }
    if (msg.cmd === "character" && msg.action) {
      window.H2V4Character?.play?.(msg.action, msg.extras || {});
      window.H2V4SyncBus?.publishStatus?.();
      return;
    }
    if (msg.cmd === "characterReset") {
      window.H2V4Character?.reset?.();
      window.H2V4SyncBus?.publishStatus?.();
      return;
    }
    if (msg.cmd === "agingSeek" && msg.progress != null) {
      window.H2V4AgingFx?.seekProgress?.(Number(msg.progress), { freeze: true });
      window.H2V4SyncBus?.publishStatus?.();
      return;
    }
    if (msg.cmd === "getStatus") {
      window.H2V4SyncBus?.publishStatus?.();
    }
  }

  function boot() {
    applyPreviewScale();
    window.addEventListener("resize", applyPreviewScale);

    // Temporary studio refinement flag (static/live_v4/js/display-config.js)
    window.H2V4DisplayConfig?.applyMainPlateVisibility?.();
    window.H2V4DisplayConfig?.watch?.();

    const djangoMode = !!(window.H2V4_DJANGO && window.H2V4_DJANGO.stateUrl);

    // Sandbox only: restore SyncBus snapshot. Django mode uses /live/api/state/.
    const hydrated = djangoMode
      ? null
      : window.H2V4SyncBus?.hydrateBroadcastFromSnapshot?.();

    window.H2V4State.subscribe(onEvent);
    if (!djangoMode) applyQueryOverrides();
    paintPersistent();
    window.H2V4DisplayConfig?.applyMainPlateVisibility?.();

    window.H2V4Timer?.boot?.();
    window.H2V4AgingFx?.start();
    // Restore aging after FX start so canvases exist
    if (hydrated?.ok) {
      window.H2V4SyncBus?.restoreAgingFromSnapshot?.(hydrated.snap);
    }
    window.H2V4BgPlatesFx?.start();
    window.H2V4Debug?.start();
    window.H2V4Character?.boot?.();
    window.H2V4Character?.probeAll?.();

    if (!djangoMode) wireQaHotkeys();

    // Parent admin panel (admin.html iframe) drives via postMessage
    window.addEventListener("message", (event) => {
      const data = event.data;
      if (!data || data.source !== "h2v4-admin") return;
      handleAdminCommand(data);
      if (data.type === "ping") {
        event.source?.postMessage(
          {
            source: "h2v4-preview",
            type: "pong",
            state: window.H2V4State.getState(),
            aging: window.H2V4AgingFx?.getStatus?.(),
            character: window.H2V4Character?.getHud?.(),
          },
          "*",
        );
      }
      if (data.type === "getCharacterHud") {
        event.source?.postMessage(
          {
            source: "h2v4-preview",
            type: "characterHud",
            character: window.H2V4Character?.getHud?.(),
          },
          "*",
        );
      }
      if (data.type === "getState") {
        event.source?.postMessage(
          {
            source: "h2v4-preview",
            type: "state",
            state: window.H2V4State.getState(),
            aging: window.H2V4AgingFx?.getStatus?.(),
            character: window.H2V4Character?.getHud?.(),
          },
          "*",
        );
      }
      if (data.type === "getAgingStatus") {
        event.source?.postMessage(
          { source: "h2v4-preview", type: "agingStatus", aging: window.H2V4AgingFx?.getStatus?.() },
          "*",
        );
      }
      if (data.type === "agingSeek" && data.progress != null) {
        event.source?.postMessage(
          { source: "h2v4-preview", type: "agingStatus", aging: window.H2V4AgingFx?.getStatus?.() },
          "*",
        );
      }
    });

    // Standalone control.html ↔ top-level broadcast (same browser profile)
    // Embedded iframe skips SyncBus command apply to avoid double-firing with postMessage.
    // Django production display uses django-bridge.js instead.
    if (!djangoMode && !isEmbedded()) {
      window.H2V4SyncBus?.subscribe?.((msg) => {
        if (msg?.role === "broadcast") return;
        handleSyncCommand(msg);
      });
    }

    window.H2V4State.subscribe((kind) => {
      if (window.parent && window.parent !== window) {
        window.parent.postMessage(
          { source: "h2v4-preview", type: "event", kind, state: window.H2V4State.getState() },
          "*",
        );
      }
      if (!djangoMode && !isEmbedded()) {
        window.H2V4SyncBus?.saveSnapshot?.();
        if (kind === "state" || kind === "lot_change" || kind === "sold") {
          window.H2V4SyncBus?.publishStatus?.();
        }
      }
    });

    // Expose frozen-compatible mock snapshot for legacy checks
    window.H2_LIVE_V4_MOCK = {
      get state() {
        return window.H2V4State.getState();
      },
    };

    document.dispatchEvent(new CustomEvent("h2v4:ready"));
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({ source: "h2v4-preview", type: "ready" }, "*");
    } else {
      window.H2V4SyncBus?.publishStatus?.();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
