import React, { useState, useEffect } from 'react';
import './WalletManager.css';

interface Wallet {
    id: number;
    address: string;
    name: string;
    description: string;
    username: string | null;
    enabled: boolean;
    created_at: string;
}

interface WalletManagerProps {
    onWalletChange?: () => void;
}

export const WalletManager: React.FC<WalletManagerProps> = ({ onWalletChange }) => {
    const [wallets, setWallets] = useState<Wallet[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Add wallet modal state
    const [showAddModal, setShowAddModal] = useState(false);
    const [newWallet, setNewWallet] = useState({
        address: '',
        name: '',
        description: '',
    });
    const [adding, setAdding] = useState(false);
    const [fetchingProfile, setFetchingProfile] = useState(false);
    const [fetchedUsername, setFetchedUsername] = useState<string | null>(null);

    // Edit wallet modal state
    const [editingWallet, setEditingWallet] = useState<Wallet | null>(null);

    // Fetch wallets from API
    const fetchWallets = async () => {
        try {
            const response = await fetch('/api/wallets');
            if (!response.ok) throw new Error('Failed to fetch wallets');
            const data = await response.json();
            setWallets(data);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch wallets');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWallets();
    }, []);

    // Fetch username from Polymarket when address changes
    const fetchUsername = async (address: string) => {
        if (!address || address.length < 10) return;

        setFetchingProfile(true);
        setFetchedUsername(null);

        try {
            // The API will auto-fetch when we add, but we can preview it here
            const response = await fetch(`/api/wallets/${address}`);
            if (response.ok) {
                const data = await response.json();
                if (data.username) {
                    setFetchedUsername(data.username);
                }
            }
        } catch {
            // Ignore errors - we'll just not show a username
        } finally {
            setFetchingProfile(false);
        }
    };

    // Add a new wallet
    const handleAddWallet = async () => {
        if (!newWallet.address) return;

        setAdding(true);
        try {
            const response = await fetch('/api/wallets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newWallet),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to add wallet');
            }

            // Reset form and close modal
            setNewWallet({ address: '', name: '', description: '' });
            setFetchedUsername(null);
            setShowAddModal(false);

            // Refresh wallet list
            await fetchWallets();
            onWalletChange?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to add wallet');
        } finally {
            setAdding(false);
        }
    };

    // Toggle wallet enabled/disabled
    const handleToggleWallet = async (address: string) => {
        try {
            const response = await fetch(`/api/wallets/${address}/toggle`, {
                method: 'POST',
            });

            if (!response.ok) throw new Error('Failed to toggle wallet');

            await fetchWallets();
            onWalletChange?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to toggle wallet');
        }
    };

    // Delete wallet
    const handleDeleteWallet = async (address: string) => {
        if (!confirm('Are you sure you want to delete this wallet?')) return;

        try {
            const response = await fetch(`/api/wallets/${address}`, {
                method: 'DELETE',
            });

            if (!response.ok) throw new Error('Failed to delete wallet');

            await fetchWallets();
            onWalletChange?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete wallet');
        }
    };

    // Update wallet
    const handleUpdateWallet = async () => {
        if (!editingWallet) return;

        try {
            const response = await fetch(`/api/wallets/${editingWallet.address}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: editingWallet.name,
                    // description would require an API update
                }),
            });

            if (!response.ok) throw new Error('Failed to update wallet');

            setEditingWallet(null);
            await fetchWallets();
            onWalletChange?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update wallet');
        }
    };

    // Format address for display
    const formatAddress = (address: string) => {
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

    if (loading) {
        return <div className="wallet-manager loading">Loading wallets...</div>;
    }

    return (
        <div className="wallet-manager">
            <div className="wallet-header">
                <h3>Tracked Wallets</h3>
                <button className="add-btn" onClick={() => setShowAddModal(true)}>
                    + Add Wallet
                </button>
            </div>

            {error && (
                <div className="error-banner">
                    {error}
                    <button onClick={() => setError(null)}>×</button>
                </div>
            )}

            <div className="wallet-list">
                {wallets.length === 0 ? (
                    <div className="empty-state">
                        <p>No wallets tracked yet</p>
                        <p className="hint">Add a wallet address to start tracking trades</p>
                    </div>
                ) : (
                    wallets.map(wallet => (
                        <div
                            key={wallet.id}
                            className={`wallet-item ${wallet.enabled ? '' : 'disabled'}`}
                        >
                            <div className="wallet-main">
                                <div className="wallet-toggle">
                                    <button
                                        className={`toggle-btn ${wallet.enabled ? 'on' : 'off'}`}
                                        onClick={() => handleToggleWallet(wallet.address)}
                                        title={wallet.enabled ? 'Disable tracking' : 'Enable tracking'}
                                    >
                                        {wallet.enabled ? '●' : '○'}
                                    </button>
                                </div>

                                <div className="wallet-info">
                                    <div className="wallet-name">
                                        {wallet.name}
                                        {wallet.username && (
                                            <span className="wallet-username">@{wallet.username}</span>
                                        )}
                                    </div>
                                    <div className="wallet-address">
                                        <code>{formatAddress(wallet.address)}</code>
                                        <button
                                            className="copy-btn"
                                            onClick={() => navigator.clipboard.writeText(wallet.address)}
                                            title="Copy full address"
                                        >
                                            📋
                                        </button>
                                    </div>
                                    {wallet.description && (
                                        <div className="wallet-description">{wallet.description}</div>
                                    )}
                                </div>

                                <div className="wallet-actions">
                                    <button
                                        className="edit-btn"
                                        onClick={() => setEditingWallet(wallet)}
                                        title="Edit"
                                    >
                                        ✏️
                                    </button>
                                    <button
                                        className="delete-btn"
                                        onClick={() => handleDeleteWallet(wallet.address)}
                                        title="Delete"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Add Wallet Modal */}
            {showAddModal && (
                <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <h3>Add Wallet to Track</h3>

                        <div className="form-group">
                            <label>Wallet Address *</label>
                            <input
                                type="text"
                                placeholder="0x..."
                                value={newWallet.address}
                                onChange={e => {
                                    setNewWallet({ ...newWallet, address: e.target.value });
                                    if (e.target.value.length >= 42) {
                                        fetchUsername(e.target.value);
                                    }
                                }}
                            />
                            {fetchingProfile && (
                                <span className="fetching">Looking up profile...</span>
                            )}
                            {fetchedUsername && (
                                <span className="found-username">Found: @{fetchedUsername}</span>
                            )}
                        </div>

                        <div className="form-group">
                            <label>Display Name</label>
                            <input
                                type="text"
                                placeholder={fetchedUsername || "Custom name for this wallet"}
                                value={newWallet.name}
                                onChange={e => setNewWallet({ ...newWallet, name: e.target.value })}
                            />
                            <span className="hint">Leave blank to use Polymarket username</span>
                        </div>

                        <div className="form-group">
                            <label>Notes / Description</label>
                            <textarea
                                placeholder="Why are you tracking this wallet? (optional)"
                                value={newWallet.description}
                                onChange={e => setNewWallet({ ...newWallet, description: e.target.value })}
                                rows={3}
                            />
                        </div>

                        <div className="modal-actions">
                            <button
                                className="cancel-btn"
                                onClick={() => {
                                    setShowAddModal(false);
                                    setNewWallet({ address: '', name: '', description: '' });
                                    setFetchedUsername(null);
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                className="submit-btn"
                                onClick={handleAddWallet}
                                disabled={adding || !newWallet.address}
                            >
                                {adding ? 'Adding...' : 'Add Wallet'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit Wallet Modal */}
            {editingWallet && (
                <div className="modal-overlay" onClick={() => setEditingWallet(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <h3>Edit Wallet</h3>

                        <div className="form-group">
                            <label>Address</label>
                            <code className="address-display">{editingWallet.address}</code>
                        </div>

                        <div className="form-group">
                            <label>Display Name</label>
                            <input
                                type="text"
                                value={editingWallet.name}
                                onChange={e => setEditingWallet({ ...editingWallet, name: e.target.value })}
                            />
                        </div>

                        <div className="modal-actions">
                            <button className="cancel-btn" onClick={() => setEditingWallet(null)}>
                                Cancel
                            </button>
                            <button className="submit-btn" onClick={handleUpdateWallet}>
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
