import { create } from "zustand";

type StreamHealth = "ready" | "connecting" | "streaming" | "degraded";

type EnterpriseState = {
  activeWorkspace: string;
  streamHealth: StreamHealth;
  setActiveWorkspace: (workspace: string) => void;
  setStreamHealth: (health: StreamHealth) => void;
};

export const useEnterpriseStore = create<EnterpriseState>((set) => ({
  activeWorkspace: "Command",
  streamHealth: "ready",
  setActiveWorkspace: (workspace) => set({ activeWorkspace: workspace }),
  setStreamHealth: (health) => set({ streamHealth: health }),
}));
