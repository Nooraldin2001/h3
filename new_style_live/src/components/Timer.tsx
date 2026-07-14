import { useMemo } from "react"

interface TimerProps {
  remainingSeconds: number
  totalSeconds: number
  active: boolean
}

export function Timer({ remainingSeconds, totalSeconds, active }: TimerProps) {
  const { mm, ss } = useMemo(() => {
    const s = Math.max(0, remainingSeconds)
    return {
      mm: String(Math.floor(s / 60)).padStart(2, "0"),
      ss: String(s % 60).padStart(2, "0"),
    }
  }, [remainingSeconds])

  const urgent = active && remainingSeconds <= 10 && remainingSeconds > 0
  const expired = remainingSeconds === 0

  const progress = totalSeconds > 0 ? Math.max(0, remainingSeconds / totalSeconds) : 0

  const color = urgent ? "var(--red-glow)" : expired ? "rgba(167,139,250,0.5)" : "var(--white-soft)"
  const glowColor = urgent
    ? "0 0 30px rgba(239,68,68,0.6), 0 0 60px rgba(239,68,68,0.3)"
    : expired
    ? "none"
    : "0 0 20px rgba(167,139,250,0.2)"

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      {/* Progress arc */}
      <div style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg
          width="clamp(90px, 12vw, 140px)"
          viewBox="0 0 140 20"
          style={{ position: "absolute", bottom: -4 }}
        >
          <rect x="0" y="6" width="140" height="3" rx="1.5" fill="rgba(255,255,255,0.06)" />
          <rect
            x="0"
            y="6"
            width={140 * progress}
            height="3"
            rx="1.5"
            fill={urgent ? "var(--red-accent)" : "var(--purple-vivid)"}
            style={{ transition: "width 0.9s linear" }}
          />
        </svg>

        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(52px, 8vw, 100px)",
            fontWeight: 700,
            lineHeight: 1,
            color,
            textShadow: glowColor,
            letterSpacing: "0.04em",
            fontVariantNumeric: "tabular-nums",
            animation: urgent ? "urgent-glow 1.2s ease-in-out infinite" : undefined,
            transition: "color 0.5s ease",
            userSelect: "none",
          }}
        >
          <span>{mm}</span>
          <span style={{ opacity: expired ? 0.3 : 0.7, margin: "0 2px" }}>:</span>
          <span>{ss}</span>
        </div>
      </div>

      {/* State label */}
      <div style={{
        fontFamily: "var(--font-display)",
        fontSize: "clamp(9px, 1.1vw, 12px)",
        letterSpacing: "0.2em",
        textTransform: "uppercase",
        color: urgent ? "var(--red-glow)" : expired ? "rgba(167,139,250,0.4)" : "rgba(167,139,250,0.5)",
        transition: "color 0.5s ease",
      }}>
        {expired ? "CLOSED" : urgent ? "CLOSING" : active ? "COUNTDOWN" : "STANDBY"}
      </div>
    </div>
  )
}
