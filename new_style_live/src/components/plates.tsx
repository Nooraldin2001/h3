/**
 * UAE license plate SVG designs.
 * Each emirate has distinct colors, layout, and branding.
 * Code and number are rendered as separate text overlays.
 */

export interface PlateOverlayConfig {
  codeStyle: React.CSSProperties
  numberStyle: React.CSSProperties
}

export interface PlateDesign {
  id: string
  label: string
  overlay: PlateOverlayConfig
  svg: React.ReactElement
}

const PLATE_W = 470
const PLATE_H = 110

// Shared plate border shadow
const plateShadow = "drop-shadow(0 4px 24px rgba(0,0,0,0.5))"

export function DubaiPlate({ code, number }: { code: string; number: string }) {
  return (
    <svg viewBox={`0 0 ${PLATE_W} ${PLATE_H}`} width="100%" height="100%" style={{ display: "block" }}>
      {/* Background */}
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="#f8f8f8" />
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="none" stroke="#c0c0c0" strokeWidth="2" />

      {/* Left blue panel */}
      <rect width="90" height={PLATE_H} rx="10" fill="#1a3a7e" />
      <rect x="80" width="10" height={PLATE_H} fill="#1a3a7e" />

      {/* UAE flag stripes in left panel */}
      <rect x="8" y="18" width="6" height="25" rx="1" fill="#00732f" />
      <rect x="8" y="43" width="6" height="24" rx="1" fill="#fff" />
      <rect x="8" y="67" width="6" height="25" rx="1" fill="#ef3340" />
      <rect x="14" y="18" width="3" height="74" fill="#ef3340" />

      {/* DUBAI text */}
      <text
        x="54"
        y="44"
        textAnchor="middle"
        fill="#ffffff"
        fontSize="17"
        fontWeight="800"
        fontFamily="Arial Black, Arial, sans-serif"
        letterSpacing="1"
      >
        DUBAI
      </text>

      {/* Code letter */}
      {code && (
        <text
          x="54"
          y="76"
          textAnchor="middle"
          fill="#ffffff"
          fontSize="24"
          fontWeight="700"
          fontFamily="Arial, sans-serif"
        >
          {code}
        </text>
      )}

      {/* Number */}
      {number && (
        <text
          x="290"
          y="78"
          textAnchor="middle"
          fill="#111111"
          fontSize="62"
          fontWeight="800"
          fontFamily="Arial Black, Arial, sans-serif"
          letterSpacing="2"
        >
          {number}
        </text>
      )}
    </svg>
  )
}

export function DubaiYellowPlate({ code, number }: { code: string; number: string }) {
  return (
    <svg viewBox={`0 0 ${PLATE_W} ${PLATE_H}`} width="100%" height="100%" style={{ display: "block" }}>
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="#ffd700" />
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="none" stroke="#c8a800" strokeWidth="2" />

      {/* Left panel */}
      <rect width="90" height={PLATE_H} rx="10" fill="#1a3a7e" />
      <rect x="80" width="10" height={PLATE_H} fill="#1a3a7e" />

      {/* UAE flag */}
      <rect x="8" y="18" width="6" height="25" rx="1" fill="#00732f" />
      <rect x="8" y="43" width="6" height="24" rx="1" fill="#fff" />
      <rect x="8" y="67" width="6" height="25" rx="1" fill="#ef3340" />
      <rect x="14" y="18" width="3" height="74" fill="#ef3340" />

      <text x="54" y="44" textAnchor="middle" fill="#ffffff" fontSize="17" fontWeight="800" fontFamily="Arial Black, Arial, sans-serif" letterSpacing="1">DUBAI</text>
      {code && <text x="54" y="76" textAnchor="middle" fill="#ffffff" fontSize="24" fontWeight="700" fontFamily="Arial, sans-serif">{code}</text>}
      {number && <text x="290" y="78" textAnchor="middle" fill="#1a1a1a" fontSize="62" fontWeight="800" fontFamily="Arial Black, Arial, sans-serif" letterSpacing="2">{number}</text>}
    </svg>
  )
}

export function AbuDhabiPlate({ code, number }: { code: string; number: string }) {
  return (
    <svg viewBox={`0 0 ${PLATE_W} ${PLATE_H}`} width="100%" height="100%" style={{ display: "block" }}>
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="#f5f5f5" />
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="none" stroke="#aaa" strokeWidth="2" />

      {/* Top and bottom red stripes */}
      <rect width={PLATE_W} height="12" rx="0" fill="#ef3340" />
      <rect y={PLATE_H - 12} width={PLATE_W} height="12" rx="0" fill="#ef3340" />
      <rect width={PLATE_W} height="12" rx="10" fill="#ef3340" />
      <rect y={PLATE_H - 12} width={PLATE_W} height="12" rx="10" fill="#ef3340" />

      {/* Left section */}
      <rect width="110" height={PLATE_H} rx="10" fill="#1a3a7e" />
      <rect x="100" width="10" height={PLATE_H} fill="#1a3a7e" />

      {/* Abu Dhabi text (Arabic) */}
      <text x="55" y="50" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="700" fontFamily="Arial, sans-serif">أبوظبي</text>
      <text x="55" y="72" textAnchor="middle" fill="#ffffffcc" fontSize="11" fontWeight="600" fontFamily="Arial, sans-serif">ABU DHABI</text>

      {/* UAE flag */}
      <rect x="8" y="20" width="5" height="70" fill="#00732f" />
      <rect x="13" y="20" width="5" height="70" fill="#fff" />
      <rect x="18" y="20" width="5" height="70" fill="#ef3340" />
      <rect x="8" y="20" width="15" height="5" fill="#000" />

      {code && (
        <text x="55" y="90" textAnchor="middle" fill="#ffffffaa" fontSize="16" fontWeight="600" fontFamily="Arial, sans-serif">{code}</text>
      )}

      {number && (
        <text x="300" y="78" textAnchor="middle" fill="#111" fontSize="62" fontWeight="800" fontFamily="Arial Black, Arial, sans-serif" letterSpacing="2">{number}</text>
      )}
    </svg>
  )
}

export function SharjahPlate({ code, number }: { code: string; number: string }) {
  return (
    <svg viewBox={`0 0 ${PLATE_W} ${PLATE_H}`} width="100%" height="100%" style={{ display: "block" }}>
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="#f8f8f8" />
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="none" stroke="#bbb" strokeWidth="2" />

      <rect width="105" height={PLATE_H} rx="10" fill="#1a5c2e" />
      <rect x="95" width="10" height={PLATE_H} fill="#1a5c2e" />

      <text x="52" y="48" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="700" fontFamily="Arial, sans-serif">الشارقة</text>
      <text x="52" y="66" textAnchor="middle" fill="#ffffffcc" fontSize="10" fontWeight="600" fontFamily="Arial, sans-serif">SHARJAH</text>
      {code && <text x="52" y="88" textAnchor="middle" fill="#ffffffaa" fontSize="18" fontWeight="700" fontFamily="Arial, sans-serif">{code}</text>}

      {number && <text x="295" y="78" textAnchor="middle" fill="#111" fontSize="62" fontWeight="800" fontFamily="Arial Black, Arial, sans-serif" letterSpacing="2">{number}</text>}
    </svg>
  )
}

export function AjmanPlate({ code, number }: { code: string; number: string }) {
  return (
    <svg viewBox={`0 0 ${PLATE_W} ${PLATE_H}`} width="100%" height="100%" style={{ display: "block" }}>
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="#f8f8f8" />
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="none" stroke="#bbb" strokeWidth="2" />

      <rect width="105" height={PLATE_H} rx="10" fill="#8B0000" />
      <rect x="95" width="10" height={PLATE_H} fill="#8B0000" />

      <text x="52" y="48" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="700" fontFamily="Arial, sans-serif">عجمان</text>
      <text x="52" y="66" textAnchor="middle" fill="#ffffffcc" fontSize="10" fontWeight="600" fontFamily="Arial, sans-serif">AJMAN</text>
      {code && <text x="52" y="88" textAnchor="middle" fill="#ffffffaa" fontSize="18" fontWeight="700" fontFamily="Arial, sans-serif">{code}</text>}

      {number && <text x="295" y="78" textAnchor="middle" fill="#111" fontSize="62" fontWeight="800" fontFamily="Arial Black, Arial, sans-serif" letterSpacing="2">{number}</text>}
    </svg>
  )
}

export function RAKPlate({ code, number }: { code: string; number: string }) {
  return (
    <svg viewBox={`0 0 ${PLATE_W} ${PLATE_H}`} width="100%" height="100%" style={{ display: "block" }}>
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="#f8f8f8" />
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="none" stroke="#bbb" strokeWidth="2" />

      <rect width="105" height={PLATE_H} rx="10" fill="#00529b" />
      <rect x="95" width="10" height={PLATE_H} fill="#00529b" />

      <text x="52" y="44" textAnchor="middle" fill="#fff" fontSize="11" fontWeight="700" fontFamily="Arial, sans-serif">رأس الخيمة</text>
      <text x="52" y="62" textAnchor="middle" fill="#ffffffcc" fontSize="9" fontWeight="600" fontFamily="Arial, sans-serif">RAS AL KHAIMAH</text>
      {code && <text x="52" y="86" textAnchor="middle" fill="#ffffffaa" fontSize="18" fontWeight="700" fontFamily="Arial, sans-serif">{code}</text>}

      {number && <text x="295" y="78" textAnchor="middle" fill="#111" fontSize="62" fontWeight="800" fontFamily="Arial Black, Arial, sans-serif" letterSpacing="2">{number}</text>}
    </svg>
  )
}

export function UAQPlate({ code, number }: { code: string; number: string }) {
  return (
    <svg viewBox={`0 0 ${PLATE_W} ${PLATE_H}`} width="100%" height="100%" style={{ display: "block" }}>
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="#f8f8f8" />
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="none" stroke="#bbb" strokeWidth="2" />

      <rect width="105" height={PLATE_H} rx="10" fill="#3a0070" />
      <rect x="95" width="10" height={PLATE_H} fill="#3a0070" />

      <text x="52" y="44" textAnchor="middle" fill="#fff" fontSize="11" fontWeight="700" fontFamily="Arial, sans-serif">أم القيوين</text>
      <text x="52" y="62" textAnchor="middle" fill="#ffffffcc" fontSize="9" fontWeight="600" fontFamily="Arial, sans-serif">UMM AL QUWAIN</text>
      {code && <text x="52" y="86" textAnchor="middle" fill="#ffffffaa" fontSize="18" fontWeight="700" fontFamily="Arial, sans-serif">{code}</text>}

      {number && <text x="295" y="78" textAnchor="middle" fill="#111" fontSize="62" fontWeight="800" fontFamily="Arial Black, Arial, sans-serif" letterSpacing="2">{number}</text>}
    </svg>
  )
}

export function FujairahPlate({ code, number }: { code: string; number: string }) {
  return (
    <svg viewBox={`0 0 ${PLATE_W} ${PLATE_H}`} width="100%" height="100%" style={{ display: "block" }}>
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="#f8f8f8" />
      <rect width={PLATE_W} height={PLATE_H} rx="10" fill="none" stroke="#bbb" strokeWidth="2" />

      <rect width="105" height={PLATE_H} rx="10" fill="#006633" />
      <rect x="95" width="10" height={PLATE_H} fill="#006633" />

      <text x="52" y="48" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="700" fontFamily="Arial, sans-serif">الفجيرة</text>
      <text x="52" y="66" textAnchor="middle" fill="#ffffffcc" fontSize="10" fontWeight="600" fontFamily="Arial, sans-serif">FUJAIRAH</text>
      {code && <text x="52" y="88" textAnchor="middle" fill="#ffffffaa" fontSize="18" fontWeight="700" fontFamily="Arial, sans-serif">{code}</text>}

      {number && <text x="295" y="78" textAnchor="middle" fill="#111" fontSize="62" fontWeight="800" fontFamily="Arial Black, Arial, sans-serif" letterSpacing="2">{number}</text>}
    </svg>
  )
}

export const PLATE_TYPES = [
  "dubai",
  "abu_dhabi",
  "dubai_yellow",
  "sharjah",
  "ajman",
  "ras_al_khaimah",
  "umm_al_quwain",
  "fujairah",
]

export function PlateRenderer({
  plateType,
  code,
  number,
}: {
  plateType: string
  code: string
  number: string
}) {
  switch (plateType) {
    case "dubai":
      return <DubaiPlate code={code} number={number} />
    case "dubai_yellow":
      return <DubaiYellowPlate code={code} number={number} />
    case "abu_dhabi":
      return <AbuDhabiPlate code={code} number={number} />
    case "sharjah":
      return <SharjahPlate code={code} number={number} />
    case "ajman":
      return <AjmanPlate code={code} number={number} />
    case "ras_al_khaimah":
      return <RAKPlate code={code} number={number} />
    case "umm_al_quwain":
      return <UAQPlate code={code} number={number} />
    case "fujairah":
      return <FujairahPlate code={code} number={number} />
    default:
      return <DubaiPlate code={code} number={number} />
  }
}
