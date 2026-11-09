/**
 * H2 Live V4 — sandbox admin panel.
 * Drives the preview iframe via postMessage → H2V4State.patch.
 */
(function () {
  const frame = document.getElementById("preview");
  const statusEl = document.getElementById("status");
  let debugOn = false;
  let ready = false;

  function setStatus(html) {
    if (statusEl) statusEl.innerHTML = html;
  }

  function send(payload) {
    if (!frame?.contentWindow) return;
    frame.contentWindow.postMessage({ source: "h2v4-admin", type: "patch", payload }, "*");
  }

  function ping() {
    frame?.contentWindow?.postMessage({ source: "h2v4-admin", type: "ping" }, "*");
  }

  function requestAgingStatus() {
    frame?.contentWindow?.postMessage({ source: "h2v4-admin", type: "getAgingStatus" }, "*");
  }

  function requestCharacterHud() {
    frame?.contentWindow?.postMessage({ source: "h2v4-admin", type: "getCharacterHud" }, "*");
  }

  function paintCharHud(h) {
    if (!h) return;
    const set = (id, v) => {
      const el = document.getElementById(id);
      if (el) el.textContent = v;
    };
    set("char-hud-state", h.state || "IDLE");
    set("char-hud-action", h.action || "—");
    set(
      "char-hud-asset",
      h.loadedAsset?.action
        ? `${h.loadedAsset.action} (${h.loadedAsset.quality || "?"})`
        : "—",
    );
    set("char-hud-tier", h.tier || "—");
    set("char-hud-cues", h.cueStatus || "none");
    set("char-hud-busy", h.busy ? "yes" : "no");
    set("char-hud-error", h.error || "—");
  }

  function paintAgingHud(a) {
    if (!a) return;
    const stateEl = document.getElementById("aging-hud-state");
    const stageEl = document.getElementById("aging-hud-stage");
    const progEl = document.getElementById("aging-hud-progress");
    const elEl = document.getElementById("aging-hud-elapsed");
    if (!stateEl) return;
    let label = "OFF";
    if (a.enabled) {
      if (a.completed) label = "COMPLETE (frozen)";
      else if (!a.running) label = "ON · idle";
      else if (a.paused) label = "PAUSED";
      else label = "RUNNING";
    }
    stateEl.textContent = label;
    if (stageEl) stageEl.textContent = a.enabled ? `${a.stage_label || a.stage}` : "—";
    if (progEl) progEl.textContent = `${((a.progress || 0) * 100).toFixed(1)}%`;
    if (elEl) {
      const tot = a.total_duration_seconds || 60;
      elEl.textContent = `${(a.elapsed_seconds || 0).toFixed(1)}s / ${tot}s`;
    }
    const en = document.getElementById("aging-enabled");
    if (en && document.activeElement !== en) en.value = a.enabled ? "1" : "0";
  }

  function collectLot() {
    return {
      plate_type: document.getElementById("plate-type").value,
      code: document.getElementById("code").value,
      number: document.getElementById("number").value,
      phone_number: document.getElementById("phone").value,
      price: document.getElementById("price").value,
    };
  }

  function charPrefs() {
    return {
      new_style: {
        character: {
          entry: document.getElementById("char-entry").value,
          speed: Number(document.getElementById("char-speed").value) || 1,
        },
      },
    };
  }

  function bind() {
    document.getElementById("btn-apply-lot")?.addEventListener("click", () => {
      send(collectLot());
      setStatus("Applied lot / plate fields");
    });

    function clampLiveText(v) {
      return String(v || "").slice(0, 100);
    }

    document.getElementById("btn-live-text-1-apply")?.addEventListener("click", () => {
      const v = clampLiveText(document.getElementById("live-text-1")?.value);
      send({ live_text_line1: v });
      setStatus(v ? "Live Text Line 1 updated" : "Live Text Line 1 cleared");
    });
    document.getElementById("btn-live-text-1-clear")?.addEventListener("click", () => {
      const el = document.getElementById("live-text-1");
      if (el) el.value = "";
      send({ live_text_line1: "" });
      setStatus("Live Text Line 1 cleared");
    });
    document.getElementById("btn-live-text-2-apply")?.addEventListener("click", () => {
      const v = clampLiveText(document.getElementById("live-text-2")?.value);
      send({ live_text_line2: v });
      setStatus(v ? "Live Text Line 2 updated" : "Live Text Line 2 cleared");
    });
    document.getElementById("btn-live-text-2-clear")?.addEventListener("click", () => {
      const el = document.getElementById("live-text-2");
      if (el) el.value = "";
      send({ live_text_line2: "" });
      setStatus("Live Text Line 2 cleared");
    });

    document.getElementById("btn-timer-duration")?.addEventListener("click", () => {
      send({ timer_seconds: Number(document.getElementById("timer-seconds").value) || 60 });
      setStatus("Timer duration set");
    });
    document.getElementById("btn-timer-start")?.addEventListener("click", () => {
      send({
        timer_seconds: Number(document.getElementById("timer-seconds").value) || 60,
        start_timer: true,
      });
      setStatus("Timer started");
    });
    document.getElementById("btn-timer-pause")?.addEventListener("click", () => {
      send({ pause_timer: true });
      setStatus("Timer paused");
    });
    document.getElementById("btn-timer-resume")?.addEventListener("click", () => {
      send({ resume_timer: true });
      setStatus("Timer resumed");
    });
    document.getElementById("btn-timer-reset")?.addEventListener("click", () => {
      send({ reset_timer: true });
      setStatus("Timer reset");
    });

    const map = [
      ["btn-show", { ns_show_number: true }],
      ["btn-hide", { ns_hide_number: true }],
      ["btn-reveal", { ns_replay_reveal: true }],
      ["btn-beam", { ns_beam: true }],
      ["btn-drop", { ns_drop: true }],
      ["btn-point", () => ({ ns_char_point: true, ...charPrefs() })],
      ["btn-yellow", () => ({ ns_char_yellow: true, ...charPrefs() })],
      ["btn-red", () => ({ ns_char_red: true, ...charPrefs() })],
      ["btn-sold-stamp", () => ({ ns_char_sold_stamp: true, ...charPrefs() })],
    ];
    map.forEach(([id, payload]) => {
      document.getElementById(id)?.addEventListener("click", () => {
        send(typeof payload === "function" ? payload() : payload);
        setStatus(`Triggered <strong>${id.replace("btn-", "")}</strong>`);
      });
    });

    function charDirect(action, extras) {
      frame?.contentWindow?.postMessage(
        { source: "h2v4-admin", type: "character", action, extras: extras || {} },
        "*",
      );
      setStatus(`Character → ${action}`);
    }
    document.getElementById("btn-char-enter")?.addEventListener("click", () => {
      send(charPrefs());
      charDirect("enter");
    });
    document.getElementById("btn-char-exit")?.addEventListener("click", () => charDirect("exit"));
    document.getElementById("btn-char-reset")?.addEventListener("click", () => {
      frame?.contentWindow?.postMessage({ source: "h2v4-admin", type: "characterReset" }, "*");
      setStatus("Character reset");
    });

    document.getElementById("btn-sold")?.addEventListener("click", () => {
      send({
        trigger_sold: true,
        sold_style: "fireworks",
        sold_name: document.getElementById("sold-name").value,
      });
      setStatus("SOLD + fireworks");
    });

    // --- Independent Plate Aging controls (dev panel; outside OBS stage) ---
    document.getElementById("aging-enabled")?.addEventListener("change", () => {
      const on = document.getElementById("aging-enabled").value === "1";
      send(on ? { aging_enable: true } : { aging_disable: true });
      setStatus(on ? "Aging ENABLED (idle until Start)" : "Aging DISABLED → pristine");
      requestAgingStatus();
    });
    document.getElementById("aging-preset")?.addEventListener("change", () => {
      const v = Number(document.getElementById("aging-preset").value) || 60;
      document.getElementById("aging-duration").value = String(v);
    });
    document.getElementById("btn-aging-apply-duration")?.addEventListener("click", () => {
      const sec = Number(document.getElementById("aging-duration").value) || 60;
      send({ aging_duration_seconds: sec });
      setStatus(`Aging duration → <strong>${sec}s</strong>`);
      requestAgingStatus();
    });
    document.getElementById("btn-aging-start")?.addEventListener("click", () => {
      document.getElementById("aging-enabled").value = "1";
      send({ aging_enable: true, aging_duration_seconds: Number(document.getElementById("aging-duration").value) || 60, aging_start: true });
      setStatus("Aging Start");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-pause")?.addEventListener("click", () => {
      send({ aging_pause: true });
      setStatus("Aging Pause");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-resume")?.addEventListener("click", () => {
      send({ aging_resume: true });
      setStatus("Aging Resume");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-reset")?.addEventListener("click", () => {
      send({ aging_reset: true });
      setStatus("Aging Reset → pristine");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-replay")?.addEventListener("click", () => {
      document.getElementById("aging-enabled").value = "1";
      send({ ns_aging_replay: true });
      setStatus("Aging Replay from pristine");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-disable")?.addEventListener("click", () => {
      document.getElementById("aging-enabled").value = "0";
      send({ aging_disable: true });
      setStatus("Aging disabled → pristine");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-seek")?.addEventListener("click", () => {
      const p = document.getElementById("aging-seek").value;
      if (p === "") return;
      document.getElementById("aging-enabled").value = "1";
      send({ aging_enable: true });
      frame?.contentWindow?.postMessage(
        { source: "h2v4-admin", type: "agingSeek", progress: Number(p) },
        "*",
      );
      setStatus(`Aging seek → ${(Number(p) * 100).toFixed(1)}%`);
    });

    document.getElementById("btn-bg-apply")?.addEventListener("click", () => {
      const enabled = document.getElementById("bg-motion").value === "1";
      send({
        new_style: {
          bg_motion_enabled: enabled,
          bg_motion_playing: enabled,
          bg_density: Number(document.getElementById("bg-density").value) || 16,
          bg_speed: Number(document.getElementById("bg-speed").value) || 0.65,
        },
      });
      setStatus(enabled ? "Ambient floats enabled" : "Ambient floats disabled");
    });
    document.getElementById("btn-bg-start")?.addEventListener("click", () => {
      document.getElementById("bg-motion").value = "1";
      send({
        new_style: {
          bg_motion_enabled: true,
          bg_motion_playing: true,
          bg_density: Number(document.getElementById("bg-density").value) || 16,
          bg_speed: Number(document.getElementById("bg-speed").value) || 0.65,
        },
      });
      setStatus("Ambient floats started");
    });
    document.getElementById("btn-bg-stop")?.addEventListener("click", () => {
      send({
        new_style: {
          bg_motion_playing: false,
        },
      });
      setStatus("Ambient floats stopped (frozen)");
    });

    document.getElementById("btn-reload")?.addEventListener("click", () => {
      ready = false;
      const q = debugOn ? "?embed=1&debug=1" : "?embed=1";
      frame.src = `./index.html${q}&t=${Date.now()}`;
      setStatus("Reloading preview…");
    });

    document.getElementById("btn-debug")?.addEventListener("click", () => {
      debugOn = !debugOn;
      ready = false;
      frame.src = `./index.html?embed=1${debugOn ? "&debug=1" : ""}&t=${Date.now()}`;
      setStatus(debugOn ? "Debug overlay ON" : "Debug overlay OFF");
    });

    // Live sync when plate type changes to phone → hint phone field
    document.getElementById("plate-type")?.addEventListener("change", () => {
      const t = document.getElementById("plate-type").value;
      if ((t === "du" || t === "etisalat") && !document.getElementById("phone").value) {
        document.getElementById("phone").value = "0501234567";
      }
    });
  }

  window.addEventListener("message", (event) => {
    const data = event.data;
    if (!data || data.source !== "h2v4-preview") return;
    if (data.aging) paintAgingHud(data.aging);
    if (data.character) paintCharHud(data.character);
    if (data.type === "agingStatus" && data.aging) paintAgingHud(data.aging);
    if (data.type === "characterHud" && data.character) paintCharHud(data.character);
    function syncLiveTextInputs(s) {
      if (!s) return;
      const i1 = document.getElementById("live-text-1");
      const i2 = document.getElementById("live-text-2");
      if (i1 && document.activeElement !== i1) i1.value = s.live_text_line1 || "";
      if (i2 && document.activeElement !== i2) i2.value = s.live_text_line2 || "";
    }

    if (data.type === "ready" || data.type === "pong") {
      ready = true;
      const s = data.state;
      if (s) {
        syncLiveTextInputs(s);
        setStatus(
          `Preview ready · lot <strong>${s.plate_type}|${s.code}|${s.number}|${s.phone_number || ""}</strong> · sold# ${s.sold_event_id}`,
        );
      } else {
        setStatus("Preview ready");
        ping();
      }
      if (data.aging) paintAgingHud(data.aging);
      if (data.character) paintCharHud(data.character);
    }
    if (data.type === "state" || data.type === "event") {
      const s = data.state;
      if (!s) return;
      const remEl = document.getElementById("timer-remaining");
      if (remEl) remEl.value = String(s.timer_remaining_seconds ?? "");
      syncLiveTextInputs(s);
      setStatus(
        `lot <strong>${s.plate_type}|${s.code}|${s.number}|${s.phone_number || ""}</strong> · ` +
          `timer <strong>${s.timer_remaining_seconds}s</strong>${s.timer_active ? " ▶" : ""} · ` +
          `visible=${s.new_style?.number_visible !== false} · sold# ${s.sold_event_id}` +
          (data.kind ? ` · event <strong>${data.kind}</strong>` : ""),
      );
    }
  });

  bind();
  frame?.addEventListener("load", () => {
    setTimeout(ping, 400);
  });
  // Live aging + character HUD (dev panel only — never on OBS stage)
  window.setInterval(() => {
    if (!ready) return;
    requestAgingStatus();
    requestCharacterHud();
  }, 250);
})();
