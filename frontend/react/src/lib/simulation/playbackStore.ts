import { create } from 'zustand'
import type { ScenarioSimulation, SimulationPackage } from './types'

interface PlaybackState {
  simulation: SimulationPackage | null
  scenarioIndex: number
  frameIndex: number
  isPlaying: boolean
  isVisible: boolean
  speed: number
  setSimulation: (simulation: SimulationPackage) => void
  setScenarioIndex: (index: number) => void
  setFrameIndex: (index: number) => void
  setPlaying: (playing: boolean) => void
  setVisible: (visible: boolean) => void
  setSpeed: (speed: number) => void
  nextFrame: () => void
}

export const usePlaybackStore = create<PlaybackState>((set, get) => ({
  simulation: null,
  scenarioIndex: 0,
  frameIndex: 0,
  isPlaying: true,
  isVisible: true,
  speed: 1,
  setSimulation: (simulation) => set({ simulation, scenarioIndex: 0, frameIndex: 0 }),
  setScenarioIndex: (scenarioIndex) => set({ scenarioIndex, frameIndex: 0 }),
  setFrameIndex: (frameIndex) => set({ frameIndex }),
  setPlaying: (isPlaying) => set({ isPlaying }),
  setVisible: (isVisible) => set({ isVisible }),
  setSpeed: (speed) => set({ speed }),
  nextFrame: () => {
    const { simulation, scenarioIndex, frameIndex } = get()
    if (!simulation?.playlist.length) return

    const scenario = simulation.playlist[scenarioIndex]
    const hasNextFrame = frameIndex + 1 < scenario.frames.length

    if (hasNextFrame) {
      set({ frameIndex: frameIndex + 1 })
      return
    }

    set({
      scenarioIndex: (scenarioIndex + 1) % simulation.playlist.length,
      frameIndex: 0,
    })
  },
}))

export function selectCurrentScenario(simulation: SimulationPackage | null, scenarioIndex: number): ScenarioSimulation | null {
  return simulation?.playlist[scenarioIndex] || null
}