/**
 * H2 Live V4 — light beam orbit + number reveal/drop (plate-local).
 * Number Drop = sequential digit-by-digit downward fall (not simultaneous).
 */
(function (global) {
  let dropBusy = false;
  let dropCleanupTimer = 0;

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

  function restorePlainText(el, text) {
    if (!el) return;
    el.style.display = "";
    el.style.textAlign = "";
    el.textContent = text;
  }

  /**
   * Split visible glyphs into measurable spans (preserves parent typography).
   */
  function splitIntoDigitSpans(el) {
    const original = el.textContent ?? "";
    const chars = Array.from(original);
    // Inline flow keeps letter-spacing / centering closer to the static plate text
    el.style.display = "block";
    el.style.textAlign = "center";
    el.textContent = "";
    const spans = chars.map((ch, i) => {
      const span = document.createElement("span");
      span.className = "plate-digit";
      span.dataset.digitIndex = String(i);
      span.textContent = ch === " " ? "\u00a0" : ch;
      if (ch === " " || ch === "\u00a0") span.classList.add("is-space");
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
    toEl.style.letterSpacing = cs.letterSpacing;
    toEl.style.lineHeight = "1";
    toEl.style.color = cs.color;
    toEl.style.textShadow = cs.textShadow;
    toEl.style.textRendering = cs.textRendering;
  }

  function finishDropHidden(el, originalText) {
    restorePlainText(el, originalText);
    clearFallLayer();
    const state = global.H2V4State?.getState?.();
    if (state?.new_style) {
      state.new_style.number_visible = false;
    }
    applyNumberVisibility(false);
    dropBusy = false;
  }

  /**
   * Sequential downward Number Drop — one digit after another.
   */
  function playDrop() {
    const el = contentEl();
    const stage = document.getElementById("stage");
    const Geom = global.H2V4Geom;
    if (!el || !stage || !Geom) return;
    if (dropBusy) return;

    // Ensure source is visible for measurement
    const wasHidden = el.classList.contains("is-hidden") || el.style.visibility === "hidden";
    if (wasHidden) {
      el.style.visibility = "visible";
      el.style.opacity = "1";
      el.classList.remove("is-hidden");
    }

    const textNow = el.textContent ?? "";
    if (!textNow.length) {
      finishDropHidden(el, textNow);
      return;
    }

    dropBusy = true;
    if (dropCleanupTimer) clearTimeout(dropCleanupTimer);
    clearFallLayer();

    const { original, spans } = splitIntoDigitSpans(el);
    // Force layout before measuring
    void el.offsetWidth;

    const fallMs = 720;
    const staggerMs = 200;
    const fallDistance = 340;
    let pending = 0;
    let started = 0;

    spans.forEach((span, index) => {
      const ch = span.textContent;
      // Spaces: simply clear in place when their turn arrives (no falling glyph)
      const isSpace = span.classList.contains("is-space") || ch === "\u00a0" || ch === " ";

      const startAt = index * staggerMs;
      pending += 1;

      setTimeout(() => {
        if (isSpace) {
          span.style.visibility = "hidden";
          span.style.opacity = "0";
          pending -= 1;
          if (pending === 0) finishDropHidden(el, original);
          return;
        }

        const box = Geom.elementStageBox(span);
        if (!box || box.w < 0.5) {
          span.style.visibility = "hidden";
          span.style.opacity = "0";
          pending -= 1;
          if (pending === 0) finishDropHidden(el, original);
          return;
        }

        // Remove digit from plate the same moment the faller appears
        span.style.visibility = "hidden";
        span.style.opacity = "0";

        const faller = document.createElement("div");
        faller.className = "plate-digit-fall";
        faller.textContent = ch === "\u00a0" ? " " : ch;
        copyTypography(el, faller);
        faller.style.left = `${box.x}px`;
        faller.style.top = `${box.y}px`;
        faller.style.width = `${Math.max(box.w, 1)}px`;
        faller.style.height = `${Math.max(box.h, 1)}px`;
        faller.style.display = "flex";
        faller.style.alignItems = "center";
        faller.style.justifyContent = "center";
        stage.appendChild(faller);

        const drift = (index % 2 === 0 ? -1 : 1) * (6 + (index % 3) * 4);
        const rot = (index % 2 === 0 ? -1 : 1) * (8 + (index % 4) * 3);

        const anim = faller.animate(
          [
            { transform: "translate(0px, 0px) rotate(0deg)", opacity: 1 },
            {
              transform: `translate(${drift}px, ${fallDistance}px) rotate(${rot}deg)`,
              opacity: 0,
            },
          ],
          {
            duration: fallMs,
            easing: "cubic-bezier(0.4, 0.0, 0.7, 1)",
            fill: "forwards",
          },
        );

        started += 1;
        anim.finished.finally(() => {
          faller.remove();
          pending -= 1;
          if (pending === 0) finishDropHidden(el, original);
        });
      }, startAt);
    });

    // Safety cleanup if animations stall
    const totalMs = staggerMs * Math.max(0, spans.length - 1) + fallMs + 200;
    dropCleanupTimer = window.setTimeout(() => {
      if (dropBusy) finishDropHidden(el, original);
    }, totalMs + 100);
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
      const shell = document.getElementById("plate-shell");
      if (plate && shell && rim) {
        const pr = plate.getBoundingClientRect();
        const sr = shell.getBoundingClientRect();
        const scale = global.H2V4Geom?.getStageScale?.() || 1;
        const pad = 28;
        rim.style.left = `${(sr.left - pr.left) / scale - pad}px`;
        rim.style.top = `${(sr.top - pr.top) / scale - pad}px`;
        rim.style.width = `${sr.width / scale + pad * 2}px`;
        rim.style.height = `${sr.height / scale + pad * 2}px`;
        rim.style.right = "auto";
        rim.style.bottom = "auto";
        rim.style.inset = "auto";
      } else {
        fitRimToShell();
      }
    }
    plate?.classList.toggle("yellow-card", !!on);
    plate?.classList.toggle("yellow-illuminate", !!on);
    rim?.classList.toggle("yellow", !!on);
    if (on) rim?.classList.remove("red");
    rim?.setAttribute("aria-hidden", on || rim?.classList.contains("red") ? "false" : "true");
    if (!on && !rim?.classList.contains("red")) {
      plate?.classList.remove("yellow-illuminate");
    }
  }

  function setRed(on) {
    const plate = document.getElementById("plate");
    const rim = document.getElementById("plate-rim");
    plate?.classList.toggle("red-card", !!on);
    if (on) {
      fitRimToShell();
      rim?.classList.add("red");
      rim?.classList.remove("yellow");
      rim?.setAttribute("aria-hidden", "false");
      applyNumberVisibility(false);
    } else {
      rim?.classList.remove("red");
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
    setYellow,
    setRed,
    clearCardFx,
    isDropBusy: () => dropBusy,
  };
})(window);
