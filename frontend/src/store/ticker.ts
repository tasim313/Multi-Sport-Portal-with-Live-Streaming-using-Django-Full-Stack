import { create } from 'zustand'
import type { TickerMatch } from '@/types'

interface TickerState {
  matches: TickerMatch[]
  setMatches: (matches: TickerMatch[]) => void
  updateMatch: (match: TickerMatch) => void
}

export const useTickerStore = create<TickerState>((set) => ({
  matches: [],
  setMatches: (matches) => set({ matches }),
  updateMatch: (updated) =>
    set((state) => ({
      matches: state.matches.map((m) => (m.id === updated.id ? updated : m)),
    })),
}))
