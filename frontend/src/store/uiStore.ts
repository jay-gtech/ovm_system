import { create } from 'zustand'

interface UIState {
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
  toggleSidebar: () => void
  setSidebar: (collapsed: boolean) => void
  toggleTheme: () => void
  setTheme: (theme: 'light' | 'dark') => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  theme: 'light',
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebar: (collapsed) => set({ sidebarCollapsed: collapsed }),
  toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
  setTheme: (theme) => set({ theme }),
}))
