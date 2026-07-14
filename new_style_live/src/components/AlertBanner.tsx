interface AlertBannerProps {
  message: string
}

export function AlertBanner({ message }: AlertBannerProps) {
  if (!message) return null

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        animation: "alert-in 0.35s cubic-bezier(0.22, 1, 0.36, 1) both",
        margin: "0 clamp(20px, 4vw, 56px)",
        borderRadius: 6,
        overflow: "hidden",
        transformOrigin: "top center",
      }}
    >
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "clamp(10px, 1.5vh, 14px) clamp(16px, 2.5vw, 28px)",
        background: "linear-gradient(90deg, rgba(200,28,28,0.15) 0%, rgba(200,28,28,0.08) 60%, transparent 100%)",
        borderLeft: "3px solid var(--red-accent)",
        backdropFilter: "blur(8px)",
        direction: "rtl",
        justifyContent: "flex-start",
      }}>
        {/* Warning icon */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
          <path
            d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
            stroke="var(--red-glow)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <line x1="12" y1="9" x2="12" y2="13" stroke="var(--red-glow)" strokeWidth="2" strokeLinecap="round" />
          <line x1="12" y1="17" x2="12.01" y2="17" stroke="var(--red-glow)" strokeWidth="2" strokeLinecap="round" />
        </svg>

        <span style={{
          fontFamily: "var(--font-arabic)",
          fontSize: "clamp(13px, 1.8vw, 18px)",
          fontWeight: 600,
          color: "var(--white-soft)",
          textShadow: "0 1px 4px rgba(0,0,0,0.4)",
          lineHeight: 1.4,
        }}>
          {message}
        </span>
      </div>
    </div>
  )
}
