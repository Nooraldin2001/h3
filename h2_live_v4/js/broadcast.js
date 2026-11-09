/**
 * H2 Auctions Live V4 — base screen only.
 * Mock auction data. No Django / production API.
 * Intentionally does not load V2/V3 live-display scripts.
 */
(function () {
  const MOCK = Object.freeze({
    brand: "H2 AUCTIONS",
    plateType: "dubai",
    code: "AA",
    number: "7777",
    bidAed: 1250000,
    timerTotalSeconds: 60,
    timerRemainingSeconds: 60,
  });

  function formatTimer(totalSeconds) {
    const safe = Math.max(0, Math.floor(Number(totalSeconds) || 0));
    const m = Math.floor(safe / 60);
    const s = safe % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }

  function formatBid(value) {
    return Math.floor(Number(value) || 0).toLocaleString("en-AE");
  }

  function render() {
    const code = document.getElementById("plate-code");
    const number = document.getElementById("plate-number");
    const bid = document.getElementById("bid-amount");
    const timer = document.getElementById("timer-value");
    const bar = document.getElementById("timer-bar");

    if (code) code.textContent = MOCK.code;
    if (number) number.textContent = MOCK.number;
    if (bid) bid.textContent = formatBid(MOCK.bidAed);
    if (timer) timer.textContent = formatTimer(MOCK.timerRemainingSeconds);
    if (bar) {
      const pct = Math.max(
        0,
        Math.min(100, (MOCK.timerRemainingSeconds / MOCK.timerTotalSeconds) * 100),
      );
      bar.style.width = `${pct}%`;
    }
  }

  // Base screen: static mock render only. No FX loops.
  render();
  window.H2_LIVE_V4_MOCK = MOCK;
})();
