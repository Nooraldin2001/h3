export interface AuctionState {
  plate_type: string
  code: string
  number: string
  price: string
  message: string
  alert_message: string
  timer_seconds: number
  timer_remaining_seconds: number
  timer_active: boolean
  display_token: string
}

export interface SoldDetail {
  plateType: string
  code: string
  number: string
  price: string
}
