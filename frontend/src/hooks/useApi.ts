/**
 * API Hook - Centralized API calls to Flask backend.
 * Provides typed methods for all backend operations.
 */

import { useCallback, useState } from 'react';
import type { Wallet, Trade, Stats } from '../stores/appStore';

const API_BASE = '/api';

interface ApiState {
    loading: boolean;
    error: string | null;
}

interface ApiResponse<T> {
    data: T | null;
    error: string | null;
}

// ============================================
// Wallet API
// ============================================

export function useWalletApi() {
    const [state, setState] = useState<ApiState>({ loading: false, error: null });

    const getWallets = useCallback(async (): Promise<ApiResponse<Wallet[]>> => {
        setState({ loading: true, error: null });
        try {
            const res = await fetch(`${API_BASE}/wallets`);
            const data = await res.json();
            setState({ loading: false, error: null });
            return { data, error: null };
        } catch (e) {
            const error = (e as Error).message;
            setState({ loading: false, error });
            return { data: null, error };
        }
    }, []);

    const addWallet = useCallback(async (address: string, name: string): Promise<ApiResponse<Wallet>> => {
        setState({ loading: true, error: null });
        try {
            const res = await fetch(`${API_BASE}/wallets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address, name }),
            });
            const data = await res.json();
            setState({ loading: false, error: null });
            return { data, error: null };
        } catch (e) {
            const error = (e as Error).message;
            setState({ loading: false, error });
            return { data: null, error };
        }
    }, []);

    const updateWallet = useCallback(async (address: string, updates: Partial<Wallet>): Promise<ApiResponse<boolean>> => {
        setState({ loading: true, error: null });
        try {
            const res = await fetch(`${API_BASE}/wallets/${address}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates),
            });
            const data = await res.json();
            setState({ loading: false, error: null });
            return { data: data.success, error: null };
        } catch (e) {
            const error = (e as Error).message;
            setState({ loading: false, error });
            return { data: null, error };
        }
    }, []);

    const deleteWallet = useCallback(async (address: string): Promise<ApiResponse<boolean>> => {
        setState({ loading: true, error: null });
        try {
            const res = await fetch(`${API_BASE}/wallets/${address}`, {
                method: 'DELETE',
            });
            const data = await res.json();
            setState({ loading: false, error: null });
            return { data: data.success, error: null };
        } catch (e) {
            const error = (e as Error).message;
            setState({ loading: false, error });
            return { data: null, error };
        }
    }, []);

    return { ...state, getWallets, addWallet, updateWallet, deleteWallet };
}

// ============================================
// Settings API
// ============================================

export function useSettingsApi() {
    const [state, setState] = useState<ApiState>({ loading: false, error: null });

    const getSetting = useCallback(async (key: string): Promise<ApiResponse<unknown>> => {
        setState({ loading: true, error: null });
        try {
            const res = await fetch(`${API_BASE}/settings/${key}`);
            const data = await res.json();
            setState({ loading: false, error: null });
            return { data: data.value, error: null };
        } catch (e) {
            const error = (e as Error).message;
            setState({ loading: false, error });
            return { data: null, error };
        }
    }, []);

    const setSetting = useCallback(async (key: string, value: unknown, category?: string): Promise<ApiResponse<boolean>> => {
        setState({ loading: true, error: null });
        try {
            const res = await fetch(`${API_BASE}/settings/${key}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ value, category }),
            });
            const data = await res.json();
            setState({ loading: false, error: null });
            return { data: data.success, error: null };
        } catch (e) {
            const error = (e as Error).message;
            setState({ loading: false, error });
            return { data: null, error };
        }
    }, []);

    const getSettingsByCategory = useCallback(async (category: string): Promise<ApiResponse<Record<string, unknown>>> => {
        setState({ loading: true, error: null });
        try {
            const res = await fetch(`${API_BASE}/settings?category=${category}`);
            const data = await res.json();
            setState({ loading: false, error: null });
            return { data, error: null };
        } catch (e) {
            const error = (e as Error).message;
            setState({ loading: false, error });
            return { data: null, error };
        }
    }, []);

    return { ...state, getSetting, setSetting, getSettingsByCategory };
}

// ============================================
// Trades API
// ============================================

export function useTradesApi() {
    const [state, setState] = useState<ApiState>({ loading: false, error: null });

    const getTrades = useCallback(async (limit = 50): Promise<ApiResponse<Trade[]>> => {
        setState({ loading: true, error: null });
        try {
            const res = await fetch(`${API_BASE}/trades?limit=${limit}`);
            const data = await res.json();
            setState({ loading: false, error: null });
            return { data, error: null };
        } catch (e) {
            const error = (e as Error).message;
            setState({ loading: false, error });
            return { data: null, error };
        }
    }, []);

    const getStats = useCallback(async (): Promise<ApiResponse<Stats>> => {
        setState({ loading: true, error: null });
        try {
            const res = await fetch(`${API_BASE}/stats`);
            const data = await res.json();
            setState({ loading: false, error: null });
            return { data, error: null };
        } catch (e) {
            const error = (e as Error).message;
            setState({ loading: false, error });
            return { data: null, error };
        }
    }, []);

    return { ...state, getTrades, getStats };
}
