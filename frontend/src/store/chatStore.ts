import { create } from 'zustand';
import type { SSEEvent } from '../api/sse';

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  agentName?: string;
  content: string;
  timestamp: number;
}

export interface Project {
  id: string;
  name: string;
  mode: string;
  created_at: string;
  updated_at: string;
}

export interface RaceResult {
  lane_idx: number;
  model: string;
  project_id: string;
  summary: string;
}

interface ChatState {
  messages: ChatMessage[];
  projects: Project[];
  currentProjectId: string | null;
  mode: 'engineer' | 'team' | 'race';
  isRunning: boolean;
  activeAgent: string | null;
  agentThoughts: string;
  viewerRefreshKey: number;
  raceResults: RaceResult[] | null;
  raceSelected: boolean;

  addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (id: string | null) => void;
  setMode: (mode: 'engineer' | 'team' | 'race') => void;
  setRunning: (running: boolean) => void;
  setActiveAgent: (agent: string | null) => void;
  appendThought: (thought: string) => void;
  clearThoughts: () => void;
  triggerViewerRefresh: () => void;
  setRaceResults: (results: RaceResult[] | null) => void;
  setRaceSelected: (selected: boolean) => void;
  reset: () => void;
}

let msgCounter = 0;

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  projects: [],
  currentProjectId: null,
  mode: 'engineer',
  isRunning: false,
  activeAgent: null,
  agentThoughts: '',
  viewerRefreshKey: 0,
  raceResults: null,
  raceSelected: false,

  addMessage: (msg) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { ...msg, id: `msg_${++msgCounter}`, timestamp: Date.now() },
      ],
    })),

  setProjects: (projects) => set({ projects }),
  setCurrentProject: (id) => set({ currentProjectId: id }),
  setMode: (mode) => set({ mode }),
  setRunning: (running) => set({ isRunning: running }),
  setActiveAgent: (agent) => set({ activeAgent: agent }),
  appendThought: (thought) =>
    set((state) => ({ agentThoughts: state.agentThoughts + thought })),
  clearThoughts: () => set({ agentThoughts: '' }),
  triggerViewerRefresh: () =>
    set((state) => ({ viewerRefreshKey: state.viewerRefreshKey + 1 })),
  setRaceResults: (results) => set({ raceResults: results }),
  setRaceSelected: (selected) => set({ raceSelected: selected }),
  reset: () =>
    set({
      isRunning: false,
      activeAgent: null,
      agentThoughts: '',
      raceResults: null,
      raceSelected: false,
    }),
}));