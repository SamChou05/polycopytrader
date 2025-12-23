/**
 * WebSocket Hook - Centralized socket connection for all tools.
 * Provides real-time data from the Flask backend.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAppStore } from '../stores/appStore';

interface UseSocketOptions {
    autoConnect?: boolean;
    reconnectionAttempts?: number;
}

interface SocketState {
    isConnected: boolean;
    error: string | null;
}

export function useSocket(options: UseSocketOptions = {}) {
    const { autoConnect = true, reconnectionAttempts = 5 } = options;
    const socketRef = useRef<Socket | null>(null);
    const [state, setState] = useState<SocketState>({
        isConnected: false,
        error: null,
    });

    const { setConnected, addTrade, updateStats, setWallets } = useAppStore();

    // Initialize socket connection
    useEffect(() => {
        if (!autoConnect) return;

        const socket = io('/', {
            path: '/socket.io',
            reconnectionAttempts,
            transports: ['websocket', 'polling'],
        });

        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('Socket connected');
            setState({ isConnected: true, error: null });
            setConnected(true);
        });

        socket.on('disconnect', (reason) => {
            console.log('Socket disconnected:', reason);
            setState({ isConnected: false, error: null });
            setConnected(false);
        });

        socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            setState({ isConnected: false, error: error.message });
        });

        // Handle initial state from server
        socket.on('initial_state', (data) => {
            console.log('Received initial state:', data);
            if (data.stats) updateStats(data.stats);
            if (data.wallets) setWallets(data.wallets);
            if (data.trades) {
                data.trades.forEach((trade: any) => addTrade(trade));
            }
        });

        // Handle trade updates
        socket.on('trade_update', (data) => {
            console.log('Trade update:', data);
            if (data.trade) addTrade(data.trade);
            if (data.stats) updateStats(data.stats);
        });

        // Handle connection status updates
        socket.on('connection_status', (data) => {
            setConnected(data.connected);
        });

        // Cleanup on unmount
        return () => {
            socket.disconnect();
            socketRef.current = null;
        };
    }, [autoConnect, reconnectionAttempts]);

    // Emit event to server
    const emit = useCallback((event: string, data?: any) => {
        if (socketRef.current?.connected) {
            socketRef.current.emit(event, data);
        } else {
            console.warn('Socket not connected, cannot emit:', event);
        }
    }, []);

    // Subscribe to a specific event
    const on = useCallback((event: string, callback: (data: any) => void) => {
        socketRef.current?.on(event, callback);
        return () => {
            socketRef.current?.off(event, callback);
        };
    }, []);

    return {
        ...state,
        socket: socketRef.current,
        emit,
        on,
    };
}
