import { useEffect, useRef, useState } from "react"

interface PriceDisplayProps {
  price: string
}

function formatPrice(price: string): string {
  const n = parseFloat(price.replace(/,/g, ""))
  if (isNaN(n)) return price
  return n.toLocaleString("en-AE")
}

export function PriceDisplay({ price }: PriceDisplayProps) {
  const [animating, setAnimating] = useState(false)
  const prevPrice = useRef(price)

  useEffect(() => {
    if (price !== prevPrice.current && price) {
      setAnimating(true)
      const t = setTimeout(() => setAnimating(false), 700)
      prevPrice.current = price
      return () => clearTimeout(t)
    }
  }, [price])

  if (!price) return null

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 4,
    }}>
      {/* Arabic label */}
      <div style={{
        fontSize: "clamp(11px, 1.4vw, 15px)",
        color: "rgba(201,165,53,0.7)",
        fontFamily: "var(--font-arabic)",
        letterSpacing: "0.05em",
        direction: "rtl",
        fontWeight: 600,
      }}>
        السعر الحالي
      </div>

      {/* Price container */}
      <div style={{
        position: "relative",
        display: "flex",
        alignItems: "baseline",
        gap: "clamp(8px, 1.2vw, 16px)",
        padding: "clamp(10px, 1.5vh, 18px) clamp(24px, 4vw, 48px)",
        background: "linear-gradient(135deg, rgba(20,16,42,0.9) 0%, rgba(10,8,22,0.95) 100%)",
        border: "1px solid rgba(201,165,53,0.2)",
        borderRadius: 6,
        backdropFilter: "blur(12px)",
        boxShadow: "0 0 40px rgba(201,165,53,0.08), inset 0 1px 0 rgba(255,255,255,0.04)",
        animation: animating ? "price-pulse 0.65s ease-out both" : undefined,
        direction: "ltr",
      }}>
        {/* Gold corner accents */}
        <div style={{ position: "absolute", top: 0, left: 0, width: 20, height: 20, borderTop: "2px solid rgba(201,165,53,0.5)", borderLeft: "2px solid rgba(201,165,53,0.5)", borderRadius: "6px 0 0 0" }} />
        <div style={{ position: "absolute", top: 0, right: 0, width: 20, height: 20, borderTop: "2px solid rgba(201,165,53,0.5)", borderRight: "2px solid rgba(201,165,53,0.5)", borderRadius: "0 6px 0 0" }} />
        <div style={{ position: "absolute", bottom: 0, left: 0, width: 20, height: 20, borderBottom: "2px solid rgba(201,165,53,0.5)", borderLeft: "2px solid rgba(201,165,53,0.5)", borderRadius: "0 0 0 6px" }} />
        <div style={{ position: "absolute", bottom: 0, right: 0, width: 20, height: 20, borderBottom: "2px solid rgba(201,165,53,0.5)", borderRight: "2px solid rgba(201,165,53,0.5)", borderRadius: "0 0 6px 0" }} />

        <span style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(16px, 2vw, 24px)",
          fontWeight: 600,
          color: "rgba(201,165,53,0.8)",
          letterSpacing: "0.08em",
        }}>
          AED
        </span>

        <span style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(36px, 5.5vw, 72px)",
          fontWeight: 700,
          color: "var(--white-soft)",
          lineHeight: 1,
          letterSpacing: "0.02em",
          textShadow: "0 0 30px rgba(201,165,53,0.15)",
          fontVariantNumeric: "tabular-nums",
        }}>
          {formatPrice(price)}
        </span>
      </div>
    </div>
  )
}
