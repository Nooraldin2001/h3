import { useMemo } from "react"

interface NewsTickerProps {
  message: string
}

export function NewsTicker({ message }: NewsTickerProps) {
  if (!message) return null

  // Scale duration by message length for consistent speed
  const duration = useMemo(() => {
    const base = 18
    const extra = Math.max(0, message.length - 40) * 0.15
    return base + extra
  }, [message])

  return (
    <div
      style={{
        position: "relative",
        zIndex: 30,
        flexShrink: 0,
        height: "clamp(38px, 5vh, 52px)",
        overflow: "hidden",
        borderTop: "1px solid rgba(124,58,237,0.2)",
      }}
      aria-label="شريط الأخبار"
      aria-live="polite"
    >
      {/* Background with gradient */}
      <div style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(90deg, rgba(91,33,182,0.85) 0%, rgba(10,5,21,0.92) 8%, rgba(10,5,21,0.92) 92%, rgba(91,33,182,0.85) 100%)",
        backdropFilter: "blur(8px)",
      }} />

      {/* Left bullet */}
      <div style={{
        position: "absolute",
        left: 0,
        top: 0,
        bottom: 0,
        width: "clamp(60px, 8vw, 90px)",
        background: "linear-gradient(90deg, var(--red-accent) 0%, rgba(200,28,28,0.8) 70%, transparent 100%)",
        zIndex: 2,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        paddingLeft: 10,
      }}>
        <div style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: "#fff",
          boxShadow: "0 0 6px #fff",
        }} />
        <span style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(8px, 1vw, 11px)",
          color: "#fff",
          fontWeight: 700,
          letterSpacing: "0.12em",
        }}>
          LIVE
        </span>
      </div>

      {/* Right fade mask */}
      <div style={{
        position: "absolute",
        right: 0,
        top: 0,
        bottom: 0,
        width: 60,
        background: "linear-gradient(270deg, rgba(10,5,21,0.95) 0%, transparent 100%)",
        zIndex: 2,
      }} />

      {/* Scrolling text */}
      <div style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        overflow: "hidden",
        paddingLeft: "clamp(60px, 8vw, 90px)",
      }}>
        <div style={{
          display: "inline-flex",
          whiteSpace: "nowrap",
          animation: `ticker-rtl ${duration}s linear infinite`,
          direction: "rtl",
          gap: "4em",
        }}>
          <span style={{
            fontFamily: "var(--font-arabic)",
            fontSize: "clamp(13px, 1.8vw, 18px)",
            color: "var(--white-soft)",
            fontWeight: 400,
            letterSpacing: "0.02em",
          }}>
            {message}
          </span>
          {/* Duplicate for seamless loop */}
          <span style={{
            fontFamily: "var(--font-arabic)",
            fontSize: "clamp(13px, 1.8vw, 18px)",
            color: "var(--white-soft)",
            fontWeight: 400,
            letterSpacing: "0.02em",
            marginRight: "4em",
          }}>
            {message}
          </span>
        </div>
      </div>
    </div>
  )
}
