/**
 * H2 Live V4 — visual debug overlay (?debug=1).
 * Positions use stage-local CSS px via H2V4Geom (correct under preview scale).
 */
(function (global) {
  const params = new URLSearchParams(location.search);
  const enabled = params.get("debug") === "1";

  function boxFromStage(label, stageBox, color) {
    if (!stageBox) return "";
    return `<div class="dbg-box" data-dbg="${label}" style="left:${stageBox.x}px;top:${stageBox.y}px;width:${stageBox.w}px;height:${stageBox.h}px;border-color:${color}">
      <span>${label}</span>
    </div>`;
  }

  function draw() {
    const root = document.getElementById("debug-overlay");
    if (!root || !enabled) return;
    root.hidden = false;
    root.setAttribute("aria-hidden", "false");

    const Geom = global.H2V4Geom;
    if (!Geom) return;

    const state = global.H2V4State?.getState?.() || {};
    const type = state.plate_type || "dubai";
    const geo = global.H2PlateSystem?.getGeometry(type) || {};
    const shell = document.getElementById("plate-shell");
    const timer = document.querySelector(".timer");
    const bid = document.querySelector(".bid");
    const brand = document.querySelector(".brand");
    const char = document.getElementById("character");
    const plate = document.getElementById("plate");
    const codeEl = document.getElementById("plate-code");
    const numberEl = document.getElementById("plate-number");
    const phoneEl = document.getElementById("plate-phone");

    let html = "";
    html += boxFromStage("timer", Geom.elementStageBox(timer), "#4ade80");
    html += boxFromStage("bid", Geom.elementStageBox(bid), "#60a5fa");
    html += boxFromStage("brand", Geom.elementStageBox(brand), "#f472b6");
    html += boxFromStage("plate", Geom.elementStageBox(plate), "#facc15");
    html += boxFromStage("shell", Geom.elementStageBox(shell), "#fde047");
    html += boxFromStage("char", Geom.elementStageBox(char), "#fb923c");
    const rim = document.getElementById("plate-rim");
    if (rim && rim.getAttribute("aria-hidden") !== "true") {
      html += boxFromStage("rim", Geom.elementStageBox(rim), "#f97316");
    }
    const spr = document.getElementById("character-sprite");
    if (spr && !spr.hidden) {
      html += boxFromStage("char-sprite", Geom.elementStageBox(spr), "#fdba74");
    }

    // Character anchors (stage CSS px)
    const anch = global.H2V4Character?.getAnchorsLive?.();
    if (anch) {
      const dot = (label, p, color) => {
        if (!p || p.x == null) return "";
        return `<div class="dbg-anchor" data-dbg="${label}" style="left:${p.x}px;top:${p.y}px;background:${color}" title="${label}"></div>`;
      };
      html += dot("entry", anch.entryFeet, "#22c55e");
      html += dot("stop", anch.stopFeet, "#eab308");
      html += dot("exit", anch.exitFeet, "#ef4444");
      html += dot("feet", anch.feetNow, "#fb923c");
      html += dot("gesture", anch.gestureTarget, "#a78bfa");
      if (anch.entryFeet && anch.stopFeet) {
        html += `<svg class="dbg-path" width="1920" height="1080" style="position:absolute;left:0;top:0;pointer-events:none;z-index:1">
          <line x1="${anch.entryFeet.x}" y1="${anch.entryFeet.y}" x2="${anch.stopFeet.x}" y2="${anch.stopFeet.y}" stroke="#86efac" stroke-width="2" stroke-dasharray="8 6"/>
        </svg>`;
      }
    }

    // Live overlay element boxes (actual rendered text regions)
    if (codeEl && !codeEl.hidden) {
      html += boxFromStage("code-el", Geom.elementStageBox(codeEl), "#e879f9");
    }
    if (numberEl && !numberEl.hidden) {
      html += boxFromStage("number-el", Geom.elementStageBox(numberEl), "#22d3ee");
    }
    if (phoneEl && !phoneEl.hidden) {
      html += boxFromStage("phone-el", Geom.elementStageBox(phoneEl), "#a3e635");
    }

    // Registry %-boxes mapped through shell's stage-local box
    if (shell && geo) {
      const shellBox = Geom.elementStageBox(shell);
      const paintReg = (name, b, color) => {
        if (!b || !shellBox) return "";
        const box = {
          x: shellBox.x + (shellBox.w * b.left) / 100,
          y: shellBox.y + (shellBox.h * b.top) / 100,
          w: (shellBox.w * b.width) / 100,
          h: (shellBox.h * b.height) / 100,
        };
        return boxFromStage(name, box, color);
      };
      html += paintReg("code-reg", geo.codeBox, "rgba(232,121,249,0.55)");
      html += paintReg("number-reg", geo.numberBox, "rgba(34,211,238,0.55)");
      html += paintReg("phone-reg", geo.phoneBox, "rgba(163,230,53,0.55)");
      const stamp = global.H2PlateSystem.getStampTarget(type);
      const sx = shellBox.x + shellBox.w * stamp.x;
      const sy = shellBox.y + shellBox.h * stamp.y;
      html += `<div class="dbg-anchor" data-dbg="stamp" style="left:${sx}px;top:${sy}px" title="stampTarget"></div>`;
    }

    document.querySelectorAll(".safezone").forEach((el, i) => {
      html += boxFromStage(`safe-${i ? "R" : "L"}`, Geom.elementStageBox(el), "rgba(255,255,255,0.35)");
    });

    const identity = global.H2V4State?.plateIdentity?.() || "";
    const scale = Geom.getStageScale().toFixed(3);
    const rem = global.H2V4Timer?.computeRemaining?.(state) ?? state.timer_remaining_seconds;
    const ag = global.H2V4AgingFx?.getStatus?.();
    const agTxt = ag
      ? `aging=${ag.enabled ? "on" : "off"} ${ag.stage}@${(ag.progress || 0).toFixed(2)}`
      : "aging=?";
    html += `<div class="dbg-hud">type=${type} | lot=${identity} | scale=${scale} | timer=${rem}s active=${!!state.timer_active} | ${agTxt}</div>`;

    root.innerHTML = html;
  }

  /**
   * Measure max px error between a debug box and its live element.
   */
  function measureAlignment() {
    const Geom = global.H2V4Geom;
    const root = document.getElementById("debug-overlay");
    if (!Geom || !root) return {};
    const pairs = [
      ["timer", ".timer"],
      ["bid", ".bid"],
      ["brand", ".brand"],
      ["plate", "#plate"],
    ];
    const out = {};
    pairs.forEach(([name, sel]) => {
      const el = document.querySelector(sel);
      const dbg = root.querySelector(`[data-dbg="${name}"]`);
      if (!el || !dbg) {
        out[name] = { errorPx: null, missing: true };
        return;
      }
      const live = Geom.elementStageBox(el);
      const drawn = {
        x: parseFloat(dbg.style.left) || 0,
        y: parseFloat(dbg.style.top) || 0,
        w: parseFloat(dbg.style.width) || 0,
        h: parseFloat(dbg.style.height) || 0,
      };
      out[name] = {
        errorPx: Geom.boxError(live, drawn),
        live,
        drawn,
      };
    });
    return out;
  }

  function start() {
    if (!enabled) {
      const root = document.getElementById("debug-overlay");
      if (root) {
        root.hidden = true;
        root.setAttribute("aria-hidden", "true");
      }
      return;
    }
    document.body.classList.add("debug-on");
    draw();
    setInterval(draw, 250);
  }

  global.H2V4Debug = { enabled, draw, start, measureAlignment };
})(window);
