import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Bloomberg-style Window Manager
 * Features:
 * - Free-form positioning (drag anywhere)
 * - Resizable windows
 * - Overlapping widgets with z-index management
 * - Snap-to-grid and snap-to-edge
 * - Multiple layout presets
 * - Layout persistence
 */

export interface WindowPosition {
    x: number;
    y: number;
}

export interface WindowSize {
    width: number;
    height: number;
}

export interface WindowState {
    id: string;
    toolId: string;
    title: string;
    position: WindowPosition;
    size: WindowSize;
    isMinimized: boolean;
    isMaximized: boolean;
    zIndex: number;
    // Pre-maximize state for restore
    preMaximizeState?: {
        position: WindowPosition;
        size: WindowSize;
    };
}

export interface LayoutPreset {
    id: string;
    name: string;
    windows: Omit<WindowState, 'id' | 'zIndex'>[];
}

export interface WindowStore {
    windows: WindowState[];
    activeWindowId: string | null;
    nextZIndex: number;

    // Default sizes for new windows
    defaultWindowSize: WindowSize;

    // Grid settings for snapping
    gridSize: number;
    snapToGrid: boolean;
    snapToEdge: boolean;

    // Layout presets
    layoutPresets: LayoutPreset[];

    // Actions
    openWindow: (toolId: string, title: string, options?: Partial<WindowState>) => string;
    closeWindow: (id: string) => void;
    closeAllWindows: () => void;
    focusWindow: (id: string) => void;
    minimizeWindow: (id: string) => void;
    maximizeWindow: (id: string) => void;
    restoreWindow: (id: string) => void;

    // Position & Size
    moveWindow: (id: string, position: WindowPosition) => void;
    resizeWindow: (id: string, size: WindowSize) => void;

    // Snapping
    setSnapToGrid: (enabled: boolean) => void;
    setSnapToEdge: (enabled: boolean) => void;
    setGridSize: (size: number) => void;

    // Layout presets
    saveLayoutPreset: (name: string) => void;
    loadLayoutPreset: (id: string) => void;
    deleteLayoutPreset: (id: string) => void;

    // Tiling helpers
    tileWindows: (mode: 'horizontal' | 'vertical' | 'grid' | 'cascade') => void;
}

const DEFAULT_WINDOW_SIZE = { width: 600, height: 400 };
const DEFAULT_GRID_SIZE = 20;

let windowIdCounter = 0;

// Helper to snap position to grid
function snapToGridValue(value: number, gridSize: number): number {
    return Math.round(value / gridSize) * gridSize;
}

export const useWindowStore = create<WindowStore>()(
    persist(
        (set, get) => ({
            windows: [],
            activeWindowId: null,
            nextZIndex: 1,
            defaultWindowSize: DEFAULT_WINDOW_SIZE,
            gridSize: DEFAULT_GRID_SIZE,
            snapToGrid: false,
            snapToEdge: true,
            layoutPresets: [],

            openWindow: (toolId: string, title: string, options?: Partial<WindowState>) => {
                const id = `window-${++windowIdCounter}`;
                const state = get();

                // Calculate position for new window (cascade from last window)
                const lastWindow = state.windows[state.windows.length - 1];
                const baseOffset = state.windows.length * 30;

                const position = options?.position || {
                    x: lastWindow ? lastWindow.position.x + 30 : 50 + baseOffset,
                    y: lastWindow ? lastWindow.position.y + 30 : 50 + baseOffset,
                };

                const newWindow: WindowState = {
                    id,
                    toolId,
                    title,
                    position,
                    size: options?.size || { ...state.defaultWindowSize },
                    isMinimized: false,
                    isMaximized: false,
                    zIndex: state.nextZIndex,
                };

                set({
                    windows: [...state.windows, newWindow],
                    activeWindowId: id,
                    nextZIndex: state.nextZIndex + 1,
                });

                return id;
            },

            closeWindow: (id: string) => {
                set(state => ({
                    windows: state.windows.filter(w => w.id !== id),
                    activeWindowId: state.activeWindowId === id ? null : state.activeWindowId,
                }));
            },

            closeAllWindows: () => {
                set({ windows: [], activeWindowId: null });
            },

            focusWindow: (id: string) => {
                set(state => ({
                    windows: state.windows.map(w =>
                        w.id === id ? { ...w, zIndex: state.nextZIndex, isMinimized: false } : w
                    ),
                    activeWindowId: id,
                    nextZIndex: state.nextZIndex + 1,
                }));
            },

            minimizeWindow: (id: string) => {
                set(state => ({
                    windows: state.windows.map(w =>
                        w.id === id ? { ...w, isMinimized: true } : w
                    ),
                    activeWindowId: state.activeWindowId === id ? null : state.activeWindowId,
                }));
            },

            maximizeWindow: (id: string) => {
                set(state => ({
                    windows: state.windows.map(w => {
                        if (w.id !== id) return w;
                        return {
                            ...w,
                            isMaximized: true,
                            isMinimized: false,
                            preMaximizeState: {
                                position: w.position,
                                size: w.size,
                            },
                            zIndex: state.nextZIndex,
                        };
                    }),
                    activeWindowId: id,
                    nextZIndex: state.nextZIndex + 1,
                }));
            },

            restoreWindow: (id: string) => {
                set(state => ({
                    windows: state.windows.map(w => {
                        if (w.id !== id) return w;
                        return {
                            ...w,
                            isMaximized: false,
                            isMinimized: false,
                            position: w.preMaximizeState?.position || w.position,
                            size: w.preMaximizeState?.size || w.size,
                            preMaximizeState: undefined,
                        };
                    }),
                }));
            },

            moveWindow: (id: string, position: WindowPosition) => {
                const state = get();
                let finalPosition = position;

                // Apply grid snapping
                if (state.snapToGrid) {
                    finalPosition = {
                        x: snapToGridValue(position.x, state.gridSize),
                        y: snapToGridValue(position.y, state.gridSize),
                    };
                }

                // Apply edge snapping (to viewport edges)
                if (state.snapToEdge) {
                    const threshold = 20;
                    const viewportWidth = window.innerWidth;
                    const viewportHeight = window.innerHeight;
                    const win = state.windows.find(w => w.id === id);

                    if (win) {
                        // Snap to left edge
                        if (finalPosition.x < threshold) finalPosition.x = 0;
                        // Snap to right edge
                        if (finalPosition.x + win.size.width > viewportWidth - threshold) {
                            finalPosition.x = viewportWidth - win.size.width;
                        }
                        // Snap to top edge (accounting for header)
                        if (finalPosition.y < 60 + threshold) finalPosition.y = 60;
                        // Snap to bottom edge
                        if (finalPosition.y + win.size.height > viewportHeight - threshold) {
                            finalPosition.y = viewportHeight - win.size.height;
                        }
                    }
                }

                set(state => ({
                    windows: state.windows.map(w =>
                        w.id === id ? { ...w, position: finalPosition, isMaximized: false } : w
                    ),
                }));
            },

            resizeWindow: (id: string, size: WindowSize) => {
                // Enforce minimum size
                const minSize = { width: 300, height: 200 };
                const finalSize = {
                    width: Math.max(size.width, minSize.width),
                    height: Math.max(size.height, minSize.height),
                };

                set(state => ({
                    windows: state.windows.map(w =>
                        w.id === id ? { ...w, size: finalSize, isMaximized: false } : w
                    ),
                }));
            },

            setSnapToGrid: (enabled: boolean) => set({ snapToGrid: enabled }),
            setSnapToEdge: (enabled: boolean) => set({ snapToEdge: enabled }),
            setGridSize: (size: number) => set({ gridSize: size }),

            saveLayoutPreset: (name: string) => {
                const state = get();
                const preset: LayoutPreset = {
                    id: `preset-${Date.now()}`,
                    name,
                    windows: state.windows.map(w => ({
                        toolId: w.toolId,
                        title: w.title,
                        position: w.position,
                        size: w.size,
                        isMinimized: w.isMinimized,
                        isMaximized: w.isMaximized,
                    })),
                };
                set({ layoutPresets: [...state.layoutPresets, preset] });
            },

            loadLayoutPreset: (id: string) => {
                const state = get();
                const preset = state.layoutPresets.find(p => p.id === id);
                if (!preset) return;

                // Close all windows and recreate from preset
                const newWindows: WindowState[] = preset.windows.map((w, i) => ({
                    ...w,
                    id: `window-${++windowIdCounter}`,
                    zIndex: i + 1,
                }));

                set({
                    windows: newWindows,
                    nextZIndex: newWindows.length + 1,
                    activeWindowId: newWindows[0]?.id || null,
                });
            },

            deleteLayoutPreset: (id: string) => {
                set(state => ({
                    layoutPresets: state.layoutPresets.filter(p => p.id !== id),
                }));
            },

            tileWindows: (mode: 'horizontal' | 'vertical' | 'grid' | 'cascade') => {
                const state = get();
                const visibleWindows = state.windows.filter(w => !w.isMinimized);
                if (visibleWindows.length === 0) return;

                const viewportWidth = window.innerWidth;
                const viewportHeight = window.innerHeight - 60; // Account for header
                const headerOffset = 60;

                let updatedWindows = [...state.windows];

                if (mode === 'horizontal') {
                    const windowWidth = viewportWidth / visibleWindows.length;
                    visibleWindows.forEach((w, i) => {
                        const idx = updatedWindows.findIndex(uw => uw.id === w.id);
                        updatedWindows[idx] = {
                            ...w,
                            position: { x: i * windowWidth, y: headerOffset },
                            size: { width: windowWidth, height: viewportHeight },
                            isMaximized: false,
                        };
                    });
                } else if (mode === 'vertical') {
                    const windowHeight = viewportHeight / visibleWindows.length;
                    visibleWindows.forEach((w, i) => {
                        const idx = updatedWindows.findIndex(uw => uw.id === w.id);
                        updatedWindows[idx] = {
                            ...w,
                            position: { x: 0, y: headerOffset + i * windowHeight },
                            size: { width: viewportWidth, height: windowHeight },
                            isMaximized: false,
                        };
                    });
                } else if (mode === 'grid') {
                    const cols = Math.ceil(Math.sqrt(visibleWindows.length));
                    const rows = Math.ceil(visibleWindows.length / cols);
                    const windowWidth = viewportWidth / cols;
                    const windowHeight = viewportHeight / rows;

                    visibleWindows.forEach((w, i) => {
                        const col = i % cols;
                        const row = Math.floor(i / cols);
                        const idx = updatedWindows.findIndex(uw => uw.id === w.id);
                        updatedWindows[idx] = {
                            ...w,
                            position: { x: col * windowWidth, y: headerOffset + row * windowHeight },
                            size: { width: windowWidth, height: windowHeight },
                            isMaximized: false,
                        };
                    });
                } else if (mode === 'cascade') {
                    const cascadeOffset = 30;
                    visibleWindows.forEach((w, i) => {
                        const idx = updatedWindows.findIndex(uw => uw.id === w.id);
                        updatedWindows[idx] = {
                            ...w,
                            position: { x: 50 + i * cascadeOffset, y: headerOffset + i * cascadeOffset },
                            size: { width: 600, height: 400 },
                            isMaximized: false,
                            zIndex: i + 1,
                        };
                    });
                }

                set({ windows: updatedWindows });
            },
        }),
        {
            name: 'terminal-layout',
            partialize: (state) => ({
                layoutPresets: state.layoutPresets,
                snapToGrid: state.snapToGrid,
                snapToEdge: state.snapToEdge,
                gridSize: state.gridSize,
            }),
        }
    )
);
