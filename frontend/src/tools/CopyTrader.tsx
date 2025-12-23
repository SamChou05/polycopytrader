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

interface CopySettings {
    liveTrading: boolean;
    sizingMode: 'percentage' | 'fixed';
    copyPercentage: number;
    fixedAmount: number;
}

export const CopyTrader: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'activity' | 'wallets' | 'settings'>('activity');
    const [trades, setTrades] = useState<Trade[]>([]);
    const [wallets, setWallets] = useState<Wallet[]>([]);
    const [selectedWallet, setSelectedWallet] = useState<string>('all');
    const [stats, setStats] = useState<Stats>({
        trades_detected: 0,
        trades_copied: 0,
        trades_skipped: 0,
        avg_latency: 0,
    });
    const [settings, setSettings] = useState<CopySettings>({
        liveTrading: false,
        sizingMode: 'percentage',
        copyPercentage: 10,
        fixedAmount: 10,
    });
    const [settingsSaving, setSettingsSaving] = useState(false);

    // Fetch trades and stats
    const fetchData = async () => {
        try {
            const [tradesRes, statsRes, walletsRes, settingsRes] = await Promise.all([
                fetch('/api/trades?limit=50'),
                fetch('/api/stats'),
                fetch('/api/wallets'),
                fetch('/api/settings/copytrader_settings'),
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

            if (settingsRes.ok) {
                const settingsData = await settingsRes.json();
                // The API returns {key, value} - parse the value
                if (settingsData.value) {
                    try {
                        const parsed = typeof settingsData.value === 'string'
                            ? JSON.parse(settingsData.value)
                            : settingsData.value;
                        setSettings(parsed);
                    } catch (e) {
                        console.error('Failed to parse settings:', e);
                    }
                }
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

    // Filter trades by selected wallet
    const filteredTrades = selectedWallet === 'all'
        ? trades
        : trades.filter(t => t.wallet_address.toLowerCase() === selectedWallet.toLowerCase());

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
                <button
                    className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
                    onClick={() => setActiveTab('settings')}
                >
                    Settings
                </button>
            </div>

            {/* Tab Content */}
            <div className="tab-content">
                {activeTab === 'activity' ? (
                    <div className="activity-view">
                        <div className="activity-header">
                            <select
                                className="wallet-filter"
                                value={selectedWallet}
                                onChange={(e) => setSelectedWallet(e.target.value)}
                            >
                                <option value="all">All Wallets</option>
                                {wallets.map(w => (
                                    <option key={w.id} value={w.address}>
                                        {w.name}
                                    </option>
                                ))}
                            </select>
                            <span className="trade-count">
                                {filteredTrades.length} trade{filteredTrades.length !== 1 ? 's' : ''}
                            </span>
                        </div>
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
                                    {filteredTrades.length === 0 ? (
                                        <tr className="empty-row">
                                            <td colSpan={8}>{trades.length === 0 ? 'Waiting for trades...' : 'No trades for selected wallet'}</td>
                                        </tr>
                                    ) : (
                                        filteredTrades.map((trade, i) => (
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
                ) : activeTab === 'wallets' ? (
                    <WalletManager onWalletChange={fetchData} />
                ) : (
                    <div className="settings-view">
                        <div className="settings-header">
                            <h3>Copy Trading Settings</h3>
                        </div>
                        <div className="settings-list">

                            {/* Live Trading Toggle */}
                            <div className="setting-row">
                                <div className="setting-info">
                                    <label>Live Trading</label>
                                    <span className="setting-desc">
                                        {settings.liveTrading
                                            ? '⚠️ Orders will be placed on Polymarket'
                                            : 'Dry run mode - no orders placed'}
                                    </span>
                                </div>
                                <button
                                    className={`toggle-switch ${settings.liveTrading ? 'on' : 'off'}`}
                                    onClick={() => setSettings({ ...settings, liveTrading: !settings.liveTrading })}
                                >
                                    {settings.liveTrading ? 'ON' : 'OFF'}
                                </button>
                            </div>

                            {/* Sizing Mode */}
                            <div className="setting-row">
                                <div className="setting-info">
                                    <label>Sizing Mode</label>
                                    <span className="setting-desc">How to calculate your trade size</span>
                                </div>
                                <select
                                    className="setting-select"
                                    value={settings.sizingMode}
                                    onChange={(e) => setSettings({ ...settings, sizingMode: e.target.value as 'percentage' | 'fixed' })}
                                >
                                    <option value="percentage">Percentage of Target</option>
                                    <option value="fixed">Fixed Amount (USDC)</option>
                                </select>
                            </div>

                            {/* Copy Percentage (shown when percentage mode) */}
                            {settings.sizingMode === 'percentage' && (
                                <div className="setting-row">
                                    <div className="setting-info">
                                        <label>Copy Percentage</label>
                                        <span className="setting-desc">Copy {settings.copyPercentage}% of target's trade size</span>
                                    </div>
                                    <div className="setting-input-group">
                                        <input
                                            type="range"
                                            min="1"
                                            max="100"
                                            value={settings.copyPercentage}
                                            onChange={(e) => setSettings({ ...settings, copyPercentage: parseInt(e.target.value) })}
                                        />
                                        <span className="setting-value">{settings.copyPercentage}%</span>
                                    </div>
                                </div>
                            )}

                            {/* Fixed Amount (shown when fixed mode) */}
                            {settings.sizingMode === 'fixed' && (
                                <div className="setting-row">
                                    <div className="setting-info">
                                        <label>Fixed Amount</label>
                                        <span className="setting-desc">Trade this amount for every detected trade</span>
                                    </div>
                                    <div className="setting-input-group">
                                        <span className="currency">$</span>
                                        <input
                                            type="number"
                                            min="1"
                                            value={settings.fixedAmount}
                                            onChange={(e) => setSettings({ ...settings, fixedAmount: parseFloat(e.target.value) || 0 })}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* Save Button */}
                            <div className="settings-actions">
                                <button
                                    className="save-btn"
                                    disabled={settingsSaving}
                                    onClick={async () => {
                                        setSettingsSaving(true);
                                        try {
                                            await fetch('/api/settings/tool/copytrader', {
                                                method: 'PUT',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify(settings),
                                            });
                                        } catch (err) {
                                            console.error('Failed to save settings:', err);
                                        }
                                        setSettingsSaving(false);
                                    }}
                                >
                                    {settingsSaving ? 'Saving...' : 'Save Settings'}
                                </button>
                            </div>

                            {settings.liveTrading && (
                                <div className="warning-banner">
                                    ⚠️ Live trading is enabled. Real orders will be placed using your API credentials.
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
