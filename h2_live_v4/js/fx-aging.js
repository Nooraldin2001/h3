/**
 * H2 Live V4 — Plate Aging & Breaking controller (sandbox).
 *
 * Independent of the auction countdown timer.
 * Elapsed-time clock + normalized stage timeline (60s preset proportions).
 * Procedural surface/crack/fragment FX — INTERIM, not authored production art.
 *
 * ASSET_TIER: interim
 */
(function (global) {
  const ASSET_TIER = "interim";

  /** Stage fractions of total duration (from 60s reference timeline). */
  const STAGE_DEFS = [
    { id: "pristine", label: "Pristine", from: 0, to: 50 / 60 },
    { id: "weather", label: "Weathering", from: 50 / 60, to: 53 / 60 },
    { id: "stress", label: "Stress / fine cracks", from: 53 / 60, to: 56 / 60 },
    { id: "fragment", label: "Crack network / chips", from: 56 / 60, to: 59 / 60 },
    { id: "break", label: "Final break", from: 59 / 60, to: 1 },
  ];

  /** Deterministic stress anchors in plate UV (believable edge / mount points). */
  const STRESS_POINTS = [
    { x: 0.08, y: 0.22 },
    { x: 0.92, y: 0.28 },
    { x: 0.18, y: 0.78 },
    { x: 0.82, y: 0.74 },
    { x: 0.48, y: 0.18 },
    { x: 0.55, y: 0.85 },
    { x: 0.35, y: 0.48 },
  ];

  let raf = 0;
  let lastFrameMs = 0;
  let fragments = [];
  let crackTree = null;
  let surfaceDirty = true;
  let lastDrawnProgress = -1;
  let lastStageId = "";
  let plateIdentityKey = "";

  function nowMs() {
    return global.H2V4State?.nowMs?.() || Date.now();
  }

  function aging() {
    return global.H2V4State?.getState?.()?.new_style?.aging || {};
  }

  function ensureAgingDefaults(a) {
    if (typeof a.enabled !== "boolean") a.enabled = false;
    if (typeof a.running !== "boolean") a.running = false;
    if (typeof a.paused !== "boolean") a.paused = false;
    if (typeof a.completed !== "boolean") a.completed = false;
    if (!Number.isFinite(Number(a.total_duration_seconds))) {
      // Migrate legacy fresh+deteriorate → total
      const fresh = Math.max(0, Number(a.fresh_delay_seconds) || 50);
      const det = Math.max(1, Number(a.aging_duration_seconds) || 10);
      a.total_duration_seconds = fresh + det;
    }
    a.total_duration_seconds = Math.max(5, Number(a.total_duration_seconds) || 60);
    if (!Number.isFinite(Number(a.elapsed_ms))) a.elapsed_ms = 0;
    return a;
  }

  function totalMs() {
    return ensureAgingDefaults(aging()).total_duration_seconds * 1000;
  }

  function getElapsedMs() {
    const a = ensureAgingDefaults(aging());
    if (!a.enabled) return 0;
    if (a.completed) return totalMs();
    if (!a.running) return Math.max(0, Number(a.elapsed_ms) || 0);
    if (a.paused) return Math.max(0, Number(a.elapsed_ms) || 0);
    const started = Date.parse(a.started_at || "");
    const base = Math.max(0, Number(a.elapsed_ms) || 0);
    if (!Number.isFinite(started)) return base;
    return Math.min(totalMs(), base + (nowMs() - started));
  }

  function getProgress() {
    const t = totalMs();
    if (t <= 0) return 0;
    return Math.max(0, Math.min(1, getElapsedMs() / t));
  }

  function stageAt(progress) {
    const p = Math.max(0, Math.min(1, progress));
    for (let i = 0; i < STAGE_DEFS.length; i += 1) {
      const s = STAGE_DEFS[i];
      if (p < s.to || i === STAGE_DEFS.length - 1) {
        const span = Math.max(1e-6, s.to - s.from);
        return {
          ...s,
          local: Math.max(0, Math.min(1, (p - s.from) / span)),
          progress: p,
        };
      }
    }
    const last = STAGE_DEFS[STAGE_DEFS.length - 1];
    return { ...last, local: 1, progress: 1 };
  }

  function getStage() {
    return stageAt(getProgress());
  }

  function getStatus() {
    const a = ensureAgingDefaults(aging());
    const progress = getProgress();
    const stage = stageAt(progress);
    return {
      enabled: !!a.enabled,
      running: !!a.running,
      paused: !!a.paused,
      completed: !!a.completed,
      total_duration_seconds: a.total_duration_seconds,
      elapsed_ms: getElapsedMs(),
      elapsed_seconds: getElapsedMs() / 1000,
      progress,
      stage: stage.id,
      stage_label: stage.label,
      stage_local: stage.local,
      asset_tier: ASSET_TIER,
    };
  }

  function patchAging(partial) {
    const state = global.H2V4State?.getState?.();
    if (!state?.new_style) return;
    state.new_style.aging = Object.assign(ensureAgingDefaults(state.new_style.aging || {}), partial);
  }

  function syncLegacyFields() {
    const a = ensureAgingDefaults(aging());
    // Keep legacy mirrors for older debug/tools (fresh = pristine portion)
    a.fresh_delay_seconds = a.total_duration_seconds * (50 / 60);
    a.aging_duration_seconds = a.total_duration_seconds * (10 / 60);
  }

  /* ---------- Controls ---------- */

  function setEnabled(on) {
    const enabled = !!on;
    if (!enabled) {
      patchAging({
        enabled: false,
        running: false,
        paused: false,
        completed: false,
        started_at: null,
        elapsed_ms: 0,
      });
      clearAllVisuals();
      surfaceDirty = true;
      return getStatus();
    }
    patchAging({ enabled: true });
    syncLegacyFields();
    ensureLoop();
    return getStatus();
  }

  function setDuration(seconds) {
    const sec = Math.max(5, Math.min(600, Math.floor(Number(seconds) || 60)));
    const a = ensureAgingDefaults(aging());
    const wasRunning = a.running && !a.paused && !a.completed;
    let elapsed = getElapsedMs();
    if (wasRunning) {
      // Freeze accumulator before changing duration
      elapsed = getElapsedMs();
    }
    const newTotal = sec * 1000;
    const progress = a.completed ? 1 : Math.min(1, elapsed / Math.max(1, totalMs()));
    const nextElapsed = a.completed ? newTotal : Math.min(newTotal, progress * newTotal);
    patchAging({
      total_duration_seconds: sec,
      elapsed_ms: nextElapsed,
      started_at: wasRunning ? new Date(nowMs()).toISOString() : a.started_at,
      completed: nextElapsed >= newTotal,
    });
    syncLegacyFields();
    surfaceDirty = true;
    return getStatus();
  }

  function startAging() {
    const a = ensureAgingDefaults(aging());
    if (!a.enabled) setEnabled(true);
    if (a.completed) {
      // Restart from pristine when starting after completion
      fragments = [];
      crackTree = null;
      patchAging({
        running: true,
        paused: false,
        completed: false,
        elapsed_ms: 0,
        started_at: new Date(nowMs()).toISOString(),
      });
    } else if (a.running && !a.paused) {
      return getStatus(); // idempotent
    } else if (a.paused) {
      return resumeAging();
    } else {
      patchAging({
        running: true,
        paused: false,
        completed: false,
        elapsed_ms: Number(a.elapsed_ms) || 0,
        started_at: new Date(nowMs()).toISOString(),
      });
    }
    syncLegacyFields();
    surfaceDirty = true;
    ensureLoop();
    return getStatus();
  }

  function pauseAging() {
    const a = ensureAgingDefaults(aging());
    if (!a.enabled || !a.running || a.paused || a.completed) return getStatus();
    patchAging({
      elapsed_ms: getElapsedMs(),
      paused: true,
      started_at: null,
    });
    return getStatus();
  }

  function resumeAging() {
    const a = ensureAgingDefaults(aging());
    if (!a.enabled) return getStatus();
    if (a.completed) return getStatus();
    if (!a.running) return startAging();
    if (!a.paused) return getStatus();
    patchAging({
      paused: false,
      started_at: new Date(nowMs()).toISOString(),
    });
    ensureLoop();
    return getStatus();
  }

  function resetAging() {
    patchAging({
      running: false,
      paused: false,
      completed: false,
      started_at: null,
      elapsed_ms: 0,
    });
    clearAllVisuals();
    surfaceDirty = true;
    lastDrawnProgress = -1;
    lastStageId = "";
    return getStatus();
  }

  function disable() {
    return setEnabled(false);
  }

  function enable() {
    return setEnabled(true);
  }

  /* ---------- Geometry / canvases ---------- */

  function plateSize() {
    const plate = document.getElementById("plate");
    if (!plate) return { w: 760, h: 160 };
    return (
      global.H2V4Geom?.layoutSize(plate) || {
        w: plate.clientWidth || 760,
        h: plate.clientHeight || 160,
      }
    );
  }

  function sizeCanvas(canvas, w, h, dprOpt) {
    if (!canvas) return null;
    const dpr = dprOpt || Math.min(2, window.devicePixelRatio || 1);
    const cssW = Math.max(1, Math.round(w));
    const cssH = Math.max(1, Math.round(h));
    const bw = Math.round(cssW * dpr);
    const bh = Math.round(cssH * dpr);
    if (canvas.width !== bw || canvas.height !== bh) {
      canvas.width = bw;
      canvas.height = bh;
      canvas.style.width = `${cssW}px`;
      canvas.style.height = `${cssH}px`;
      surfaceDirty = true;
      crackTree = null;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w: cssW, h: cssH, dpr };
  }

  function surfaceCanvas() {
    return document.getElementById("plate-aging-surface");
  }

  function fragCanvas() {
    return document.getElementById("plate-fragments");
  }

  /* ---------- Deterministic PRNG for crack trees ---------- */

  function mulberry32(seed) {
    let t = seed >>> 0;
    return function () {
      t += 0x6d2b79f5;
      let r = Math.imul(t ^ (t >>> 15), 1 | t);
      r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
      return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
  }

  function hashIdentity() {
    const s = global.H2V4State?.getState?.() || {};
    const key = `${s.plate_type}|${s.code}|${s.number}|${s.phone_number}`;
    let h = 2166136261;
    for (let i = 0; i < key.length; i += 1) {
      h ^= key.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function buildCrackTree(w, h) {
    const rnd = mulberry32(hashIdentity() ^ 0xa6e11);
    const branches = [];

    function grow(x, y, angle, depth, width) {
      if (depth <= 0 || width < 0.35) return;
      const len = (8 + rnd() * 22) * (0.55 + depth * 0.12);
      const x2 = x + Math.cos(angle) * len;
      const y2 = y + Math.sin(angle) * len;
      branches.push({
        x1: x,
        y1: y,
        x2,
        y2,
        w: width,
        depth,
        // normalized reveal order
        order: 1 - depth / 6 + rnd() * 0.08,
      });
      const split = 0.35 + rnd() * 0.45;
      grow(x2, y2, angle + (rnd() - 0.5) * 0.7, depth - 1, width * split);
      if (rnd() > 0.35) {
        grow(x2, y2, angle + (rnd() > 0.5 ? 1 : -1) * (0.5 + rnd() * 0.9), depth - 2, width * 0.55);
      }
    }

    STRESS_POINTS.forEach((p, i) => {
      const x = p.x * w;
      const y = p.y * h;
      const baseAng =
        Math.atan2(h * 0.5 - y, w * 0.5 - x) + (rnd() - 0.5) * 0.8 + (i % 2 ? Math.PI : 0);
      grow(x, y, baseAng, 5 + (i % 2), 1.8 + rnd() * 1.4);
      // Edge chip seeds
      if (rnd() > 0.4) {
        grow(x, y, baseAng + Math.PI * 0.5, 3, 1.1);
      }
    });

    // Fine scratches (shallow)
    const scratches = [];
    for (let i = 0; i < 28; i += 1) {
      const x = rnd() * w;
      const y = rnd() * h;
      const ang = (rnd() - 0.5) * Math.PI;
      const len = 6 + rnd() * 28;
      scratches.push({
        x1: x,
        y1: y,
        x2: x + Math.cos(ang) * len,
        y2: y + Math.sin(ang) * len,
        a: 0.08 + rnd() * 0.18,
        order: rnd() * 0.6,
      });
    }

    return { branches, scratches, w, h };
  }

  function ensureCrackTree(w, h) {
    if (!crackTree || crackTree.w !== w || crackTree.h !== h) {
      crackTree = buildCrackTree(w, h);
    }
    return crackTree;
  }

  /* ---------- Surface draw (clipped to shell) ---------- */

  function drawSurface(progress, stage, physicsActive) {
    const canvas = surfaceCanvas();
    const sized = sizeCanvas(canvas, plateSize().w, plateSize().h);
    if (!sized) return;
    const { ctx, w, h } = sized;

    // Skip full redraw if frozen and already painted this progress
    if (!physicsActive && Math.abs(progress - lastDrawnProgress) < 0.0005 && !surfaceDirty) {
      return;
    }

    ctx.clearRect(0, 0, w, h);
    if (progress <= STAGE_DEFS[0].to && stage.id === "pristine") {
      lastDrawnProgress = progress;
      surfaceDirty = false;
      return;
    }

    const weather = stageIntensity(progress, "weather");
    const stress = stageIntensity(progress, "stress");
    const frag = stageIntensity(progress, "fragment");
    const brk = stageIntensity(progress, "break");
    const wear = Math.max(weather, stress * 0.85, frag, brk);

    // Worn paint / gloss loss — soft mottled veil (multiply-like via alpha)
    if (wear > 0) {
      ctx.save();
      ctx.globalCompositeOperation = "source-over";
      const grd = ctx.createLinearGradient(0, 0, w, h);
      grd.addColorStop(0, `rgba(90, 70, 40, ${0.08 + wear * 0.2})`);
      grd.addColorStop(0.45, `rgba(40, 32, 24, ${0.06 + wear * 0.14})`);
      grd.addColorStop(1, `rgba(120, 90, 50, ${0.1 + wear * 0.22})`);
      ctx.fillStyle = grd;
      ctx.fillRect(0, 0, w, h);

      // Speckle / faded paint pits
      const rnd = mulberry32(hashIdentity() ^ 0x51);
      ctx.fillStyle = `rgba(30, 22, 14, ${0.06 + wear * 0.16})`;
      for (let i = 0; i < Math.floor(55 + wear * 160); i += 1) {
        const x = rnd() * w;
        const y = rnd() * h;
        const r = 0.7 + rnd() * (1.4 + wear * 2.8);
        ctx.beginPath();
        ctx.ellipse(x, y, r * (1.4 + rnd()), r, rnd() * Math.PI, 0, Math.PI * 2);
        ctx.fill();
      }
      // Edge oxidation ring
      ctx.strokeStyle = `rgba(70, 45, 25, ${0.12 + wear * 0.28})`;
      ctx.lineWidth = 3 + wear * 5;
      ctx.strokeRect(2, 2, w - 4, h - 4);
      ctx.restore();
    }

    const tree = ensureCrackTree(w, h);

    // Scratches
    if (weather > 0 || stress > 0) {
      const reveal = Math.min(1, weather * 0.7 + stress);
      tree.scratches.forEach((s) => {
        if (s.order > reveal) return;
        ctx.beginPath();
        ctx.moveTo(s.x1, s.y1);
        ctx.lineTo(s.x2, s.y2);
        ctx.strokeStyle = `rgba(20, 14, 10, ${s.a * reveal})`;
        ctx.lineWidth = 0.6;
        ctx.stroke();
      });
    }

    // Crack network — gap + edge highlight (reads as material split, not flat ink)
    const crackReveal = Math.min(1, stress * 0.55 + frag * 0.95 + brk);
    if (crackReveal > 0) {
      tree.branches.forEach((b) => {
        if (b.order > crackReveal + 0.05) return;
        const local = Math.max(0, Math.min(1, (crackReveal - b.order) / 0.25));
        if (local <= 0) return;
        const thick = b.w * (0.5 + local * 0.9) * (0.7 + frag * 0.5 + brk * 0.6);

        // Dark fissure
        ctx.beginPath();
        ctx.moveTo(b.x1, b.y1);
        ctx.lineTo(b.x2, b.y2);
        ctx.strokeStyle = `rgba(12, 8, 6, ${0.35 + local * 0.55})`;
        ctx.lineWidth = thick;
        ctx.lineCap = "round";
        ctx.stroke();

        // Inner void
        ctx.beginPath();
        ctx.moveTo(b.x1, b.y1);
        ctx.lineTo(b.x2, b.y2);
        ctx.strokeStyle = `rgba(0, 0, 0, ${0.2 + local * 0.45})`;
        ctx.lineWidth = Math.max(0.4, thick * 0.35);
        ctx.stroke();

        // Soft highlight along one edge
        ctx.beginPath();
        ctx.moveTo(b.x1 + 0.6, b.y1 - 0.5);
        ctx.lineTo(b.x2 + 0.6, b.y2 - 0.5);
        ctx.strokeStyle = `rgba(255, 245, 220, ${0.05 + local * 0.12})`;
        ctx.lineWidth = Math.max(0.4, thick * 0.25);
        ctx.stroke();
      });
    }

    // Slight edge deformation cue (shadow notches)
    if (stress > 0 || frag > 0 || brk > 0) {
      const d = Math.max(stress, frag, brk);
      ctx.fillStyle = `rgba(0, 0, 0, ${0.04 + d * 0.1})`;
      ctx.beginPath();
      ctx.moveTo(w * 0.02, h * 0.9);
      ctx.quadraticCurveTo(w * 0.15, h * (1.02 + d * 0.04), w * 0.28, h * 0.92);
      ctx.lineTo(w * 0.02, h);
      ctx.fill();
    }

    lastDrawnProgress = progress;
    surfaceDirty = false;
  }

  function stageIntensity(progress, id) {
    const def = STAGE_DEFS.find((s) => s.id === id);
    if (!def) return 0;
    if (progress <= def.from) return 0;
    if (progress >= def.to) return 1;
    return (progress - def.from) / (def.to - def.from);
  }

  /* ---------- Fragments (free layer, may leave shell) ---------- */

  function samplePlateColor(u, v) {
    const art = document.getElementById("plate-art");
    if (!art || !art.complete || !art.naturalWidth) {
      return { r: 48, g: 40, b: 32 };
    }
    try {
      const c = document.createElement("canvas");
      c.width = 1;
      c.height = 1;
      const cx = c.getContext("2d");
      const sx = Math.max(0, Math.min(art.naturalWidth - 1, Math.floor(u * art.naturalWidth)));
      const sy = Math.max(0, Math.min(art.naturalHeight - 1, Math.floor(v * art.naturalHeight)));
      cx.drawImage(art, sx, sy, 1, 1, 0, 0, 1, 1);
      const d = cx.getImageData(0, 0, 1, 1).data;
      return { r: d[0], g: d[1], b: d[2] };
    } catch (e) {
      return { r: 52, g: 44, b: 36 };
    }
  }

  function spawnFragmentsForProgress(progress, w, h, dt) {
    const frag = stageIntensity(progress, "fragment");
    const brk = stageIntensity(progress, "break");
    if (frag <= 0 && brk <= 0) return;

    const target = Math.floor(frag * 14 + brk * 22);
    const tree = ensureCrackTree(w, h);
    while (fragments.length < target) {
      const b = tree.branches[fragments.length % tree.branches.length];
      const t = 0.65 + (fragments.length % 7) * 0.04;
      const x = b.x1 + (b.x2 - b.x1) * t;
      const y = b.y1 + (b.y2 - b.y1) * t;
      const u = x / w;
      const v = y / h;
      const col = samplePlateColor(u, v);
      const burst = brk > 0.4;
      fragments.push({
        x,
        y,
        vx: (Math.random() - 0.5) * (burst ? 3.2 : 1.2),
        vy: (burst ? -0.6 : 0.15) + Math.random() * (burst ? 1.8 : 0.9),
        rot: Math.random() * Math.PI * 2,
        vr: (Math.random() - 0.5) * (burst ? 0.35 : 0.12),
        w: 3 + Math.random() * (burst ? 9 : 5),
        h: 2 + Math.random() * (burst ? 6 : 3.5),
        life: 1,
        col,
        shadow: true,
      });
    }
  }

  function updateFragments(dt, physicsActive) {
    if (!physicsActive) return;
    const g = 980; // px/s^2-ish scaled
    const gravity = g * 0.0018;
    fragments.forEach((p) => {
      p.vy += gravity * dt * 60;
      p.x += p.vx * dt * 60;
      p.y += p.vy * dt * 60;
      p.rot += p.vr * dt * 60;
      p.life -= 0.12 * dt;
    });
    fragments = fragments.filter((p) => p.life > 0 && p.y < plateSize().h * 3);
  }

  function drawFragments(progress) {
    const canvas = fragCanvas();
    const size = plateSize();
    // Tall canvas so shards can fall outside the shell without covering bid too early
    const fw = size.w * 1.1;
    const fh = size.h * 2.4;
    const sized = sizeCanvas(canvas, fw, fh, Math.min(1.5, window.devicePixelRatio || 1));
    if (!sized) return;
    const { ctx, w, h } = sized;
    ctx.clearRect(0, 0, w, h);

    const ox = (w - size.w) / 2;
    const oy = size.h * 0.15;

    fragments.forEach((p) => {
      const x = ox + p.x;
      const y = oy + p.y;
      if (y > h || x < -20 || x > w + 20) return;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(p.rot);
      ctx.globalAlpha = Math.max(0, Math.min(1, p.life));
      if (p.shadow) {
        ctx.fillStyle = "rgba(0,0,0,0.28)";
        ctx.fillRect(-p.w * 0.5 + 1.5, -p.h * 0.5 + 2, p.w, p.h);
      }
      const { r, g, b } = p.col;
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(-p.w * 0.5, -p.h * 0.5, p.w, p.h);
      ctx.strokeStyle = `rgba(0,0,0,${0.25 * p.life})`;
      ctx.lineWidth = 0.6;
      ctx.strokeRect(-p.w * 0.5, -p.h * 0.5, p.w, p.h);
      // Tiny specular
      ctx.fillStyle = `rgba(255,255,255,${0.08 * p.life})`;
      ctx.fillRect(-p.w * 0.5, -p.h * 0.5, p.w * 0.45, Math.max(1, p.h * 0.25));
      ctx.restore();
    });
  }

  /* ---------- Plate chrome (filter / shake) ---------- */

  function applyPlateChrome(progress, stage, physicsActive) {
    const shell = document.getElementById("plate-shell");
    const art = document.getElementById("plate-art");
    const agingEl = document.getElementById("plate-aging");
    const slide = document.getElementById("plate");
    if (!shell || !agingEl) return;

    const weather = stageIntensity(progress, "weather");
    const stress = stageIntensity(progress, "stress");
    const frag = stageIntensity(progress, "fragment");
    const brk = stageIntensity(progress, "break");
    const active = progress > STAGE_DEFS[0].to;

    agingEl.style.opacity = active ? "1" : "0";
    agingEl.setAttribute("aria-hidden", active ? "false" : "true");

    if (art) {
      if (!active) {
        art.style.filter = "";
      } else {
        const sat = 1 - weather * 0.45 - stress * 0.15 - frag * 0.1;
        const bright = 1 - weather * 0.12 - frag * 0.06;
        const contrast = 1 + weather * 0.1 + stress * 0.08 + brk * 0.1;
        const sepia = weather * 0.22 + stress * 0.08;
        art.style.filter = `saturate(${sat}) brightness(${bright}) contrast(${contrast}) sepia(${sepia})`;
      }
    }

    const deform = stress * 0.035 + frag * 0.04 + brk * 0.05;
    const rot = (stress * 0.6 + frag * 0.9 + brk * 1.4) * (stage.progress > 0.9 ? 1 : -1);
    shell.style.transform = active
      ? `scale(${1 - deform}) rotate(${rot}deg)`
      : "";

    const shaking = physicsActive && brk > 0 && brk < 1;
    slide?.classList.toggle("aging-shake", shaking);
    slide?.classList.toggle("aging-final", brk >= 1 || ensureAgingDefaults(aging()).completed);
  }

  function clearAllVisuals() {
    fragments = [];
    crackTree = null;
    const art = document.getElementById("plate-art");
    const shell = document.getElementById("plate-shell");
    const agingEl = document.getElementById("plate-aging");
    const slide = document.getElementById("plate");
    if (art) art.style.filter = "";
    if (shell) shell.style.transform = "";
    if (agingEl) {
      agingEl.style.opacity = "0";
      agingEl.setAttribute("aria-hidden", "true");
    }
    slide?.classList.remove("aging-shake", "aging-final");
    const sc = surfaceCanvas();
    if (sc) {
      const ctx = sc.getContext("2d");
      ctx?.setTransform(1, 0, 0, 1, 0, 0);
      ctx?.clearRect(0, 0, sc.width, sc.height);
    }
    const fc = fragCanvas();
    if (fc) {
      const ctx = fc.getContext("2d");
      ctx?.setTransform(1, 0, 0, 1, 0, 0);
      ctx?.clearRect(0, 0, fc.width, fc.height);
    }
  }

  /* ---------- Main loop ---------- */

  function tick(frameMs) {
    const a = ensureAgingDefaults(aging());
    const dt = lastFrameMs ? Math.min(0.05, (frameMs - lastFrameMs) / 1000) : 0.016;
    lastFrameMs = frameMs;

    // Completion latch
    if (a.enabled && a.running && !a.paused && !a.completed) {
      const elapsed = getElapsedMs();
      if (elapsed >= totalMs()) {
        patchAging({
          completed: true,
          running: true,
          paused: false,
          elapsed_ms: totalMs(),
          started_at: null,
        });
      }
    }

    const progress = a.enabled ? getProgress() : 0;
    const stage = stageAt(progress);
    const physicsActive = !!(a.enabled && a.running && !a.paused && !a.completed);

    if (!a.enabled || progress <= 0) {
      if (lastStageId !== "pristine" || surfaceDirty) {
        clearAllVisuals();
        lastStageId = "pristine";
        surfaceDirty = false;
      }
    } else {
      const size = plateSize();
      drawSurface(progress, stage, physicsActive);
      if (physicsActive) {
        spawnFragmentsForProgress(progress, size.w, size.h, dt);
        updateFragments(dt, true);
      }
      drawFragments(progress);
      applyPlateChrome(progress, stage, physicsActive);
      lastStageId = stage.id;
    }

    raf = requestAnimationFrame(tick);
  }

  function ensureLoop() {
    if (!raf) {
      lastFrameMs = 0;
      raf = requestAnimationFrame(tick);
    }
  }

  function startLoop() {
    ensureLoop();
  }

  function stopLoop() {
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
    lastFrameMs = 0;
  }

  function resetVisual() {
    clearAllVisuals();
    surfaceDirty = true;
  }

  function onPlateChange() {
    // Keep clock; rebuild geometry-bound FX for new aspect / art
    fragments = [];
    crackTree = null;
    surfaceDirty = true;
    const key = String(hashIdentity());
    if (key !== plateIdentityKey) plateIdentityKey = key;
  }

  /** Seek normalized progress 0..1 for QA (keeps enabled+running, freezes). */
  function seekProgress(p, opts) {
    const progress = Math.max(0, Math.min(1, Number(p) || 0));
    const a = ensureAgingDefaults(aging());
    if (!a.enabled) setEnabled(true);
    const elapsed = progress * totalMs();
    patchAging({
      running: true,
      paused: opts?.freeze !== false,
      completed: progress >= 1,
      elapsed_ms: elapsed,
      started_at: null,
    });
    fragments = [];
    surfaceDirty = true;
    ensureLoop();
    // Force one visual apply
    const stage = stageAt(progress);
    drawSurface(progress, stage, false);
    spawnFragmentsForProgress(progress, plateSize().w, plateSize().h, 0);
    if (progress >= STAGE_DEFS.find((s) => s.id === "break").from) {
      // Place a few frozen shards for stage screenshot
      updateFragments(0, false);
    }
    drawFragments(progress);
    applyPlateChrome(progress, stage, false);
    return getStatus();
  }

  // Back-compat helpers
  function agingProgress() {
    // Old API returned deteriorate-only 0..1; map weather→break portion
    const p = getProgress();
    const from = STAGE_DEFS[1].from;
    if (p <= from) return 0;
    return Math.min(1, (p - from) / (1 - from));
  }

  function applyAgingVisual(t) {
    // Legacy: t is deteriorate 0..1 → map into full timeline
    const from = STAGE_DEFS[1].from;
    seekProgress(from + Math.max(0, Math.min(1, t)) * (1 - from), { freeze: true });
  }

  global.H2V4AgingFx = {
    ASSET_TIER,
    STAGE_DEFS,
    STRESS_POINTS,
    enable,
    disable,
    setEnabled,
    setDuration,
    startAging,
    pauseAging,
    resumeAging,
    resetAging,
    getElapsedMs,
    getProgress,
    getStage,
    getStatus,
    seekProgress,
    agingProgress,
    applyAgingVisual,
    /** Boot RAF loop (broadcast). Does not enable/start aging. */
    start: startLoop,
    startLoop,
    stop: stopLoop,
    stopLoop,
    resetVisual,
    onPlateChange,
  };
})(window);
