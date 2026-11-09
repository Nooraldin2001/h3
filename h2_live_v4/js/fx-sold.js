/**
 * H2 Live V4 — SOLD imprint + stage-level cinematic fireworks.
 *
 * Fireworks draw on #stage-fw (full 1920×1080), ABOVE studio/ambient plates
 * and BELOW the auction stack (plate/timer/bid), so bursts are visible in the
 * left/right/upper studio — not hidden under opaque plate art.
 */
(function (global) {
  let fwRaf = 0;
  let particles = [];
  let rockets = [];
  let runningUntil = 0;
  let burstTimers = [];
  let gen = 0;
  let glowTimer = 0;
  let lastTs = 0;

  const DURATION_MS = 5200;
  const STAGE_W = 1920;
  const STAGE_H = 1080;

  function els() {
    return {
      stamp: document.getElementById("plate-sold-stamp"),
      fw: document.getElementById("stage-fw"),
      plate: document.getElementById("plate"),
      shell: document.getElementById("plate-shell"),
      stage: document.getElementById("stage"),
      glow: document.querySelector(".plate-glow"),
    };
  }

  function placeStamp() {
    const { stamp, shell } = els();
    if (!stamp || !shell || !global.H2PlateSystem) return;
    const state = global.H2V4State?.getState?.() || { plate_type: "dubai" };
    const target = global.H2PlateSystem.getStampTarget(state.plate_type || "dubai");
    stamp.style.left = `${target.x * 100}%`;
    stamp.style.top = `${target.y * 100}%`;
    stamp.style.transform = "translate(-50%, -50%) rotate(-18deg)";
  }

  function showImprint() {
    const { stamp } = els();
    if (!stamp) return;
    placeStamp();
    stamp.hidden = false;
    stamp.setAttribute("aria-hidden", "false");
    stamp.classList.remove("imprint");
    void stamp.offsetWidth;
    stamp.classList.add("imprint");
  }

  function hideImprint() {
    const { stamp } = els();
    if (!stamp) return;
    stamp.classList.remove("imprint");
    stamp.hidden = true;
    stamp.setAttribute("aria-hidden", "true");
  }

  function sizeCanvas() {
    const { fw } = els();
    if (!fw) return null;
    if (fw.width !== STAGE_W || fw.height !== STAGE_H) {
      fw.width = STAGE_W;
      fw.height = STAGE_H;
    }
    fw.style.width = `${STAGE_W}px`;
    fw.style.height = `${STAGE_H}px`;
    return fw.getContext("2d");
  }

  /** Plate box in stage CSS pixels (1920×1080 space). */
  function plateBox() {
    const { plate } = els();
    if (plate && global.H2V4Geom?.elementStageBox) {
      const b = global.H2V4Geom.elementStageBox(plate);
      if (b && b.w > 0) return b;
    }
    // Fallback: centered ~760×160 around stack
    return { x: (STAGE_W - 760) / 2, y: STAGE_H * 0.42, w: 760, h: 160 };
  }

  function goldHue() {
    const roll = Math.random();
    if (roll < 0.15) return 48 + Math.random() * 8;
    if (roll < 0.55) return 38 + Math.random() * 14;
    return 28 + Math.random() * 12;
  }

  function spawnBurstAt(ox, oy, opts) {
    const count = opts.count || 48;
    const speed = opts.speed || 1;
    const life = opts.life || 1;
    const gravity = opts.gravity != null ? opts.gravity : 0.055;
    const pattern = opts.pattern || "radial";

    for (let i = 0; i < count; i++) {
      let a;
      let sp;
      if (pattern === "arc") {
        a = -Math.PI * 0.9 + Math.random() * Math.PI * 0.8;
        sp = (3.2 + Math.random() * 5.5) * speed;
      } else if (pattern === "fountain") {
        a = -Math.PI / 2 + (Math.random() - 0.5) * 0.85;
        sp = (4.0 + Math.random() * 5.5) * speed;
      } else if (pattern === "ring") {
        a = (i / count) * Math.PI * 2 + (Math.random() - 0.5) * 0.06;
        sp = (5.0 + Math.random() * 2.2) * speed;
      } else {
        a = Math.random() * Math.PI * 2;
        sp = (2.2 + Math.random() * 6.8) * speed;
      }

      const roll = Math.random();
      const kind = roll < 0.4 ? "spark" : roll < 0.72 ? "ember" : "streak";
      particles.push({
        x: ox,
        y: oy,
        vx: Math.cos(a) * sp * (kind === "streak" ? 1.4 : 1),
        vy: Math.sin(a) * sp * (kind === "streak" ? 1.4 : 1) - (pattern === "fountain" ? 2.2 : 0.8),
        life,
        decay: kind === "streak" ? 0.008 + Math.random() * 0.01 : 0.0045 + Math.random() * 0.008,
        hue: goldHue(),
        sat: 82 + Math.random() * 18,
        light: 55 + Math.random() * 30,
        r: kind === "spark" ? 0.9 + Math.random() * 1.6 : kind === "streak" ? 1.2 + Math.random() * 2.0 : 1.8 + Math.random() * 3.2,
        gravity: gravity * (kind === "spark" ? 0.8 : 1),
        drag: 0.978 + Math.random() * 0.014,
        trail: true,
        kind,
        hist: [],
      });
    }
  }

  function launchRocket(ox, oy, targetX, targetY, delay) {
    rockets.push({
      x: ox,
      y: oy,
      tx: targetX,
      ty: targetY,
      life: 1,
      delay: delay || 0,
      hue: goldHue(),
      hist: [],
      exploded: false,
      speed: 0.045 + Math.random() * 0.02,
      burstOpts: {
        count: 70 + Math.floor(Math.random() * 40),
        speed: 1.15 + Math.random() * 0.35,
        pattern: Math.random() < 0.35 ? "ring" : "radial",
        life: 1.05,
      },
    });
  }

  function scheduleShow(myGen) {
    const box = plateBox();
    const cx = box.x + box.w * 0.5;
    const cy = box.y + box.h * 0.5;
    const left = box.x + box.w * 0.02;
    const right = box.x + box.w * 0.98;
    const podiumY = box.y + box.h * 1.05;
    const podiumL = box.x - 10;
    const podiumR = box.x + box.w + 10;

    // Upper-left / upper-right explosion anchors (studio background regions)
    const ulx = STAGE_W * 0.22;
    const urx = STAGE_W * 0.78;
    const uly = STAGE_H * 0.22;
    const ury = STAGE_H * 0.22;
    const mlx = STAGE_W * 0.16;
    const mrx = STAGE_W * 0.84;
    const midY = STAGE_H * 0.34;

    const waves = [
      // Immediate rockets from podium sides → upper studio
      { t: 0, fn: () => {
        launchRocket(podiumL, podiumY, ulx + (Math.random() - 0.5) * 80, uly + Math.random() * 40, 0);
        launchRocket(podiumR, podiumY, urx + (Math.random() - 0.5) * 80, ury + Math.random() * 40, 0);
        spawnBurstAt(podiumL + 20, podiumY - 10, { count: 36, speed: 1.1, pattern: "fountain" });
        spawnBurstAt(podiumR - 20, podiumY - 10, { count: 36, speed: 1.1, pattern: "fountain" });
      }},
      { t: 220, fn: () => {
        launchRocket(left, podiumY, mlx, midY - 40, 0);
        launchRocket(right, podiumY, mrx, midY - 40, 0);
      }},
      { t: 480, fn: () => {
        spawnBurstAt(ulx, uly + 30, { count: 90, speed: 1.35, pattern: "radial" });
        spawnBurstAt(urx, ury + 30, { count: 90, speed: 1.35, pattern: "radial" });
      }},
      { t: 900, fn: () => {
        launchRocket(podiumL + 40, podiumY, STAGE_W * 0.30, STAGE_H * 0.18, 0);
        launchRocket(podiumR - 40, podiumY, STAGE_W * 0.70, STAGE_H * 0.18, 0);
        spawnBurstAt(cx - box.w * 0.55, cy, { count: 55, speed: 1.15, pattern: "arc" });
        spawnBurstAt(cx + box.w * 0.55, cy, { count: 55, speed: 1.15, pattern: "arc" });
      }},
      { t: 1400, fn: () => {
        spawnBurstAt(STAGE_W * 0.25, STAGE_H * 0.28, { count: 80, speed: 1.3, pattern: "ring" });
        spawnBurstAt(STAGE_W * 0.75, STAGE_H * 0.28, { count: 80, speed: 1.3, pattern: "ring" });
      }},
      { t: 1900, fn: () => {
        launchRocket(podiumL, podiumY - 20, STAGE_W * 0.18, STAGE_H * 0.26, 0);
        launchRocket(podiumR, podiumY - 20, STAGE_W * 0.82, STAGE_H * 0.26, 0);
        spawnBurstAt(STAGE_W * 0.35, STAGE_H * 0.2, { count: 60, speed: 1.2, pattern: "radial" });
        spawnBurstAt(STAGE_W * 0.65, STAGE_H * 0.2, { count: 60, speed: 1.2, pattern: "radial" });
      }},
      { t: 2600, fn: () => {
        spawnBurstAt(ulx + 40, midY, { count: 70, speed: 1.15, pattern: "fountain" });
        spawnBurstAt(urx - 40, midY, { count: 70, speed: 1.15, pattern: "fountain" });
        spawnBurstAt(cx, box.y - 40, { count: 48, speed: 1.05, pattern: "arc" });
      }},
      { t: 3300, fn: () => {
        launchRocket(left - 20, podiumY, STAGE_W * 0.28, STAGE_H * 0.24, 0);
        launchRocket(right + 20, podiumY, STAGE_W * 0.72, STAGE_H * 0.24, 0);
      }},
      { t: 4000, fn: () => {
        spawnBurstAt(STAGE_W * 0.22, STAGE_H * 0.32, { count: 50, speed: 1.0, pattern: "radial", life: 0.85 });
        spawnBurstAt(STAGE_W * 0.78, STAGE_H * 0.32, { count: 50, speed: 1.0, pattern: "radial", life: 0.85 });
      }},
    ];

    waves.forEach((w) => {
      const id = setTimeout(() => {
        if (myGen !== gen) return;
        w.fn();
      }, w.t);
      burstTimers.push(id);
    });
  }

  function setStudioGlow(on) {
    const { stage, plate, glow } = els();
    stage?.classList.toggle("sold-celebration", !!on);
    plate?.classList.toggle("sold-illuminate", !!on);
    glow?.classList.toggle("sold-glow", !!on);
  }

  function drawParticle(ctx, p) {
    const alpha = Math.max(0, Math.min(1, p.life));
    if (alpha <= 0.02) return;

    if (p.trail && p.hist && p.hist.length > 1) {
      ctx.beginPath();
      ctx.moveTo(p.hist[0].x, p.hist[0].y);
      for (let i = 1; i < p.hist.length; i++) ctx.lineTo(p.hist[i].x, p.hist[i].y);
      ctx.strokeStyle = `hsla(${p.hue} ${p.sat}% ${p.light + 12}% / ${alpha * 0.65})`;
      ctx.lineWidth = Math.max(0.8, p.r * (p.kind === "streak" ? 1.0 : 0.55));
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.stroke();
    }

    const glowR = p.r * (p.kind === "ember" ? 2.8 : 2.2);
    const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, glowR);
    grd.addColorStop(0, `hsla(${p.hue} ${p.sat}% ${Math.min(98, p.light + 34)}% / ${alpha})`);
    grd.addColorStop(0.4, `hsla(${p.hue} ${p.sat}% ${p.light}% / ${alpha * 0.75})`);
    grd.addColorStop(1, `hsla(${p.hue} ${p.sat}% ${p.light}% / 0)`);
    ctx.fillStyle = grd;
    ctx.beginPath();
    ctx.arc(p.x, p.y, glowR, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = `hsla(${p.hue} 30% 98% / ${alpha})`;
    ctx.beginPath();
    ctx.arc(p.x, p.y, Math.max(0.6, p.r * 0.45), 0, Math.PI * 2);
    ctx.fill();
  }

  function drawRocket(ctx, r) {
    if (r.delay > 0) return;
    const alpha = Math.max(0, Math.min(1, r.life));
    if (r.hist.length > 1) {
      ctx.beginPath();
      ctx.moveTo(r.hist[0].x, r.hist[0].y);
      for (let i = 1; i < r.hist.length; i++) ctx.lineTo(r.hist[i].x, r.hist[i].y);
      ctx.strokeStyle = `hsla(${r.hue} 90% 70% / ${alpha * 0.85})`;
      ctx.lineWidth = 3.2;
      ctx.lineCap = "round";
      ctx.stroke();
      // Outer soft trail
      ctx.strokeStyle = `hsla(${r.hue} 80% 55% / ${alpha * 0.35})`;
      ctx.lineWidth = 8;
      ctx.stroke();
    }
    ctx.fillStyle = `hsla(${r.hue} 40% 98% / ${alpha})`;
    ctx.beginPath();
    ctx.arc(r.x, r.y, 3.5, 0, Math.PI * 2);
    ctx.fill();
  }

  function frame(myGen, ts) {
    if (myGen !== gen) return;
    const ctx = sizeCanvas();
    const { fw } = els();
    if (!ctx || !fw) return;

    const now = performance.now();
    const t = typeof ts === "number" ? ts : now;
    if (!lastTs) lastTs = t;
    // Cap dt so background-tab throttling doesn't stall forever, but still advances life in ms
    let dt = Math.min(0.05, Math.max(0.008, (t - lastTs) / 1000));
    lastTs = t;
    // Per-frame scale relative to 60fps tuning constants
    const f = dt * 60;

    // Hard stop after celebration window — always clear (independent of rAF throttle)
    if (Date.now() >= runningUntil + 900) {
      particles = [];
      rockets = [];
      fwRaf = 0;
      lastTs = 0;
      ctx.clearRect(0, 0, STAGE_W, STAGE_H);
      setStudioGlow(false);
      return;
    }

    ctx.clearRect(0, 0, STAGE_W, STAGE_H);
    ctx.globalCompositeOperation = "lighter";

    const nextRockets = [];
    rockets.forEach((r) => {
      if (r.delay > 0) {
        r.delay -= dt;
        nextRockets.push(r);
        return;
      }
      const dx = r.tx - r.x;
      const dy = r.ty - r.y;
      const dist = Math.hypot(dx, dy) || 1;
      const step = Math.min(dist, (14 + r.speed * 200) * f);
      r.x += (dx / dist) * step;
      r.y += (dy / dist) * step;
      r.hist.push({ x: r.x, y: r.y });
      if (r.hist.length > 14) r.hist.shift();
      r.life -= 0.012 * f;

      if (dist < 18 || r.life <= 0) {
        if (!r.exploded) {
          r.exploded = true;
          spawnBurstAt(r.x, r.y, r.burstOpts);
          spawnBurstAt(r.x + (Math.random() - 0.5) * 30, r.y + (Math.random() - 0.5) * 20, {
            count: 28,
            speed: 0.85,
            pattern: "radial",
            life: 0.8,
          });
        }
      } else {
        drawRocket(ctx, r);
        nextRockets.push(r);
      }
    });
    rockets = nextRockets;

    // After main window, accelerate fade-out
    const windDown = Date.now() >= runningUntil;
    const next = [];
    particles.forEach((p) => {
      p.x += p.vx * f;
      p.y += p.vy * f;
      const dragPow = Math.pow(p.drag, f);
      p.vx *= dragPow;
      p.vy = p.vy * dragPow + p.gravity * f;
      p.life -= p.decay * f * (windDown ? 3.5 : 1);
      if (!p.hist) p.hist = [];
      p.hist.push({ x: p.x, y: p.y });
      const maxHist = p.kind === "streak" ? 12 : 7;
      if (p.hist.length > maxHist) p.hist.shift();
      if (p.life > 0.02) {
        drawParticle(ctx, p);
        next.push(p);
      }
    });
    particles = next;

    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 1;

    const alive = Date.now() < runningUntil + 900 || particles.length > 0 || rockets.length > 0;
    if (alive) {
      fwRaf = requestAnimationFrame((nextTs) => frame(myGen, nextTs));
    } else {
      fwRaf = 0;
      lastTs = 0;
      ctx.clearRect(0, 0, STAGE_W, STAGE_H);
      setStudioGlow(false);
    }
  }

  function clearBurstTimers() {
    burstTimers.forEach(clearTimeout);
    burstTimers = [];
  }

  function stopFireworks() {
    gen += 1;
    runningUntil = 0;
    particles = [];
    rockets = [];
    lastTs = 0;
    clearBurstTimers();
    if (glowTimer) {
      clearTimeout(glowTimer);
      glowTimer = 0;
    }
    if (fwRaf) cancelAnimationFrame(fwRaf);
    fwRaf = 0;
    setStudioGlow(false);
    const ctx = sizeCanvas();
    if (ctx) ctx.clearRect(0, 0, STAGE_W, STAGE_H);
  }

  function playFireworks(ms) {
    stopFireworks();
    const myGen = gen;
    const dur = Math.max(4500, Math.min(6000, ms || DURATION_MS));
    runningUntil = Date.now() + dur;
    lastTs = 0;
    sizeCanvas();
    setStudioGlow(true);
    scheduleShow(myGen);
    glowTimer = setTimeout(() => {
      if (myGen === gen) setStudioGlow(false);
    }, Math.floor(dur * 0.75));
    // Absolute cleanup timer — survives rAF throttling in background/headless tabs
    const hardStop = setTimeout(() => {
      if (myGen !== gen) return;
      particles = [];
      rockets = [];
      if (fwRaf) cancelAnimationFrame(fwRaf);
      fwRaf = 0;
      lastTs = 0;
      const ctx = sizeCanvas();
      if (ctx) ctx.clearRect(0, 0, STAGE_W, STAGE_H);
      setStudioGlow(false);
    }, dur + 1600);
    burstTimers.push(hardStop);
    fwRaf = requestAnimationFrame((ts) => frame(myGen, ts));
  }

  function shakePlate() {
    const { plate } = els();
    if (!plate) return;
    plate.classList.remove("plate-impact-shake");
    void plate.offsetWidth;
    plate.classList.add("plate-impact-shake");
    setTimeout(() => plate.classList.remove("plate-impact-shake"), 500);
  }

  function triggerSoldLocal(opts) {
    const delay = Math.max(0, Number(opts?.delayMs) || 0);
    const run = () => {
      if (opts?.imprint !== false) showImprint();
      if (opts?.fireworks !== false) playFireworks(opts?.durationMs || DURATION_MS);
      if (opts?.shake !== false) shakePlate();
    };
    if (delay > 0) {
      const id = setTimeout(run, delay);
      burstTimers.push(id);
    } else {
      run();
    }
  }

  function clearSoldVisuals() {
    hideImprint();
    stopFireworks();
  }

  function isPlaying() {
    return fwRaf !== 0 || Date.now() < runningUntil || particles.length > 0 || rockets.length > 0;
  }

  global.H2V4SoldFx = {
    showImprint,
    hideImprint,
    playFireworks,
    stopFireworks,
    shakePlate,
    triggerSoldLocal,
    clearSoldVisuals,
    placeStamp,
    isPlaying,
    DURATION_MS,
  };
})(window);
