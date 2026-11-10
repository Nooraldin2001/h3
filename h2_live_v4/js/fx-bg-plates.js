/**
 * H2 Live V4 — premium ambient floating plates.
 * Final approved pack: ./assets/plates/floating_final/ (12 source PNGs).
 * Never draws registration digits. Default OFF.
 * Density Low/Med/High = 15/25/35. Soft DoF, parallax, cinematic drift.
 */
(function (global) {
  let raf = 0;
  let sprites = [];
  let built = false;
  let building = false;
  let catalog = null;
  let lastBuildSig = "";
  let lastTs = 0;
  let subscribed = false;

  const PACK_DIR = "./assets/plates/floating_final/";
  const MANIFEST_URL = PACK_DIR + "manifest.json";
  const DENSITY_OPTS = [15, 25, 35];
  const DENSITY_DEFAULT = 25;
  const SPEED_PRESETS = { slow: 0.4, normal: 0.65, fast: 1.2 };

  // Keep-out around brand / timer / plate / bid (extra margin for 3D AABB).
  const KEEP_OUT = [
    { x: 700, y: 24, w: 520, h: 118 }, // logo
    { x: 720, y: 150, w: 480, h: 115 }, // timer
    { x: 540, y: 300, w: 840, h: 420 }, // plate (+margin for rotate/sway)
    { x: 700, y: 725, w: 520, h: 175 }, // bid
  ];

  /**
   * Full-studio ambient zones — includes shoulders, light-arc band, podium flanks.
   * Keep-out still rejects protected overlaps.
   */
  const STUDIO_ZONES = [
    { id: "arc_left", x: 40, y: 4, w: 520, h: 150 },
    { id: "arc_center", x: 300, y: 2, w: 1320, h: 48 }, // above logo / light arcs
    { id: "arc_right", x: 1360, y: 4, w: 520, h: 150 },
    { id: "upper_left", x: 20, y: 100, w: 460, h: 180 },
    { id: "upper_right", x: 1440, y: 100, w: 460, h: 180 },
    { id: "shoulder_left", x: 300, y: 180, w: 200, h: 520 }, // inner mid-left (clear of plate)
    { id: "shoulder_right", x: 1420, y: 180, w: 200, h: 520 }, // inner mid-right
    { id: "mid_left", x: 8, y: 200, w: 360, h: 520 },
    { id: "mid_right", x: 1550, y: 200, w: 360, h: 520 },
    { id: "lower_left", x: 30, y: 720, w: 480, h: 300 },
    { id: "lower_right", x: 1410, y: 720, w: 480, h: 300 },
    { id: "podium_left", x: 240, y: 880, w: 360, h: 170 },
    { id: "podium_right", x: 1320, y: 880, w: 360, h: 170 },
    { id: "podium_center", x: 500, y: 950, w: 920, h: 100 }, // below bid, over podium
    { id: "deep_bg_left", x: 70, y: 260, w: 320, h: 420 },
    { id: "deep_bg_right", x: 1530, y: 260, w: 320, h: 420 },
  ];

  // Final approved set — cycle emirates (dubai has A/B/C variants).
  const EMIRATE_BIAS = [
    "dubai",
    "dubai_classic",
    "abudhabi",
    "sharjah",
    "ajman",
    "rasalkhaimah",
    "ummalquwain",
    "fujairah",
    "du",
    "etisalat",
  ];

  function resolveDensity(raw) {
    if (typeof raw === "string") {
      const key = raw.toLowerCase().trim();
      if (key === "low") return 15;
      if (key === "medium" || key === "med") return 25;
      if (key === "high") return 35;
    }
    const n = Number(raw);
    if (DENSITY_OPTS.includes(n)) return n;
    // Legacy V4 presets (8/16/25) → new counts
    if (n === 8) return 15;
    if (n === 16) return 25;
    // Old "High (25)" maps to new HIGH when value is exactly the legacy-only high label was 25
    // and current medium is also 25 — keep 25 as MEDIUM for exact match above.
    if (n > 0 && n <= 3) {
      if (n <= 1.25) return 15;
      if (n <= 2.25) return 25;
      return 35;
    }
    return DENSITY_DEFAULT;
  }

  function resolveSpeed(raw) {
    if (typeof raw === "string") {
      const key = raw.toLowerCase().trim();
      if (SPEED_PRESETS[key] != null) return SPEED_PRESETS[key];
    }
    const n = Number(raw);
    if (!Number.isFinite(n) || n <= 0) return SPEED_PRESETS.normal;
    return Math.max(0.2, Math.min(2.5, n));
  }

  function isEnabled(state) {
    return !!state?.new_style?.bg_motion_enabled;
  }

  function isPlaying(state) {
    const ns = state?.new_style || {};
    if (!ns.bg_motion_enabled) return false;
    return ns.bg_motion_playing !== false;
  }

  function overlapsKeepOut(x, y, w, h) {
    const pad = 26;
    const a = { x: x - pad, y: y - pad, w: w + pad * 2, h: h + pad * 2 };
    return KEEP_OUT.some((b) => {
      return !(
        a.x + a.w < b.x ||
        b.x + b.w < a.x ||
        a.y + a.h < b.y ||
        b.y + b.h < a.y
      );
    });
  }

  function pickZone(i, count) {
    // Heavier weight on arcs / shoulders / podium so the field fills (not edge columns).
    const preferred = [
      "arc_center",
      "shoulder_left",
      "shoulder_right",
      "podium_center",
      "arc_left",
      "arc_right",
      "podium_left",
      "podium_right",
      "arc_center",
      "shoulder_left",
      "upper_left",
      "shoulder_right",
      "upper_right",
      "mid_left",
      "mid_right",
      "lower_left",
      "lower_right",
      "deep_bg_left",
      "deep_bg_right",
      "podium_center",
    ];
    const id = preferred[i % preferred.length];
    return STUDIO_ZONES.find((z) => z.id === id) || STUDIO_ZONES[i % STUDIO_ZONES.length];
  }

  function zoneSideHint(zoneId) {
    if (zoneId.includes("left")) return "left";
    if (zoneId.includes("right")) return "right";
    if (zoneId.includes("arc") || zoneId.includes("upper")) return "top";
    if (zoneId.includes("podium") || zoneId.includes("lower")) return "bottom";
    return "field";
  }

  function sampleInZone(zone, w, h, i, salt) {
    const u = (Math.random() + ((i * 0.37 + salt) % 1) * 0.4) % 1;
    const v = (Math.random() + ((i * 0.53 + salt * 1.7) % 1) * 0.4) % 1;
    let x = zone.x + u * Math.max(20, zone.w - w);
    let y = zone.y + v * Math.max(16, zone.h - h);
    x += (Math.random() - 0.5) * 44;
    y += (Math.random() - 0.5) * 36 + ((i % 7) - 3) * 9;
    x = Math.max(6, Math.min(1914 - w, x));
    y = Math.max(4, Math.min(1072 - h * 0.3, y));
    return { x, y };
  }

  /** Full-studio scatter across zones — never side-only, never a grid. */
  function spawnPose(i, count, depth) {
    const primary = pickZone(i, count);
    const w = 125 + depth * 95 + (Math.random() * 26 - 13);
    const h = w * 0.28;

    // Try primary zone, then rotate through other zones — never dump only to outer edges.
    const order = [primary].concat(
      STUDIO_ZONES.filter((z) => z.id !== primary.id).sort(
        () => Math.random() - 0.5,
      ),
    );

    for (let zi = 0; zi < order.length; zi++) {
      const zone = order[zi];
      for (let tries = 0; tries < 18; tries++) {
        const p = sampleInZone(zone, w, h, i, tries * 0.11 + zi);
        if (!overlapsKeepOut(p.x, p.y, w, h)) {
          return { x: p.x, y: p.y, side: zoneSideHint(zone.id), zone: zone.id, w };
        }
      }
    }

    // Absolute fallback: thin safe strips above logo / below bid / far sides
    const fallbacks = [
      { x: 200 + Math.random() * 400, y: 6 + Math.random() * 28 },
      { x: 1200 + Math.random() * 400, y: 6 + Math.random() * 28 },
      { x: 420 + Math.random() * 200, y: 960 + Math.random() * 70 },
      { x: 1280 + Math.random() * 200, y: 960 + Math.random() * 70 },
      { x: 40 + Math.random() * 260, y: 120 + Math.random() * 700 },
      { x: 1600 + Math.random() * 260, y: 120 + Math.random() * 700 },
    ];
    for (let f = 0; f < fallbacks.length; f++) {
      const p = fallbacks[f];
      if (!overlapsKeepOut(p.x, p.y, w, h)) {
        return { x: p.x, y: p.y, side: "field", zone: "fallback", w };
      }
    }
    return { x: 60, y: 200 + (i % 5) * 140, side: "left", zone: "fallback", w };
  }

  function steerFromKeepOut(s) {
    const w = s.w || 180;
    const h = w * 0.28;
    if (!overlapsKeepOut(s.x, s.y, w, h)) return;
    // Soft eject toward nearest open field (not hard snap to edges)
    const cx = s.x + w * 0.5;
    const cy = s.y + h * 0.5;
    const stageCx = 960;
    const stageCy = 540;
    const dx = cx - stageCx;
    const dy = cy - stageCy;
    if (Math.abs(dx) >= Math.abs(dy)) {
      s.x += dx >= 0 ? 40 : -40;
      s.vx = dx >= 0 ? Math.abs(s.vx || 0.05) : -Math.abs(s.vx || 0.05);
    } else {
      s.y += dy >= 0 ? 36 : -36;
      s.vy = dy >= 0 ? Math.abs(s.vy || 0.04) : -Math.abs(s.vy || 0.04);
    }
    // If still inside after soft push, teleport to a random safe zone sample
    if (overlapsKeepOut(s.x, s.y, w, h)) {
      const z = STUDIO_ZONES[Math.floor(Math.random() * STUDIO_ZONES.length)];
      s.x = z.x + Math.random() * Math.max(20, z.w - w);
      s.y = z.y + Math.random() * Math.max(16, z.h - h);
      s.zone = z.id;
      s.side = zoneSideHint(z.id);
      let guard = 0;
      while (overlapsKeepOut(s.x, s.y, w, h) && guard < 20) {
        s.x = z.x + Math.random() * Math.max(20, z.w - w);
        s.y = z.y + Math.random() * Math.max(16, z.h - h);
        guard += 1;
      }
    }
  }

  function clampPose(s) {
    const w = s.w || 180;
    const h = w * 0.28;
    // Soft screen bounds — allow slight overscan, then wrap
    if (s.x < -w * 0.35) s.x = 1920 - w * 0.65;
    if (s.x > 1920 - w * 0.35) s.x = -w * 0.2;
    if (s.y < -h * 0.6) s.y = 1080 - h * 0.4;
    if (s.y > 1080 + h * 0.2) s.y = -h * 0.3;
    steerFromKeepOut(s);
  }

  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const t = a[i];
      a[i] = a[j];
      a[j] = t;
    }
    return a;
  }

  function pickAssets(list, count) {
    if (!list.length || count <= 0) return [];
    const byEmirate = new Map();
    list.forEach((a) => {
      if (!byEmirate.has(a.emirate)) byEmirate.set(a.emirate, []);
      byEmirate.get(a.emirate).push(a);
    });

    const known = EMIRATE_BIAS.filter((e) => byEmirate.has(e));
    const rest = shuffle([...byEmirate.keys()].filter((e) => !known.includes(e)));
    const emirates = known.concat(rest);
    const picked = [];

    // When density >= catalog size, seed one of every approved file so Dubai A/B/C
    // and all emirates appear; then fill with duplicates.
    if (count >= list.length) {
      picked.push(...shuffle(list.slice()));
    }

    // Duplicates allowed. Prefer emirate variety; avoid identical neighbors.
    let guard = 0;
    while (picked.length < count && guard < count * 40) {
      guard += 1;
      const em = emirates[picked.length % Math.max(1, emirates.length)];
      const pool = byEmirate.get(em) || list;
      const prevFile = picked.length ? picked[picked.length - 1].file : null;
      const shuffled = shuffle(pool.slice());
      let next = shuffled.find((a) => a.file !== prevFile) || shuffled[0];
      if (next && next.file === prevFile && list.length > 1) {
        const alt = shuffle(list.filter((a) => a.file !== prevFile))[0];
        if (alt) next = alt;
      }
      if (!next) next = list[picked.length % list.length];
      picked.push(next);
    }
    return picked.slice(0, count);
  }

  async function loadCatalog() {
    if (catalog) return catalog;
    try {
      const res = await fetch(MANIFEST_URL, { cache: "force-cache" });
      if (!res.ok) throw new Error("manifest " + res.status);
      const data = await res.json();
      catalog = Array.isArray(data.assets) ? data.assets : [];
    } catch (e) {
      console.warn("[H2V4 bg plates] pack manifest missing", e);
      catalog = [];
    }
    return catalog;
  }

  function softBlurPx(depth) {
    // Far plates only — keep GPU cost low (max ~2.2px).
    if (depth < 0.42) return 0;
    return Math.min(2.2, (depth - 0.42) * 3.6);
  }

  function applyVisual(s, tSec) {
    const bob = Math.sin(tSec * s.bobSpeed + s.phase) * s.bobAmp;
    const sway = Math.cos(tSec * s.swaySpeed + s.phase * 0.9) * s.swayAmp;
    const rotY = Math.sin(tSec * s.rotSpeedY + s.phase) * s.rotAmpY;
    const rotX = Math.cos(tSec * s.rotSpeedX + s.phase * 1.25) * s.rotAmpX;
    const rotZ = Math.sin(tSec * s.rotSpeedZ + s.phase * 0.65) * s.rotAmpZ;
    s.el.style.transform =
      `translate3d(${s.x + sway}px, ${s.y + bob}px, ${s.z}px) ` +
      `rotateX(${rotX}deg) rotateY(${rotY}deg) rotateZ(${rotZ}deg) ` +
      `scale(${s.scale})`;
    s.el.style.opacity = String(s.opacity);
    const blur = s.blurPx || 0;
    s.el.style.filter =
      blur > 0.05
        ? `drop-shadow(0 10px 16px rgba(0,0,0,0.45)) blur(${blur.toFixed(2)}px)`
        : "drop-shadow(0 10px 16px rgba(0,0,0,0.45))";
  }

  function buildSync(assets) {
    const layer = document.getElementById("bg-plates");
    if (!layer) return;
    layer.innerHTML = "";
    sprites = [];

    const state = global.H2V4State?.getState?.();
    const count = resolveDensity(state?.new_style?.bg_density);
    const picked = pickAssets(assets, count);

    for (let i = 0; i < picked.length; i++) {
      const asset = picked[i];
      let depth = Math.random(); // 0 near → 1 far
      const pose = spawnPose(i, picked.length, depth);
      // Zone-biased depth layers: deep bg / mid / near podium
      if (pose.zone && pose.zone.indexOf("deep_bg") === 0) {
        depth = 0.62 + Math.random() * 0.35;
      } else if (pose.zone && pose.zone.indexOf("podium") === 0) {
        depth = Math.random() * 0.38;
      } else if (pose.zone && pose.zone.indexOf("arc") === 0) {
        depth = 0.4 + Math.random() * 0.45;
      } else if (pose.zone && pose.zone.indexOf("shoulder") === 0) {
        depth = 0.2 + Math.random() * 0.55;
      } else if (pose.zone && pose.zone.indexOf("upper") === 0) {
        depth = 0.35 + Math.random() * 0.45;
      } else {
        depth = 0.15 + Math.random() * 0.7;
      }
      const img = document.createElement("img");
      img.className = "bg-plate-sprite";
      img.alt = "";
      img.draggable = false;
      // Same coded URLs reuse browser HTTP/decode cache across duplicate sprites
      img.src = PACK_DIR + asset.file;
      img.decoding = "async";
      img.loading = "eager";
      // Perspective scaling — keep shoulder/arc plates a bit smaller to protect center AABB
      let wPx = Math.round(118 + (1 - depth) * 95 + (Math.random() * 18 - 9));
      if (pose.zone && (pose.zone.indexOf("shoulder") === 0 || pose.zone === "arc_center")) {
        wPx = Math.min(wPx, 150);
      }
      pose.w = wPx;
      // Re-validate after width change
      if (overlapsKeepOut(pose.x, pose.y, pose.w, pose.w * 0.28)) {
        const z = STUDIO_ZONES.find((zz) => zz.id === pose.zone) || STUDIO_ZONES[0];
        const p = sampleInZone(z, pose.w, pose.w * 0.28, i, 0.9);
        if (!overlapsKeepOut(p.x, p.y, pose.w, pose.w * 0.28)) {
          pose.x = p.x;
          pose.y = p.y;
        } else {
          pose.x = pose.zone && pose.zone.indexOf("right") >= 0 ? 1580 : 40;
          pose.y = 100 + Math.random() * 700;
        }
      }
      img.width = wPx;
      img.style.width = `${wPx}px`;
      img.style.height = "auto";

      // Near = larger / faster / sharper; far = smaller / slower / softer
      const nearFactor = 1 - depth;
      const scale = 0.78 + nearFactor * 0.42;
      const z = -60 - depth * 260;
      const opacity = 0.38 + nearFactor * 0.34;
      const parallax = 0.45 + nearFactor * 0.9;

      const sprite = {
        el: img,
        file: asset.file,
        emirate: asset.emirate,
        code: asset.code,
        x: pose.x,
        y: pose.y,
        side: pose.side,
        zone: pose.zone,
        w: pose.w,
        depth,
        scale,
        z,
        opacity,
        blurPx: softBlurPx(depth),
        // Slow horizontal drift dominant; light vertical float
        vx: (Math.random() < 0.5 ? -1 : 1) * (0.045 + Math.random() * 0.09) * parallax,
        vy: (Math.random() < 0.5 ? -1 : 1) * (0.02 + Math.random() * 0.05) * parallax,
        bobAmp: 3 + nearFactor * 5,
        bobSpeed: 0.22 + Math.random() * 0.28,
        swayAmp: 2 + nearFactor * 4,
        swaySpeed: 0.16 + Math.random() * 0.2,
        phase: Math.random() * Math.PI * 2,
        rotAmpX: 2.5 + Math.random() * 3.5,
        rotAmpY: 5 + Math.random() * 8,
        rotAmpZ: 1.2 + Math.random() * 2.4,
        rotSpeedX: 0.1 + Math.random() * 0.16,
        rotSpeedY: 0.12 + Math.random() * 0.22,
        rotSpeedZ: 0.08 + Math.random() * 0.14,
        parallax,
      };
      applyVisual(sprite, 0);
      layer.appendChild(img);
      sprites.push(sprite);
    }

    built = true;
    building = false;
    layer.setAttribute("aria-hidden", "false");
    lastBuildSig = buildSignature(state);
  }

  function buildSignature(state) {
    const ns = state?.new_style || {};
    return [ns.bg_motion_enabled ? 1 : 0, resolveDensity(ns.bg_density)].join("|");
  }

  function clear() {
    const layer = document.getElementById("bg-plates");
    if (layer) {
      layer.innerHTML = "";
      layer.setAttribute("aria-hidden", "true");
    }
    sprites = [];
    built = false;
    building = false;
    lastBuildSig = "";
    lastTs = 0;
  }

  function stopLoop() {
    if (raf) {
      cancelAnimationFrame(raf);
      raf = 0;
    }
    lastTs = 0;
  }

  function ensureLoop() {
    if (!raf) raf = requestAnimationFrame(tick);
  }

  function rebuildIfNeeded() {
    const state = global.H2V4State?.getState?.();
    if (!isEnabled(state)) {
      if (built || building) clear();
      stopLoop();
      return;
    }
    const sig = buildSignature(state);
    if (built && sig === lastBuildSig) return;
    if (building) return;
    building = true;
    built = false;
    loadCatalog().then((assets) => {
      const st = global.H2V4State?.getState?.();
      if (!isEnabled(st)) {
        building = false;
        clear();
        stopLoop();
        return;
      }
      buildSync(assets);
      if (isPlaying(st)) ensureLoop();
      else stopLoop();
    });
  }

  function tick(now) {
    raf = 0;
    const state = global.H2V4State?.getState?.();
    if (!isEnabled(state)) {
      if (built || building) clear();
      stopLoop();
      return;
    }
    if (!isPlaying(state)) {
      stopLoop();
      return;
    }
    if (!built && !building) {
      rebuildIfNeeded();
      ensureLoop();
      return;
    }

    const speed = resolveSpeed(state.new_style.bg_speed);
    const tSec = now * 0.001;
    const dt = lastTs ? Math.min(0.05, (now - lastTs) / 1000) : 0.016;
    lastTs = now;
    const step = speed * dt * 60; // normalize to ~60fps units

    sprites.forEach((s) => {
      s.x += s.vx * step;
      s.y += s.vy * step;
      // Mild direction drift variety — no hard side-corridor pinning
      if ((s.phase * 10 + now * 0.0002) % 1 < 0.002) {
        s.vx += (Math.random() - 0.5) * 0.01;
        s.vy += (Math.random() - 0.5) * 0.008;
        const vmax = 0.16 * (s.parallax || 1);
        s.vx = Math.max(-vmax, Math.min(vmax, s.vx));
        s.vy = Math.max(-vmax * 0.7, Math.min(vmax * 0.7, s.vy));
      }
      clampPose(s);
      applyVisual(s, tSec);
    });

    ensureLoop();
  }

  function syncFromState() {
    const state = global.H2V4State?.getState?.();
    if (!isEnabled(state)) {
      clear();
      stopLoop();
      return;
    }
    rebuildIfNeeded();
    if (isPlaying(state)) {
      if (built) ensureLoop();
    } else {
      stopLoop();
      // Freeze current poses (or build once then freeze)
      if (!built && !building) rebuildIfNeeded();
    }
  }

  function start() {
    if (!subscribed && global.H2V4State?.subscribe) {
      subscribed = true;
      global.H2V4State.subscribe((kind) => {
        if (kind === "state" || kind === "lot_change") syncFromState();
      });
    }
    syncFromState();
  }

  function stop() {
    stopLoop();
  }

  function setPlaying(on) {
    global.H2V4State?.patch?.({
      new_style: { bg_motion_playing: !!on },
    });
  }

  function setEnabled(on) {
    global.H2V4State?.patch?.({
      new_style: {
        bg_motion_enabled: !!on,
        bg_motion_playing: on ? true : false,
      },
    });
  }

  global.H2V4BgPlatesFx = {
    build: rebuildIfNeeded,
    clear,
    start,
    stop,
    syncFromState,
    setPlaying,
    setEnabled,
    loadCatalog,
    resolveDensity,
    resolveSpeed,
    KEEP_OUT,
    STUDIO_ZONES,
    DENSITY_OPTS,
    SPEED_PRESETS,
    ASSET_NOTE:
      "Final floating pack (12 approved PNGs) — letter/blank only, no registration digits. Motion off by default.",
  };
})(window);
