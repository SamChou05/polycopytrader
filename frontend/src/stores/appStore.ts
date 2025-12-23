import { create } from 'zustand';

/**
 * Application-wide store for connection status, settings, and shared state.
 */

export interface Trade {
    id?: string;
    wallet_address: string;
    asset: string;
    side: 'BUY' | 'SELL';
    size: number;
    price: number;
    copied: boolean;
    latency_ms: number | null;
    title: string;
    outcome: string;
    timestamp: string;
}

export interface Wallet {
    id: number;
    address: string;
    name: string;
    enabled: boolean;
}

export interface Stats {
    trades_detected: number;
    trades_copied: number;
    trades_skipped: number;
    avg_latency: number;
}

export interface AppStore {
    // Connection
    isConnected: boolean;
    setConnected: (connected: boolean) => void;

    // Mode
    mode: 'DRY_RUN' | 'LIVE';
    setMode: (mode: 'DRY_RUN' | 'LIVE') => void;

    // Wallets
    wallets: Wallet[];
    setWallets: (wallets: Wallet[]) => void;
    addWallet: (wallet: Wallet) => void;
    toggleWallet: (id: number) => void;
    removeWallet: (id: number) => void;

    // Trades
    trades: Trade[];
    addTrade: (trade: Trade) => void;
    clearTrades: () => void;

    // Stats
    stats: Stats;
    updateStats: (stats: Partial<Stats>) => void;
}

export const useAppStore = create<AppStore>((set) => ({
    // Connection
    isConnected: false,
    setConnected: (connected) => set({ isConnected: connected }),

    // Mode
    mode: 'DRY_RUN',
    setMode: (mode) => set({ mode }),

    // Wallets
    wallets: [],
    setWallets: (wallets) => set({ wallets }),
    addWallet: (wallet) => set((state) => ({
        wallets: [...state.wallets, wallet]
    })),
    toggleWallet: (id) => set((state) => ({
        wallets: state.wallets.map(w =>
            w.id === id ? { ...w, enabled: !w.enabled } : w
        ),
    })),
    removeWallet: (id) => set((state) => ({
        wallets: state.wallets.filter(w => w.id !== id),
    })),

    // Trades
    trades: [],
    addTrade: (trade) => set((state) => ({
        trades: [trade, ...state.trades].slice(0, 50), // Keep last 50
    })),
    clearTrades: () => set({ trades: [] }),

    // Stats
    stats: {
        trades_detected: 0,
        trades_copied: 0,
        trades_skipped: 0,
        avg_latency: 0,
    },
    updateStats: (stats) => set((state) => ({
        stats: { ...state.stats, ...stats },
    })),
}));
