/**
 * H2 Live V4 — sandbox admin panel.
 * Modes:
 *   iframe (admin.html)     → postMessage into preview iframe
 *   standalone (control.html) → H2V4SyncBus (BroadcastChannel + snapshot)
 *   django (Django /live/control/v4/) → H2V4DjangoBridge → /live/api/state/
 */
(function () {
  const rawMode = document.body?.dataset?.mode || "iframe";
  const mode = rawMode === "django" || rawMode === "standalone" ? rawMode : "iframe";
  const frame = document.getElementById("preview");
  const statusEl = document.getElementById("status");
  let debugOn = false;
  let ready = mode === "standalone" || mode === "django";

  function setStatus(html) {
    if (statusEl) statusEl.innerHTML = html;
  }

  function send(payload) {
    if (mode === "django") {
      const p = window.H2V4DjangoBridge?.sendPatch?.(payload);
      if (p && typeof p.then === "function") {
        return p.catch((e) => {
          setStatus(`خطأ في الواجهة البرمجية: ${e.message || e}`);
          throw e;
        });
      }
      return Promise.resolve();
    }
    if (mode === "standalone") {
      window.H2V4SyncBus?.sendPatch?.(payload);
      return Promise.resolve();
    }
    if (!frame?.contentWindow) return Promise.resolve();
    frame.contentWindow.postMessage({ source: "h2v4-admin", type: "patch", payload }, "*");
    return Promise.resolve();
  }

  function ping() {
    if (mode === "django") {
      window.H2V4DjangoBridge?.pollOnce?.();
      return;
    }
    if (mode === "standalone") {
      window.H2V4SyncBus?.requestStatus?.();
      return;
    }
    frame?.contentWindow?.postMessage({ source: "h2v4-admin", type: "ping" }, "*");
  }

  function requestAgingStatus() {
    if (mode === "django") {
      ping();
      return;
    }
    if (mode === "standalone") {
      window.H2V4SyncBus?.requestStatus?.();
      return;
    }
    frame?.contentWindow?.postMessage({ source: "h2v4-admin", type: "getAgingStatus" }, "*");
  }

  function requestCharacterHud() {
    if (mode === "django") return;
    if (mode === "standalone") {
      window.H2V4SyncBus?.requestStatus?.();
      return;
    }
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

  /** Prevents poll/status from wiping inputs during / right after a Live Text apply. */
  const liveTextHoldUntil = { line1: 0, line2: 0 };
  /** Typed-but-not-yet-applied text must not be clobbered by a poll between blur and Apply. */
  const liveTextDirty = { line1: false, line2: false };

  function syncLiveTextInputs(s) {
    if (!s) return;
    const now = Date.now();
    const i1 = document.getElementById("live-text-1");
    const i2 = document.getElementById("live-text-2");
    if (
      i1 &&
      document.activeElement !== i1 &&
      !liveTextDirty.line1 &&
      now >= liveTextHoldUntil.line1
    ) {
      i1.value = s.live_text_line1 || "";
    }
    if (
      i2 &&
      document.activeElement !== i2 &&
      !liveTextDirty.line2 &&
      now >= liveTextHoldUntil.line2
    ) {
      i2.value = s.live_text_line2 || "";
    }
  }

  function applyStatusFromState(s, aging, character, kind) {
    if (!s) return;
    ready = true;
    const remEl = document.getElementById("timer-remaining");
    if (remEl) remEl.value = String(s.timer_remaining_seconds ?? "");
    syncLiveTextInputs(s);
    if (aging) paintAgingHud(aging);
    if (character) paintCharHud(character);
    setStatus(
      `اللوحة <strong>${s.plate_type}|${s.code}|${s.number}|${s.phone_number || ""}</strong> · ` +
        `المؤقت <strong>${s.timer_remaining_seconds}ث</strong>${s.timer_active ? " ▶" : ""} · ` +
        `الرقم=${s.new_style?.number_visible !== false ? "ظاهر" : "مخفي"} · sold# ${s.sold_event_id}` +
        (kind ? ` · حدث <strong>${kind}</strong>` : "") +
        (mode === "standalone" ? " · مزامنة محلية" : ""),
    );
  }

  function hydrateFormFromSnapshot() {
    const snap = window.H2V4SyncBus?.loadSnapshot?.();
    const s = snap?.state;
    if (!s) return;
    const setVal = (id, v) => {
      const el = document.getElementById(id);
      if (el && v != null && document.activeElement !== el) el.value = String(v);
    };
    setVal("plate-type", s.plate_type);
    setVal("code", s.code);
    setVal("number", s.number);
    setVal("phone", s.phone_number);
    setVal("price", s.price);
    setVal("timer-seconds", s.timer_seconds);
    setVal("timer-remaining", s.timer_remaining_seconds);
    setVal("live-text-1", s.live_text_line1 || "");
    setVal("live-text-2", s.live_text_line2 || "");
    if (s.new_style) {
      if (s.new_style.bg_motion_enabled != null) {
        setVal("bg-motion", s.new_style.bg_motion_enabled ? "1" : "0");
      }
      if (s.new_style.bg_density != null) {
        const d = Number(s.new_style.bg_density);
        // Map legacy 8/16 (and bare level indices) onto Low/Med/High counts
        let dens = d;
        if (d === 8) dens = 15;
        else if (d === 16) dens = 25;
        else if (d > 0 && d <= 3) dens = d <= 1.25 ? 15 : d <= 2.25 ? 25 : 35;
        else if (![15, 25, 35].includes(d)) dens = 25;
        setVal("bg-density", dens);
      }
      if (s.new_style.bg_speed != null) setVal("bg-speed", s.new_style.bg_speed);
      if (s.new_style.character?.entry) setVal("char-entry", s.new_style.character.entry);
      if (s.new_style.character?.speed != null) setVal("char-speed", s.new_style.character.speed);
      if (s.new_style.aging?.total_duration_seconds != null) {
        setVal("aging-duration", s.new_style.aging.total_duration_seconds);
      }
      if (s.new_style.aging?.enabled != null) {
        setVal("aging-enabled", s.new_style.aging.enabled ? "1" : "0");
      }
    }
    if (snap.aging) paintAgingHud(snap.aging);
    setStatus("تمت استعادة اللقطة · بانتظار البث…");
  }

  function bind() {
    document.getElementById("btn-apply-lot")?.addEventListener("click", () => {
      send(collectLot());
      setStatus("تم تطبيق بيانات اللوحة");
    });

    function clampLiveText(v) {
      return String(v || "").slice(0, 100);
    }

    function readLiveTextValues() {
      const el1 = document.getElementById("live-text-1");
      const el2 = document.getElementById("live-text-2");
      const v1 = clampLiveText(el1?.value);
      const v2 = clampLiveText(el2?.value);
      if (el1) el1.value = v1;
      if (el2) el2.value = v2;
      return { v1, v2 };
    }

    function applyLiveTextLine(line) {
      const inputId = line === 1 ? "live-text-1" : "live-text-2";
      const key = line === 1 ? "live_text_line1" : "live_text_line2";
      const holdKey = line === 1 ? "line1" : "line2";
      const el = document.getElementById(inputId);
      const v = clampLiveText(el?.value);
      if (el) el.value = v;
      // Hold input against stale poll overwrite until PATCH settles (+ grace)
      liveTextHoldUntil[holdKey] = Date.now() + 2500;
      liveTextDirty[holdKey] = true;
      setStatus(v ? `جارٍ إرسال النص ${line}…` : `جارٍ مسح النص ${line}…`);
      return send({ [key]: v })
        .then(() => {
          liveTextDirty[holdKey] = false;
          liveTextHoldUntil[holdKey] = Date.now() + 1000;
          setStatus(v ? `تم تحديث النص ${line}` : `تم مسح النص ${line}`);
        })
        .catch(() => {
          liveTextHoldUntil[holdKey] = 0;
          // keep dirty so poll cannot wipe the typed value after a failed save
        });
    }

    function applyLiveTextBoth() {
      const { v1, v2 } = readLiveTextValues();
      liveTextHoldUntil.line1 = Date.now() + 2500;
      liveTextHoldUntil.line2 = Date.now() + 2500;
      liveTextDirty.line1 = true;
      liveTextDirty.line2 = true;
      setStatus("جارٍ إرسال النصّين معاً…");
      return send({ live_text_line1: v1, live_text_line2: v2 })
        .then(() => {
          liveTextDirty.line1 = false;
          liveTextDirty.line2 = false;
          liveTextHoldUntil.line1 = Date.now() + 1000;
          liveTextHoldUntil.line2 = Date.now() + 1000;
          setStatus("تم تحديث النص الأول والثاني");
        })
        .catch(() => {
          liveTextHoldUntil.line1 = 0;
          liveTextHoldUntil.line2 = 0;
        });
    }

    function clearLiveTextLine(line) {
      const inputId = line === 1 ? "live-text-1" : "live-text-2";
      const el = document.getElementById(inputId);
      if (el) el.value = "";
      return applyLiveTextLine(line);
    }

    function clearLiveTextBoth() {
      const el1 = document.getElementById("live-text-1");
      const el2 = document.getElementById("live-text-2");
      if (el1) el1.value = "";
      if (el2) el2.value = "";
      return applyLiveTextBoth();
    }

    document.getElementById("btn-live-text-1-apply")?.addEventListener("click", () => {
      applyLiveTextLine(1);
    });
    document.getElementById("btn-live-text-1-clear")?.addEventListener("click", () => {
      clearLiveTextLine(1);
    });
    document.getElementById("btn-live-text-2-apply")?.addEventListener("click", () => {
      applyLiveTextLine(2);
    });
    document.getElementById("btn-live-text-2-clear")?.addEventListener("click", () => {
      clearLiveTextLine(2);
    });
    document.getElementById("btn-live-text-apply-both")?.addEventListener("click", () => {
      applyLiveTextBoth();
    });
    document.getElementById("btn-live-text-clear-both")?.addEventListener("click", () => {
      clearLiveTextBoth();
    });

    // Mark dirty on type so a poll cannot wipe text after blur (before Apply click)
    document.getElementById("live-text-1")?.addEventListener("input", () => {
      liveTextDirty.line1 = true;
    });
    document.getElementById("live-text-2")?.addEventListener("input", () => {
      liveTextDirty.line2 = true;
    });

    // Enter in either textbox submits that line on the first keypress (no second Apply click)
    document.getElementById("live-text-1")?.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        applyLiveTextLine(1);
      }
    });
    document.getElementById("live-text-2")?.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        applyLiveTextLine(2);
      }
    });

    document.getElementById("btn-timer-duration")?.addEventListener("click", () => {
      send({ timer_seconds: Number(document.getElementById("timer-seconds").value) || 60 });
      setStatus("تم تحديد مدة المؤقت");
    });
    document.getElementById("btn-timer-start")?.addEventListener("click", () => {
      send({
        timer_seconds: Number(document.getElementById("timer-seconds").value) || 60,
        start_timer: true,
      });
      setStatus("بدأ المؤقت");
    });
    document.getElementById("btn-timer-pause")?.addEventListener("click", () => {
      send({ pause_timer: true });
      setStatus("تم إيقاف المؤقت مؤقتاً");
    });
    document.getElementById("btn-timer-resume")?.addEventListener("click", () => {
      send({ resume_timer: true });
      setStatus("تم استكمال المؤقت");
    });
    document.getElementById("btn-timer-reset")?.addEventListener("click", () => {
      send({ reset_timer: true });
      setStatus("تمت إعادة ضبط المؤقت");
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
        setStatus(`تم التنفيذ: <strong>${id.replace("btn-", "")}</strong>`);
      });
    });

    function charDirect(action, extras) {
      if (mode === "django") {
        // Character enter/exit/reset are display-local; Point/Yellow/Red/SOLD use API events.
        setStatus(`الشخصية ← ${action} (استخدم إشارة / صفراء / حمراء / SOLD لمزامنة OBS)`);
        return;
      }
      if (mode === "standalone") {
        window.H2V4SyncBus?.sendCharacter?.(action, extras || {});
      } else {
        frame?.contentWindow?.postMessage(
          { source: "h2v4-admin", type: "character", action, extras: extras || {} },
          "*",
        );
      }
      setStatus(`الشخصية ← ${action}`);
    }
    document.getElementById("btn-char-enter")?.addEventListener("click", () => {
      send(charPrefs());
      charDirect("enter");
    });
    document.getElementById("btn-char-exit")?.addEventListener("click", () => charDirect("exit"));
    document.getElementById("btn-char-reset")?.addEventListener("click", () => {
      if (mode === "django") {
        setStatus("إعادة ضبط الشخصية محلية على شاشة البث في وضع Django");
        return;
      }
      if (mode === "standalone") {
        window.H2V4SyncBus?.sendCharacterReset?.();
      } else {
        frame?.contentWindow?.postMessage({ source: "h2v4-admin", type: "characterReset" }, "*");
      }
      setStatus("تمت إعادة ضبط الشخصية");
    });

    document.getElementById("btn-sold")?.addEventListener("click", () => {
      send({
        trigger_sold: true,
        sold_style: "fireworks",
        sold_name: document.getElementById("sold-name").value,
      });
      setStatus("SOLD + الألعاب النارية");
    });

    // --- Independent Plate Aging controls (dev panel; outside OBS stage) ---
    document.getElementById("aging-enabled")?.addEventListener("change", () => {
      const on = document.getElementById("aging-enabled").value === "1";
      send(on ? { aging_enable: true } : { aging_disable: true });
      setStatus(on ? "التقادم مفعّل (بانتظار البدء)" : "التقادم معطّل → سليمة");
      requestAgingStatus();
    });
    document.getElementById("aging-preset")?.addEventListener("change", () => {
      const v = Number(document.getElementById("aging-preset").value) || 60;
      document.getElementById("aging-duration").value = String(v);
    });
    document.getElementById("btn-aging-apply-duration")?.addEventListener("click", () => {
      const sec = Number(document.getElementById("aging-duration").value) || 60;
      send({ aging_duration_seconds: sec });
      setStatus(`مدة التقادم ← <strong>${sec}ث</strong>`);
      requestAgingStatus();
    });
    document.getElementById("btn-aging-start")?.addEventListener("click", () => {
      document.getElementById("aging-enabled").value = "1";
      send({
        aging_enable: true,
        aging_duration_seconds: Number(document.getElementById("aging-duration").value) || 60,
        aging_start: true,
      });
      setStatus("بدء التقادم");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-pause")?.addEventListener("click", () => {
      send({ aging_pause: true });
      setStatus("إيقاف التقادم مؤقتاً");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-resume")?.addEventListener("click", () => {
      send({ aging_resume: true });
      setStatus("استكمال التقادم");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-reset")?.addEventListener("click", () => {
      send({ aging_reset: true });
      setStatus("إعادة ضبط التقادم → سليمة");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-replay")?.addEventListener("click", () => {
      document.getElementById("aging-enabled").value = "1";
      send({ ns_aging_replay: true });
      setStatus("إعادة تشغيل التقادم من البداية");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-disable")?.addEventListener("click", () => {
      document.getElementById("aging-enabled").value = "0";
      send({ aging_disable: true });
      setStatus("تم تعطيل التقادم → سليمة");
      requestAgingStatus();
    });
    document.getElementById("btn-aging-seek")?.addEventListener("click", () => {
      const p = document.getElementById("aging-seek").value;
      if (p === "") return;
      document.getElementById("aging-enabled").value = "1";
      send({ aging_enable: true });
      if (mode === "django") {
        setStatus("انتقال المرحلة متاح في وضع التجربة فقط؛ استخدم البدء / المدة في Django");
        return;
      }
      if (mode === "standalone") {
        window.H2V4SyncBus?.sendAgingSeek?.(Number(p));
      } else {
        frame?.contentWindow?.postMessage(
          { source: "h2v4-admin", type: "agingSeek", progress: Number(p) },
          "*",
        );
      }
      setStatus(`انتقال التقادم ← ${(Number(p) * 100).toFixed(1)}%`);
    });

    document.getElementById("btn-bg-apply")?.addEventListener("click", () => {
      const enabled = document.getElementById("bg-motion").value === "1";
      send({
        new_style: {
          bg_motion_enabled: enabled,
          bg_motion_playing: enabled,
          bg_density: Number(document.getElementById("bg-density").value) || 25,
          bg_speed: Number(document.getElementById("bg-speed").value) || 0.65,
        },
      });
      setStatus(enabled ? "تم تفعيل اللوحات المتحركة" : "تم إيقاف اللوحات المتحركة");
    });
    document.getElementById("btn-bg-start")?.addEventListener("click", () => {
      document.getElementById("bg-motion").value = "1";
      send({
        new_style: {
          bg_motion_enabled: true,
          bg_motion_playing: true,
          bg_density: Number(document.getElementById("bg-density").value) || 25,
          bg_speed: Number(document.getElementById("bg-speed").value) || 0.65,
        },
      });
      setStatus("تم تشغيل اللوحات المتحركة");
    });
    document.getElementById("btn-bg-stop")?.addEventListener("click", () => {
      send({
        new_style: {
          bg_motion_playing: false,
        },
      });
      setStatus("تم إيقاف اللوحات المتحركة (تجميد)");
    });

    document.getElementById("btn-reload")?.addEventListener("click", () => {
      if (mode === "django") {
        const url = window.H2V4_DJANGO?.displayUrl;
        if (url) window.open(url, "h2v4_broadcast");
        setStatus("تم فتح شاشة البث V4");
        ping();
        return;
      }
      if (mode === "standalone") {
        window.open("./index.html", "h2v4_broadcast");
        setStatus("تم فتح / تركيز شاشة البث");
        ping();
        return;
      }
      ready = false;
      const q = debugOn ? "?embed=1&debug=1" : "?embed=1";
      frame.src = `./index.html${q}&t=${Date.now()}`;
      setStatus("جارٍ إعادة تحميل المعاينة…");
    });

    document.getElementById("btn-debug")?.addEventListener("click", () => {
      if (mode === "django") {
        const url = window.H2V4_DJANGO?.displayUrl;
        if (url) window.open(url + (url.includes("?") ? "&" : "?") + "debug=1", "h2v4_broadcast_debug");
        setStatus("تم فتح البث مع أدوات التشخيص");
        return;
      }
      if (mode === "standalone") {
        window.open("./index.html?debug=1", "h2v4_broadcast_debug");
        setStatus("تم فتح البث مع طبقة التشخيص");
        return;
      }
      debugOn = !debugOn;
      ready = false;
      frame.src = `./index.html?embed=1${debugOn ? "&debug=1" : ""}&t=${Date.now()}`;
      setStatus(debugOn ? "طبقة التشخيص مفعّلة" : "طبقة التشخيص معطّلة");
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
    if (mode !== "iframe") return;
    const data = event.data;
    if (!data || data.source !== "h2v4-preview") return;
    if (data.aging) paintAgingHud(data.aging);
    if (data.character) paintCharHud(data.character);
    if (data.type === "agingStatus" && data.aging) paintAgingHud(data.aging);
    if (data.type === "characterHud" && data.character) paintCharHud(data.character);

    if (data.type === "ready" || data.type === "pong") {
      ready = true;
      const s = data.state;
      if (s) {
        applyStatusFromState(s, data.aging, data.character);
      } else {
        setStatus("المعاينة جاهزة");
        ping();
      }
    }
    if (data.type === "state" || data.type === "event") {
      applyStatusFromState(data.state, data.aging, data.character, data.kind);
    }
  });

  if (mode === "standalone") {
    window.H2V4SyncBus?.subscribe?.((msg) => {
      if (!msg || msg.type !== "status") return;
      applyStatusFromState(msg.state, msg.aging, msg.character);
    });
  }

  if (mode === "django") {
    window.addEventListener("h2v4:django-state", (ev) => {
      const s = ev.detail;
      if (!s) return;
      applyStatusFromState(s, s.new_style?.aging || null, null);
      paintAgingHud({
        enabled: !!s.new_style?.aging?.enabled,
        running: !!s.new_style?.aging?.running,
        paused: !!s.new_style?.aging?.paused,
        completed: !!s.new_style?.aging?.completed,
        progress: 0,
        stage_label: s.new_style?.aging?.enabled ? "ON" : "OFF",
        elapsed_seconds: (s.new_style?.aging?.elapsed_ms || 0) / 1000,
        total_duration_seconds: s.new_style?.aging?.total_duration_seconds || 60,
      });
    });
  }

  bind();

  if (mode === "django") {
    ping();
    setStatus("لوحة تحكم Django V4 · مزامنة عبر /live/api/state/");
  } else if (mode === "standalone") {
    hydrateFormFromSnapshot();
    ping();
    setStatus(
      "تحكم مستقل · افتح شاشة البث بشكل منفصل · " +
        (window.H2V4SyncBus?.HAS_BROADCAST_CHANNEL
          ? "قناة المزامنة جاهزة"
          : "احتياطي تخزين محلي"),
    );
  } else {
    frame?.addEventListener("load", () => {
      setTimeout(ping, 400);
    });
  }

  // Live aging + character HUD (dev panel only — never on OBS stage)
  window.setInterval(() => {
    if (!ready) return;
    requestAgingStatus();
    requestCharacterHud();
  }, 250);
})();
