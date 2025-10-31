import { create } from 'zustand';

interface UIState {
    isSidebarOpen: boolean;
    isChunkSidebarOpen: boolean;
    toggleSidebar: () => void;
    setSidebarOpen: (open: boolean) => void;
    setChunkSidebarOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
    isSidebarOpen: true,
    isChunkSidebarOpen: false,
    toggleSidebar: () =>
        set((state) => ({
            isSidebarOpen: !state.isSidebarOpen,
        })),
    setSidebarOpen: (open) =>
        set({
            isSidebarOpen: open,
        }),
    setChunkSidebarOpen: (open) =>
        set({
            isChunkSidebarOpen: open,
        }),
}));

