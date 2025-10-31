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
        set((state) => {
            const newMainSidebarState = !state.isSidebarOpen;
            return {
                isSidebarOpen: newMainSidebarState,
                isChunkSidebarOpen: newMainSidebarState ? false : state.isChunkSidebarOpen,
            };
        }),
    setSidebarOpen: (open) =>
        set((state) => ({
            isSidebarOpen: open,
            isChunkSidebarOpen: open ? false : state.isChunkSidebarOpen,
        })),
    setChunkSidebarOpen: (open) =>
        set((state) => ({
            isChunkSidebarOpen: open,
            isSidebarOpen: open ? false : state.isSidebarOpen,
        })),
}));

