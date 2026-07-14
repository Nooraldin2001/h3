import { useState, useEffect, useRef } from "react"
import { PlateRenderer, PLATE_TYPES } from "./plates"

interface PlateStageProps {
  plateType: string
  code: string
  number: string
  urgent: boolean
}

export function PlateStage({ plateType, code, number, urgent }: PlateStageProps) {
  const idle = !plateType && !code && !number
  const [carouselIndex, setCarouselIndex] = useState(0)
  const [plateKey, setPlateKey] = useState(0)
  const prevType = useRef(plateType)

  // Carousel in idle mode
  useEffect(() => {
    if (!idle) return
    const t = setInterval(() => {
      setCarouselIndex((i) => (i + 1) % PLATE_TYPES.length)
    }, 2800)
    return () => clearInterval(t)
  }, [idle])

  // Animate plate when type changes
  useEffect(() => {
    if (plateType !== prevType.current) {
      setPlateKey((k) => k + 1)
      prevType.current = plateType
    }
  }, [plateType])

  const displayType = idle ? PLATE_TYPES[carouselIndex] : plateType
  const displayCode = idle ? "" : code
  const displayNumber = idle ? "" : number

  return (
    <div style={{
      position: "relative",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      width: "100%",
      maxWidth: "clamp(400px, 60vw, 860px)",
    }}>
      {/* Spotlight glow behind plate */}
      <div style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        width: "90%",
        height: "200%",
        background: urgent
          ? "radial-gradient(ellipse, rgba(200,28,28,0.2) 0%, transparent 65%)"
          : "radial-gradient(ellipse, rgba(109,40,217,0.22) 0%, transparent 65%)",
        transition: "background 1s ease",
        pointerEvents: "none",
      }} />

      {/* Reflection line */}
      <div style={{
        position: "absolute",
        bottom: -14,
        left: "5%",
        width: "90%",
        height: 1,
        background: "linear-gradient(90deg, transparent, rgba(167,139,250,0.25), transparent)",
      }} />

      {/* Plate container */}
      <div
        key={idle ? carouselIndex : plateKey}
        style={{
          position: "relative",
          width: "100%",
          animation: "plate-enter 0.5s cubic-bezier(0.22, 1, 0.36, 1) both",
          filter: urgent
            ? "drop-shadow(0 0 24px rgba(239,68,68,0.5)) drop-shadow(0 8px 32px rgba(0,0,0,0.6))"
            : "drop-shadow(0 0 12px rgba(109,40,217,0.25)) drop-shadow(0 8px 32px rgba(0,0,0,0.7))",
          transition: "filter 0.8s ease",
        }}
      >
        <PlateRenderer
          plateType={displayType}
          code={displayCode}
          number={displayNumber}
        />
      </div>

      {/* Pedestal reflection */}
      <div style={{
        width: "80%",
        height: "clamp(14px, 2.5vw, 28px)",
        background: "linear-gradient(180deg, rgba(167,139,250,0.08) 0%, transparent 100%)",
        borderRadius: "0 0 50% 50%",
        marginTop: 4,
        opacity: idle ? 0.4 : 0.7,
        transition: "opacity 0.5s ease",
      }} />

      {/* Idle indicator */}
      {idle && (
        <div style={{
          marginTop: 12,
          fontSize: "clamp(10px, 1.2vw, 13px)",
          color: "rgba(167,139,250,0.45)",
          fontFamily: "var(--font-display)",
          letterSpacing: "0.2em",
          textTransform: "uppercase",
        }}>
          AWAITING NEXT LOT
        </div>
      )}
    </div>
  )
}
