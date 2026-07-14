import { useState, useEffect, useCallback } from "react"
import { Timer } from "./components/Timer"
import { PlateStage } from "./components/PlateStage"
import { PriceDisplay } from "./components/PriceDisplay"
import { AlertBanner } from "./components/AlertBanner"
import { NewsTicker } from "./components/NewsTicker"
import { SoldOverlay } from "./components/SoldOverlay"
import type { AuctionState, SoldDetail } from "./types"

const DEMO_STATES: AuctionState[] = [
  {
    plate_type: "dubai",
    code: "N",
    number: "65655",
    price: "250000",
    message: "مزاد علني مباشر لبيع وشراء الأرقام المميزة • H3 Auctions • العروض مستمرة",
    alert_message: "",
    timer_seconds: 60,
    timer_remaining_seconds: 45,
    timer_active: true,
    display_token: "demo",
  },
  {
    plate_type: "abu_dhabi",
    code: "A",
    number: "12",
    price: "1850000",
    message: "مزاد علني مباشر لبيع وشراء الأرقام المميزة • H3 Auctions • العروض مستمرة",
    alert_message: "آخر فرصة للمزايدة — السعر الحالي قابل للتغيير",
    timer_seconds: 60,
    timer_remaining_seconds: 8,
    timer_active: true,
    display_token: "demo",
  },
  {
    plate_type: "dubai_yellow",
    code: "B",
    number: "777",
    price: "500000",
    message: "مزاد علني مباشر لبيع وشراء الأرقام المميزة • H3 Auctions • العروض مستمرة",
    alert_message: "",
    timer_seconds: 60,
    timer_remaining_seconds: 0,
    timer_active: false,
    display_token: "demo",
  },
  {
    plate_type: "",
    code: "",
    number: "",
    price: "",
    message: "مزاد علني مباشر لبيع وشراء الأرقام المميزة • H3 Auctions • العروض مستمرة",
    alert_message: "",
    timer_seconds: 60,
    timer_remaining_seconds: 60,
    timer_active: false,
    display_token: "demo",
  },
]

export default function App() {
  const [demoIndex, setDemoIndex] = useState(0)
  const [state, setState] = useState<AuctionState>(DEMO_STATES[0])
  const [soldDetail, setSoldDetail] = useState<SoldDetail | null>(null)
  const [soldVisible, setSoldVisible] = useState(false)

  // Simulate live API ticking the timer down
  useEffect(() => {
    const interval = setInterval(() => {
      setState((prev) => {
        if (!prev.timer_active || prev.timer_remaining_seconds <= 0) return prev
        return { ...prev, timer_remaining_seconds: Math.max(0, prev.timer_remaining_seconds - 1) }
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const applyDemo = useCallback((idx: number) => {
    setDemoIndex(idx)
    setState({ ...DEMO_STATES[idx] })
  }, [])

  const triggerSold = useCallback(() => {
    const detail: SoldDetail = {
      plateType: state.plate_type,
      code: state.code,
      number: state.number,
      price: state.price,
    }
    setSoldDetail(detail)
    setSoldVisible(true)
  }, [state])

  // Expose sold trigger globally for control panel integration
  useEffect(() => {
    (window as any).triggerSoldCelebration = triggerSold
    const handler = (e: Event) => {
      const ce = e as CustomEvent
      setSoldDetail(ce.detail)
      setSoldVisible(true)
    }
    window.addEventListener("auction:sold", handler)
    return () => window.removeEventListener("auction:sold", handler)
  }, [triggerSold])

  const onSoldDone = useCallback(() => {
    setSoldVisible(false)
    setSoldDetail(null)
  }, [])

  const urgent = state.timer_active && state.timer_remaining_seconds <= 10 && state.timer_remaining_seconds > 0
  const expired = state.timer_remaining_seconds === 0 && state.timer_active

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "radial-gradient(ellipse 120% 80% at 50% 0%, #1a0d3d 0%, #0a0515 45%, #06030d 100%)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        fontFamily: "var(--font-arabic)",
      }}
    >
      {/* Ambient background lights */}
      <div style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        zIndex: 0,
      }}>
        <div style={{
          position: "absolute",
          top: "-10%",
          left: "50%",
          transform: "translateX(-50%)",
          width: "60%",
          height: "50%",
          background: "radial-gradient(ellipse, rgba(109,40,217,0.18) 0%, transparent 70%)",
          animation: "ambient-pulse 6s ease-in-out infinite",
        }} />
        <div style={{
          position: "absolute",
          bottom: "5%",
          left: "20%",
          width: "30%",
          height: "40%",
          background: "radial-gradient(ellipse, rgba(200,28,28,0.08) 0%, transparent 70%)",
        }} />
      </div>

      {/* Brand header */}
      <header style={{
        position: "relative",
        zIndex: 10,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "clamp(10px, 2vh, 22px) clamp(20px, 4vw, 56px)",
        borderBottom: "1px solid rgba(167,139,250,0.08)",
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 38,
            height: 38,
            borderRadius: "50%",
            background: "linear-gradient(135deg, var(--purple-vivid), var(--red-accent))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 15,
            fontWeight: 700,
            color: "#fff",
            fontFamily: "var(--font-display)",
            letterSpacing: 1,
            boxShadow: "0 0 18px rgba(124,58,237,0.5)",
          }}>H3</div>
          <span style={{
            fontSize: "clamp(11px, 1.4vw, 14px)",
            color: "rgba(167,139,250,0.7)",
            fontFamily: "var(--font-display)",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}>H3 Auctions</span>
        </div>

        <div style={{
          textAlign: "center",
          color: "rgba(237,232,255,0.55)",
          fontSize: "clamp(11px, 1.5vw, 15px)",
          lineHeight: 1.4,
          direction: "rtl",
        }}>
          مزاد علني مباشر لبيع وشراء الأرقام المميزة
        </div>

        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          fontSize: "clamp(10px, 1.1vw, 12px)",
          color: "rgba(201,165,53,0.6)",
          fontFamily: "var(--font-display)",
          letterSpacing: "0.1em",
        }}>
          <span style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "#22c55e",
            boxShadow: "0 0 6px #22c55e",
            display: "inline-block",
          }} />
          LIVE
        </div>
      </header>

      {/* Alert banner zone — fixed height so layout never shifts */}
      <div style={{ position: "relative", zIndex: 20, flexShrink: 0, height: state.alert_message ? "auto" : 0 }}>
        <AlertBanner message={state.alert_message} />
      </div>

      {/* Main stage */}
      <main style={{
        position: "relative",
        zIndex: 5,
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "clamp(16px, 3vh, 36px)",
        padding: "clamp(12px, 2vh, 28px) clamp(20px, 4vw, 56px)",
        minHeight: 0,
      }}>
        {/* Timer */}
        <Timer
          remainingSeconds={state.timer_remaining_seconds}
          totalSeconds={state.timer_seconds}
          active={state.timer_active}
        />

        {/* Plate hero */}
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", width: "100%", minHeight: 0 }}>
          <PlateStage
            plateType={state.plate_type}
            code={state.code}
            number={state.number}
            urgent={urgent}
          />
        </div>

        {/* Price */}
        <PriceDisplay price={state.price} />
      </main>

      {/* News ticker */}
      <NewsTicker message={state.message} />

      {/* Demo controls — small overlay for preview purposes */}
      <DemoControls
        demoIndex={demoIndex}
        onApply={applyDemo}
        onSold={triggerSold}
        total={DEMO_STATES.length}
      />

      {/* Sold overlay */}
      {soldVisible && soldDetail && (
        <SoldOverlay detail={soldDetail} onDone={onSoldDone} />
      )}
    </div>
  )
}

function DemoControls({
  demoIndex,
  onApply,
  onSold,
  total,
}: {
  demoIndex: number
  onApply: (i: number) => void
  onSold: () => void
  total: number
}) {
  const labels = ["Active", "Urgent", "Expired", "Idle"]
  return (
    <div style={{
      position: "fixed",
      bottom: 60,
      left: 16,
      zIndex: 100,
      display: "flex",
      gap: 6,
      flexWrap: "wrap",
      maxWidth: 260,
    }}>
      {Array.from({ length: total }, (_, i) => (
        <button
          key={i}
          onClick={() => onApply(i)}
          style={{
            padding: "4px 10px",
            fontSize: 11,
            fontFamily: "var(--font-display)",
            background: demoIndex === i ? "rgba(124,58,237,0.7)" : "rgba(20,16,42,0.8)",
            color: demoIndex === i ? "#fff" : "rgba(237,232,255,0.5)",
            border: `1px solid ${demoIndex === i ? "rgba(167,139,250,0.6)" : "rgba(167,139,250,0.15)"}`,
            borderRadius: 4,
            cursor: "pointer",
            backdropFilter: "blur(8px)",
          }}
        >
          {labels[i] ?? i}
        </button>
      ))}
      <button
        onClick={onSold}
        style={{
          padding: "4px 10px",
          fontSize: 11,
          fontFamily: "var(--font-display)",
          background: "rgba(200,28,28,0.6)",
          color: "#fff",
          border: "1px solid rgba(239,68,68,0.4)",
          borderRadius: 4,
          cursor: "pointer",
          backdropFilter: "blur(8px)",
        }}
      >
        SOLD
      </button>
    </div>
  )
}
