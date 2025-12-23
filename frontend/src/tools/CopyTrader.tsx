import React, { useState, useEffect } from 'react';
import { WalletManager } from '../components/WalletManager';
import './CopyTrader.css';

interface Trade {
    id: number;
    wallet_address: string;
    asset: string;
    side: string;
    size: number;
    price: number;
    copied: boolean;
    latency_ms: number;
    title: string;
    outcome: string;
    timestamp: string;
}

interface Stats {
    trades_detected: number;
    trades_copied: number;
    trades_skipped: number;
    avg_latency: number;
}

/**
 * Copy Trader tool - monitors wallets and displays trade activity.
 */
interface Wallet {
    id: number;
    address: string;
    name: string;
    enabled: boolean;
}

export const CopyTrader: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'activity' | 'wallets'>('activity');
    const [trades, setTrades] = useState<Trade[]>([]);
    const [wallets, setWallets] = useState<Wallet[]>([]);
    const [stats, setStats] = useState<Stats>({
        trades_detected: 0,
        trades_copied: 0,
        trades_skipped: 0,
        avg_latency: 0,
    });

    // Fetch trades and stats
    const fetchData = async () => {
        try {
            const [tradesRes, statsRes, walletsRes] = await Promise.all([
                fetch('/api/trades?limit=50'),
                fetch('/api/stats'),
                fetch('/api/wallets'),
            ]);

            if (tradesRes.ok) {
                const tradesData = await tradesRes.json();
                setTrades(tradesData);
            }

            if (statsRes.ok) {
                const statsData = await statsRes.json();
                setStats(statsData);
            }

            if (walletsRes.ok) {
                const walletsData = await walletsRes.json();
                setWallets(walletsData);
            }
        } catch (err) {
            console.error('Failed to fetch data:', err);
        }
    };

    useEffect(() => {
        fetchData();
        // Poll for updates every 5 seconds
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    // Format timestamp for display
    const formatTime = (timestamp: string) => {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch {
            return timestamp;
        }
    };

    // Get wallet name for an address
    const getWalletName = (address: string) => {
        const wallet = wallets.find(w => w.address.toLowerCase() === address.toLowerCase());
        if (wallet) {
            return wallet.name;
        }
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

    return (
        <div className="copy-trader">
            {/* Stats Bar */}
            <div className="stats-bar">
                <div className="stat">
                    <span className="stat-label">Detected</span>
                    <span className="stat-value highlight">{stats.trades_detected}</span>
                </div>
                <div className="stat">
                    <span className="stat-label">Copied</span>
                    <span className="stat-value positive">{stats.trades_copied}</span>
                </div>
                <div className="stat">
                    <span className="stat-label">Skipped</span>
                    <span className="stat-value neutral">{stats.trades_skipped}</span>
                </div>
                <div className="stat">
                    <span className="stat-label">Avg Latency</span>
                    <span className="stat-value highlight">{stats.avg_latency}ms</span>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="tab-nav">
                <button
                    className={`tab-btn ${activeTab === 'activity' ? 'active' : ''}`}
                    onClick={() => setActiveTab('activity')}
                >
                    Activity
                </button>
                <button
                    className={`tab-btn ${activeTab === 'wallets' ? 'active' : ''}`}
                    onClick={() => setActiveTab('wallets')}
                >
                    Wallets
                </button>
            </div>

            {/* Tab Content */}
            <div className="tab-content">
                {activeTab === 'activity' ? (
                    <div className="activity-view">
                        <div className="trades-container">
                            <table className="trades-table">
                                <thead>
                                    <tr>
                                        <th>TIME</th>
                                        <th>WALLET</th>
                                        <th>MARKET</th>
                                        <th>SIDE</th>
                                        <th>SIZE</th>
                                        <th>PRICE</th>
                                        <th>LATENCY</th>
                                        <th>STATUS</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {trades.length === 0 ? (
                                        <tr className="empty-row">
                                            <td colSpan={8}>Waiting for trades...</td>
                                        </tr>
                                    ) : (
                                        trades.map((trade, i) => (
                                            <tr key={trade.id || i} className={i === 0 ? 'new-trade' : ''}>
                                                <td>{formatTime(trade.timestamp)}</td>
                                                <td className="wallet-cell">{getWalletName(trade.wallet_address)}</td>
                                                <td className="market-cell">
                                                    <span className="market-title">{trade.title || trade.asset}</span>
                                                    {trade.outcome && (
                                                        <span className="market-outcome">{trade.outcome}</span>
                                                    )}
                                                </td>
                                                <td className={trade.side === 'BUY' ? 'buy' : 'sell'}>{trade.side}</td>
                                                <td>{trade.size?.toFixed(2)}</td>
                                                <td>${trade.price?.toFixed(2)}</td>
                                                <td>{trade.latency_ms}ms</td>
                                                <td className={trade.copied ? 'copied' : 'skipped'}>
                                                    {trade.copied ? 'COPIED' : 'SKIP'}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ) : (
                    <WalletManager onWalletChange={fetchData} />
                )}
            </div>
        </div>
    );
};
