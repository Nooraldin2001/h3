/**
 * H2 Live V4 — light beam orbit + number reveal/drop (plate-local).
 * Number Drop = sequential digit-by-digit downward fall (not simultaneous).
 */
(function (global) {
  let dropBusy = false;
  let dropCleanupTimer = 0;
  /** Per-digit stagger timeouts — cleared on cancel so timers never accumulate. */
  let dropStaggerTimers = [];
  /** Text captured when a drop sequence starts (restore on cancel / finish). */
  let dropOriginalText = "";
  /** Bumped to invalidate in-flight drop completion callbacks (lot change / cancel). */
  let dropGen = 0;

  /** Timing: cinematic cascade (overlap OK; starts must be clearly staggered). */
  const DROP_FALL_MS = 650;
  const DROP_STAGGER_MS = 260;
  const DROP_FALL_DIST = 360;

  function contentEl() {
    const state = global.H2V4State?.getState?.() || {};
    const type = state.plate_type || "dubai";
    if (global.H2PlateSystem?.isPhone(type)) {
      return document.getElementById("plate-phone");
    }
    return document.getElementById("plate-number");
  }

  /**
   * Hide/show registration digits (or phone) only.
   * Final hidden state = clean plate art — no blur, smear, or dark censor mask.
   * Stored state values are untouched (caller owns new_style.number_visible).
   */
  function applyNumberVisibility(visible) {
    // While Number Drop owns digit spans, do not yank opacity (breaks sequential fall).
    // cancelDrop / finishDropHidden clear dropBusy before the final hide/show.
    if (dropBusy) return;

    const el = contentEl();
    const conceal = document.getElementById("plate-red-conceal");

    if (conceal) {
      conceal.classList.remove("active");
      conceal.hidden = true;
      conceal.setAttribute("aria-hidden", "true");
      conceal.style.opacity = "0";
    }

    if (!el) return;

    el.classList.remove("is-hidden");
    if (visible) {
      el.style.visibility = "visible";
      el.style.opacity = "1";
      el.setAttribute("aria-hidden", "false");
    } else {
      el.style.opacity = "0";
      el.style.visibility = "hidden";
      el.classList.add("is-hidden");
      el.setAttribute("aria-hidden", "true");
    }
  }

  function playReveal() {
    applyNumberVisibility(true);
    const el = contentEl();
    const reveal = document.getElementById("plate-reveal");
    const state = global.H2V4State?.getState?.();
    const type = state?.plate_type || "dubai";
    const box = global.H2PlateSystem?.getPrimaryContentBox(type);
    if (reveal && box) {
      reveal.style.top = `${box.top}%`;
      reveal.style.left = `${box.left}%`;
      reveal.style.width = `${box.width}%`;
      reveal.style.height = `${box.height}%`;
      reveal.classList.remove("play");
      void reveal.offsetWidth;
      reveal.classList.add("play");
      setTimeout(() => reveal.classList.remove("play"), 900);
    }
    if (el) {
      el.classList.remove("reveal-pop");
      void el.offsetWidth;
      el.classList.add("reveal-pop");
      setTimeout(() => el.classList.remove("reveal-pop"), 700);
    }
  }

  function playBeam() {
    const beam = document.getElementById("plate-beam");
    if (!beam) return;
    beam.classList.remove("orbit");
    void beam.offsetWidth;
    beam.classList.add("orbit");
    beam.setAttribute("aria-hidden", "false");
    setTimeout(() => {
      beam.classList.remove("orbit");
      beam.setAttribute("aria-hidden", "true");
    }, 2200);
  }

  function clearFallLayer() {
    document.querySelectorAll(".plate-digit-fall").forEach((n) => n.remove());
  }

  function clearDropStaggerTimers() {
    dropStaggerTimers.forEach((id) => clearTimeout(id));
    dropStaggerTimers = [];
    if (dropCleanupTimer) {
      clearTimeout(dropCleanupTimer);
      dropCleanupTimer = 0;
    }
  }

  function restorePlainText(el, text, opts) {
    if (!el) return;
    const keepHidden = !!(opts && opts.keepHidden);
    el.style.display = "";
    el.style.textAlign = "";
    if (!keepHidden) {
      el.style.visibility = "";
      el.style.opacity = "";
    }
    el.classList.remove("is-dropping");
    // Prefer plate-system glyphs so Show Number / paint match resting typography
    const state = global.H2V4State?.getState?.();
    const type = state?.plate_type || "dubai";
    const phoneMode = global.H2PlateSystem?.isPhone?.(type);
    if (!phoneMode && global.H2PlateSystem?.renderPlate && state) {
      // Only rewrite this overlay's glyphs; full renderPlate is fine and keeps boxes
      global.H2PlateSystem.renderPlate(state);
      return;
    }
    el.classList.remove("has-glyphs");
    el.textContent = text == null ? "" : String(text);
  }

  /**
   * Use existing plate-num glyphs when present (no reflow).
   * Otherwise build the same flex glyph structure plate-system uses.
   */
  function ensureDigitSpans(el) {
    const existing = Array.from(el.querySelectorAll(":scope > .plate-num"));
    if (existing.length) {
      const original = existing.map((s) => s.textContent || "").join("");
      existing.forEach((span, i) => {
        span.dataset.digitIndex = String(i);
        span.style.visibility = "";
        span.style.opacity = "";
      });
      return { original, spans: existing };
    }

    const original = el.textContent ?? "";
    const chars = Array.from(original);
    el.classList.add("has-glyphs");
    el.style.display = "";
    el.style.textAlign = "";
    el.textContent = "";
    const spans = chars.map((ch, i) => {
      const span = document.createElement("span");
      const isSpace = ch === " " || ch === "\u00a0";
      span.className = ch === "1" ? "plate-num plate-num-1" : "plate-num";
      if (isSpace) span.classList.add("is-space");
      span.dataset.digitIndex = String(i);
      span.textContent = isSpace ? "\u00a0" : ch;
      el.appendChild(span);
      return span;
    });
    return { original, spans };
  }

  function copyTypography(fromEl, toEl) {
    const cs = getComputedStyle(fromEl);
    toEl.style.fontFamily = cs.fontFamily;
    toEl.style.fontSize = cs.fontSize;
    toEl.style.fontWeight = cs.fontWeight;
    toEl.style.fontStyle = cs.fontStyle;
    toEl.style.fontStretch = cs.fontStretch;
    toEl.style.fontVariantNumeric = cs.fontVariantNumeric;
    // Single glyph — do not carry parent letter-spacing / flex gap
    toEl.style.letterSpacing = "0";
    toEl.style.lineHeight = "1";
    toEl.style.color = cs.color;
    toEl.style.textShadow = cs.textShadow;
    toEl.style.textRendering = cs.textRendering;
  }

  function finishDropHidden(el, originalText, myGen) {
    if (myGen != null && myGen !== dropGen) return;
    clearDropStaggerTimers();
    clearFallLayer();
    dropOriginalText = originalText;
    const state = global.H2V4State?.getState?.();
    // Honor newer lot/show actions that restored visibility during the fall
    const keepVisible = state?.new_style?.number_visible !== false;
    // Hide before glyph rebuild so digits never flash after the cascade
    if (!keepVisible && el) {
      el.style.opacity = "0";
      el.style.visibility = "hidden";
      el.classList.add("is-hidden");
    }
    // Clear busy before applyNumberVisibility (it no-ops while dropBusy)
    if (myGen === dropGen) dropBusy = false;
    restorePlainText(el, originalText, { keepHidden: !keepVisible });
    if (!keepVisible) {
      if (state?.new_style) state.new_style.number_visible = false;
      applyNumberVisibility(false);
    } else {
      applyNumberVisibility(true);
    }
  }

  /**
   * Abort in-flight Number Drop so stale callbacks cannot hide a newer number.
   * Restores plate text from live state (or last captured drop text).
   */
  function cancelDrop() {
    dropGen += 1;
    clearDropStaggerTimers();
    clearFallLayer();
    dropBusy = false;
    const el = contentEl();
    const state = global.H2V4State?.getState?.();
    const type = state?.plate_type || "dubai";
    const phoneMode = global.H2PlateSystem?.isPhone?.(type);
    const text =
      (phoneMode ? state?.phone_number : state?.number) ??
      dropOriginalText ??
      "";
    if (el) restorePlainText(el, text);
    dropOriginalText = "";
  }

  /**
   * Sequential downward Number Drop — one digit after another, L→R.
   * Remaining glyphs keep their flex slots (visibility:hidden only).
   */
  function playDrop() {
    const el = contentEl();
    const stage = document.getElementById("stage");
    const Geom = global.H2V4Geom;
    if (!el || !stage || !Geom) return;

    // Restart safely if a previous cascade is still running
    if (dropBusy) {
      cancelDrop();
    }

    const myGen = ++dropGen;

    // Ensure source is visible for measurement
    el.style.visibility = "visible";
    el.style.opacity = "1";
    el.classList.remove("is-hidden");
    el.removeAttribute("hidden");

    // Prefer state value so we drop the true registration, not a stale DOM scrap
    const state = global.H2V4State?.getState?.() || {};
    const type = state.plate_type || "dubai";
    const phoneMode = global.H2PlateSystem?.isPhone?.(type);
    const desired = String(
      phoneMode ? state.phone_number || "" : state.number || el.textContent || "",
    );

    if (!phoneMode && global.H2PlateSystem?.renderPlate) {
      global.H2PlateSystem.renderPlate(state);
    } else if (desired && (el.textContent || "") !== desired) {
      el.textContent = desired;
    }

    void el.offsetWidth;

    const { original, spans } = ensureDigitSpans(el);
    dropOriginalText = original || desired;
    void el.offsetWidth;

    if (!spans.length) {
      finishDropHidden(el, dropOriginalText, myGen);
      return;
    }

    dropBusy = true;
    clearFallLayer();
    el.classList.add("is-dropping");

    let pending = spans.length;

    spans.forEach((span, index) => {
      const ch = span.textContent || "";
      const isSpace =
        span.classList.contains("is-space") || ch === "\u00a0" || ch === " ";
      const startAt = index * DROP_STAGGER_MS;

      const tid = window.setTimeout(() => {
        if (myGen !== dropGen) return;

        if (isSpace) {
          span.style.visibility = "hidden";
          span.style.opacity = "0";
          pending -= 1;
          if (pending === 0) finishDropHidden(el, dropOriginalText, myGen);
          return;
        }

        const box = Geom.elementStageBox(span);
        if (!box || box.w < 0.5 || box.h < 0.5) {
          span.style.visibility = "hidden";
          span.style.opacity = "0";
          pending -= 1;
          if (pending === 0) finishDropHidden(el, dropOriginalText, myGen);
          return;
        }

        // Detach visually; keep flex slot so later digits do not shift
        span.style.visibility = "hidden";
        span.style.opacity = "0";

        const faller = document.createElement("div");
        const isOne = ch === "1" || span.classList.contains("plate-num-1");
        faller.className = isOne
          ? "plate-digit-fall plate-num plate-num-1"
          : "plate-digit-fall plate-num";
        faller.textContent = ch === "\u00a0" ? " " : ch;
        faller.setAttribute("aria-hidden", "true");
        copyTypography(span, faller);
        // Re-apply opaque ink for falling clone (plate-num-1 uses transparent + ::before)
        if (!isOne) {
          faller.style.color = getComputedStyle(el).color || "#0a0a0a";
        }
        faller.style.left = `${box.x}px`;
        faller.style.top = `${box.y}px`;
        faller.style.width = `${Math.max(box.w, 1)}px`;
        faller.style.height = `${Math.max(box.h, 1)}px`;
        stage.appendChild(faller);

        const drift = (index % 2 === 0 ? -1 : 1) * (5 + (index % 3) * 3);
        const rot = (index % 2 === 0 ? -1 : 1) * (10 + (index % 4) * 4);

        const anim = faller.animate(
          [
            {
              transform: "translate(0px, 0px) rotate(0deg)",
              opacity: 1,
              offset: 0,
            },
            {
              transform: `translate(${drift * 0.35}px, ${DROP_FALL_DIST * 0.45}px) rotate(${rot * 0.45}deg)`,
              opacity: 0.92,
              offset: 0.45,
            },
            {
              transform: `translate(${drift}px, ${DROP_FALL_DIST}px) rotate(${rot}deg)`,
              opacity: 0,
              offset: 1,
            },
          ],
          {
            duration: DROP_FALL_MS,
            easing: "cubic-bezier(0.33, 0.0, 0.7, 1)",
            fill: "forwards",
          },
        );

        anim.finished.finally(() => {
          faller.remove();
          if (myGen !== dropGen) return;
          pending -= 1;
          if (pending === 0) finishDropHidden(el, dropOriginalText, myGen);
        });
      }, startAt);

      dropStaggerTimers.push(tid);
    });

    const totalMs =
      DROP_STAGGER_MS * Math.max(0, spans.length - 1) + DROP_FALL_MS + 250;
    dropCleanupTimer = window.setTimeout(() => {
      if (myGen === dropGen && dropBusy) {
        finishDropHidden(el, dropOriginalText, myGen);
      }
    }, totalMs);
  }

  function fitRimToShell() {
    const plate = document.getElementById("plate");
    const shell = document.getElementById("plate-shell");
    const rim = document.getElementById("plate-rim");
    if (!plate || !shell || !rim) return;
    global.H2V4Character?.fitRim?.();
    if (!global.H2V4Character?.fitRim) {
      const pr = plate.getBoundingClientRect();
      const sr = shell.getBoundingClientRect();
      const scale = global.H2V4Geom?.getStageScale?.() || 1;
      const pad = 10;
      rim.style.left = `${(sr.left - pr.left) / scale - pad}px`;
      rim.style.top = `${(sr.top - pr.top) / scale - pad}px`;
      rim.style.width = `${sr.width / scale + pad * 2}px`;
      rim.style.height = `${sr.height / scale + pad * 2}px`;
      rim.style.right = "auto";
      rim.style.bottom = "auto";
      rim.style.inset = "auto";
    }
  }

  function setYellow(on) {
    const plate = document.getElementById("plate");
    const rim = document.getElementById("plate-rim");
    if (on) {
      // Extra pad so soft bloom can extend past the physical shell without a hard frame
      fitRimPadded(28);
      // Clear red glow visuals if somehow still active (digits stay as-is)
      rim?.classList.remove("red");
      plate?.classList.remove("red-card", "red-illuminate");
    }
    plate?.classList.toggle("yellow-card", !!on);
    plate?.classList.toggle("yellow-illuminate", !!on);
    rim?.classList.toggle("yellow", !!on);
    rim?.setAttribute("aria-hidden", on || rim?.classList.contains("red") ? "false" : "true");
    if (!on && !rim?.classList.contains("red")) {
      plate?.classList.remove("yellow-illuminate");
    }
  }

  function fitRimPadded(pad) {
    const plate = document.getElementById("plate");
    const shell = document.getElementById("plate-shell");
    const rim = document.getElementById("plate-rim");
    if (!plate || !shell || !rim) {
      fitRimToShell();
      return;
    }
    const pr = plate.getBoundingClientRect();
    const sr = shell.getBoundingClientRect();
    const scale = global.H2V4Geom?.getStageScale?.() || 1;
    const p = pad != null ? pad : 28;
    rim.style.left = `${(sr.left - pr.left) / scale - p}px`;
    rim.style.top = `${(sr.top - pr.top) / scale - p}px`;
    rim.style.width = `${sr.width / scale + p * 2}px`;
    rim.style.height = `${sr.height / scale + p * 2}px`;
    rim.style.right = "auto";
    rim.style.bottom = "auto";
    rim.style.inset = "auto";
  }

  function setRed(on) {
    const plate = document.getElementById("plate");
    const rim = document.getElementById("plate-rim");
    if (on) {
      // Clear yellow glow first so the two card lights never stack
      setYellow(false);
      fitRimPadded(28);
      plate?.classList.remove("red-card", "red-illuminate");
      void plate?.offsetWidth;
      plate?.classList.add("red-card", "red-illuminate");
      rim?.classList.add("red");
      rim?.classList.remove("yellow");
      rim?.setAttribute("aria-hidden", "false");
      // Hide registration/phone digits only — code/logo/art stay visible
      applyNumberVisibility(false);
    } else {
      // Glow off only — do NOT restore digits (persistent until Show Number)
      rim?.classList.remove("red");
      plate?.classList.remove("red-card", "red-illuminate");
      if (!rim?.classList.contains("yellow")) {
        rim?.setAttribute("aria-hidden", "true");
      }
    }
  }

  function clearCardFx() {
    setYellow(false);
    setRed(false);
  }

  global.H2V4BeamDropFx = {
    applyNumberVisibility,
    playReveal,
    playBeam,
    playDrop,
    cancelDrop,
    setYellow,
    setRed,
    clearCardFx,
    isDropBusy: () => dropBusy,
  };
})(window);
