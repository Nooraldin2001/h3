import { useEffect, useState, useMemo } from "react"
import type { SoldDetail } from "../types"
import { PlateRenderer } from "./plates"

interface SoldOverlayProps {
  detail: SoldDetail
  onDone: () => void
}

interface Particle {
  id: number
  x: number
  y: number
  size: number
  color: string
  delay: number
  duration: number
  shape: "rect" | "circle" | "diamond"
}

const PARTICLE_COLORS = [
  "#c9a535", "#edd97a", "#f0e0a0", // gold family
  "#7c3aed", "#a78bfa", "#6d28d9", // purple family
  "#dc2626", "#ef4444",             // red
  "#ffffff", "#f5f0ff",             // white
]

function generateParticles(count: number): Particle[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: 5 + Math.random() * 90,
    y: 5 + Math.random() * 60,
    size: 4 + Math.random() * 10,
    color: PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)],
    delay: Math.random() * 1.5,
    duration: 1.8 + Math.random() * 1.4,
    shape: (["rect", "circle", "diamond"] as const)[Math.floor(Math.random() * 3)],
  }))
}

function formatPrice(price: string): string {
  const n = parseFloat(price.replace(/,/g, ""))
  if (isNaN(n)) return price
  return n.toLocaleString("en-AE")
}

export function SoldOverlay({ detail, onDone }: SoldOverlayProps) {
  const [phase, setPhase] = useState<"glow" | "fly" | "reveal" | "fade" | "done">("glow")
  const particles = useMemo(() => generateParticles(60), [])

  useEffect(() => {
    const t1 = setTimeout(() => setPhase("fly"), 400)
    const t2 = setTimeout(() => setPhase("reveal"), 1200)
    const t3 = setTimeout(() => setPhase("fade"), 3800)
    const t4 = setTimeout(() => { setPhase("done"); onDone() }, 5000)
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4) }
  }, [onDone])

  const overlayOpacity = phase === "fade" ? 0 : phase === "done" ? 0 : 1

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      zIndex: 200,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      transition: "opacity 1.2s ease",
      opacity: overlayOpacity,
      pointerEvents: phase === "done" ? "none" : "auto",
    }}>
      {/* Dark overlay */}
      <div style={{
        position: "absolute",
        inset: 0,
        background: "rgba(6,3,13,0.88)",
        backdropFilter: "blur(4px)",
      }} />

      {/* Radial light burst */}
      {(phase === "reveal" || phase === "fade") && (
        <div style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "70vw",
          height: "70vw",
          background: "radial-gradient(circle, rgba(201,165,53,0.15) 0%, rgba(109,40,217,0.1) 40%, transparent 70%)",
          animation: "sold-reveal 0.6s ease-out both",
          borderRadius: "50%",
        }} />
      )}

      {/* Confetti particles */}
      {(phase === "reveal" || phase === "fade") && particles.map((p) => (
        <div
          key={p.id}
          style={{
            position: "absolute",
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.shape === "circle" ? p.size : p.size * 0.7,
            height: p.shape === "circle" ? p.size : p.size * 1.4,
            background: p.color,
            borderRadius: p.shape === "circle" ? "50%" : p.shape === "diamond" ? "2px" : "1px",
            transform: p.shape === "diamond" ? "rotate(45deg)" : undefined,
            opacity: 0,
            animation: `confetti-fall ${p.duration}s ${p.delay}s ease-in both`,
            boxShadow: p.color.includes("c9a") || p.color.includes("edd") ? `0 0 6px ${p.color}88` : undefined,
          }}
        />
      ))}

      {/* Flying plate */}
      {(phase === "glow" || phase === "fly") && (
        <div style={{
          position: "absolute",
          width: "clamp(300px, 45vw, 580px)",
          animation: phase === "fly" ? "plate-fly 0.85s cubic-bezier(0.4, 0, 0.2, 1) forwards" : undefined,
          filter: phase === "glow"
            ? "drop-shadow(0 0 40px rgba(201,165,53,0.6)) drop-shadow(0 0 80px rgba(109,40,217,0.4))"
            : "drop-shadow(0 0 20px rgba(201,165,53,0.3))",
          transition: "filter 0.4s ease",
        }}>
          <PlateRenderer
            plateType={detail.plateType}
            code={detail.code}
            number={detail.number}
          />
        </div>
      )}

      {/* Main celebration content */}
      {(phase === "reveal" || phase === "fade") && (
        <div style={{
          position: "relative",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "clamp(16px, 3vh, 32px)",
          animation: "sold-reveal 0.5s cubic-bezier(0.22, 1, 0.36, 1) both",
          textAlign: "center",
        }}>
          {/* Elegant rings */}
          <div style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "clamp(300px, 40vw, 500px)",
            height: "clamp(300px, 40vw, 500px)",
            borderRadius: "50%",
            border: "1px solid rgba(201,165,53,0.15)",
            pointerEvents: "none",
          }}>
            <div style={{
              position: "absolute",
              inset: "10%",
              borderRadius: "50%",
              border: "1px solid rgba(109,40,217,0.2)",
            }} />
            <div style={{
              position: "absolute",
              inset: "22%",
              borderRadius: "50%",
              border: "1px solid rgba(201,165,53,0.1)",
            }} />
          </div>

          {/* تم البيع */}
          <div style={{
            fontFamily: "var(--font-arabic)",
            fontSize: "clamp(52px, 9vw, 120px)",
            fontWeight: 900,
            background: "linear-gradient(135deg, #edd97a 0%, #c9a535 40%, #f0e0a0 70%, #c9a535 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            lineHeight: 1.1,
            direction: "rtl",
            textShadow: "none",
            filter: "drop-shadow(0 0 30px rgba(201,165,53,0.4))",
          }}>
            تم البيع
          </div>

          {/* Plate mini display */}
          <div style={{
            width: "clamp(260px, 36vw, 480px)",
            filter: "drop-shadow(0 8px 32px rgba(0,0,0,0.6)) drop-shadow(0 0 20px rgba(201,165,53,0.2))",
          }}>
            <PlateRenderer
              plateType={detail.plateType}
              code={detail.code}
              number={detail.number}
            />
          </div>

          {/* Price */}
          {detail.price && (
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 4,
            }}>
              <div style={{
                fontFamily: "var(--font-arabic)",
                fontSize: "clamp(11px, 1.3vw, 14px)",
                color: "rgba(201,165,53,0.6)",
                fontWeight: 600,
                direction: "rtl",
              }}>
                السعر النهائي
              </div>
              <div style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(28px, 4.5vw, 58px)",
                fontWeight: 700,
                color: "var(--white-soft)",
                letterSpacing: "0.04em",
                direction: "ltr",
              }}>
                <span style={{ fontSize: "0.55em", color: "rgba(201,165,53,0.8)", marginRight: 8 }}>AED</span>
                {formatPrice(detail.price)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
