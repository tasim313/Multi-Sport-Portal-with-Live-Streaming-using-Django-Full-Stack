/**
 * WebSocket client utilities.
 * Manages connections to Django Channels WebSocket endpoints.
 */

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export type WSCallback = (data: unknown) => void
export type MessageHandler = (type: string, data: unknown) => void

export class SportWebSocket {
  private ws: WebSocket | null = null
  private url: string
  private handlers: Map<string, WSCallback[]> = new Map()
  private pingInterval: ReturnType<typeof setInterval> | null = null
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  private reconnectAttempts = 0
  private maxReconnects = 5

  constructor(path: string) {
    this.url = `${WS_BASE}${path}`
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        this.reconnectAttempts = 0
        this._startPing()
      }

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          const { type, data } = msg
          const callbacks = this.handlers.get(type) || []
          callbacks.forEach(cb => cb(data))
        } catch {
          // ignore malformed messages
        }
      }

      this.ws.onclose = () => {
        this._stopPing()
        this._scheduleReconnect()
      }

      this.ws.onerror = () => {
        this.ws?.close()
      }
    } catch {
      this._scheduleReconnect()
    }
  }

  on(type: string, callback: WSCallback): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, [])
    }
    this.handlers.get(type)!.push(callback)

    // Return unsubscribe function
    return () => {
      const cbs = this.handlers.get(type) || []
      this.handlers.set(type, cbs.filter(cb => cb !== callback))
    }
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  disconnect(): void {
    this._stopPing()
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout)
    this.ws?.close()
    this.ws = null
  }

  private _startPing(): void {
    this.pingInterval = setInterval(() => {
      this.send({ type: 'ping' })
    }, 30000)
  }

  private _stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  private _scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnects) return
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000)
    this.reconnectAttempts++
    this.reconnectTimeout = setTimeout(() => this.connect(), delay)
  }
}

// Factory helpers
export const createMatchWS = (matchId: number) =>
  new SportWebSocket(`/ws/matches/${matchId}/`)

export const createTickerWS = () =>
  new SportWebSocket('/ws/ticker/')
