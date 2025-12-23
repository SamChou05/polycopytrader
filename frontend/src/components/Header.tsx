import React from 'react';
import { useAppStore } from '../stores/appStore';
import { useWindowStore } from '../stores/windowStore';
import { getAllTools } from '../tools/registry';
import './Header.css';

interface HeaderProps {
    onOpenTool: (toolId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenTool }) => {
    const { isConnected, mode } = useAppStore();
    const {
        windows,
        tileWindows,
        saveLayoutPreset,
        loadLayoutPreset,
        deleteLayoutPreset,
        layoutPresets,
        snapToGrid,
        snapToEdge,
        setSnapToGrid,
        setSnapToEdge,
    } = useWindowStore();

    const [toolsMenuOpen, setToolsMenuOpen] = React.useState(false);
    const [layoutMenuOpen, setLayoutMenuOpen] = React.useState(false);
    const [saveDialogOpen, setSaveDialogOpen] = React.useState(false);
    const [presetName, setPresetName] = React.useState('');

    const tools = getAllTools();
    const minimizedWindows = windows.filter(w => w.isMinimized);

    const handleSavePreset = () => {
        if (presetName.trim()) {
            saveLayoutPreset(presetName.trim());
            setPresetName('');
            setSaveDialogOpen(false);
        }
    };

    return (
        <header className="app-header">
            <div className="header-left">
                <div className="status-indicator">
                    <span className={`status-dot ${isConnected ? 'online' : 'offline'}`} />
                    <span className="status-text">{isConnected ? 'LIVE' : 'OFFLINE'}</span>
                </div>
            </div>

            <div className="header-center">
                {/* Tools Menu */}
                <div className="dropdown-container">
                    <button
                        className="header-btn"
                        onClick={() => { setToolsMenuOpen(!toolsMenuOpen); setLayoutMenuOpen(false); }}
                    >
                        <span>Tools</span>
                        <span className="dropdown-arrow">▼</span>
                    </button>

                    {toolsMenuOpen && (
                        <div className="dropdown-menu">
                            {tools.map(tool => (
                                <button
                                    key={tool.id}
                                    className={`menu-item ${tool.comingSoon ? 'disabled' : ''}`}
                                    onClick={() => {
                                        if (!tool.comingSoon) {
                                            onOpenTool(tool.id);
                                            setToolsMenuOpen(false);
                                        }
                                    }}
                                >
                                    <span className="menu-icon">{tool.icon}</span>
                                    <span className="menu-label">{tool.name}</span>
                                    {tool.comingSoon && <span className="badge">Soon</span>}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Layout Menu */}
                <div className="dropdown-container">
                    <button
                        className="header-btn"
                        onClick={() => { setLayoutMenuOpen(!layoutMenuOpen); setToolsMenuOpen(false); }}
                    >
                        <span>Layout</span>
                        <span className="dropdown-arrow">▼</span>
                    </button>

                    {layoutMenuOpen && (
                        <div className="dropdown-menu layout-menu">
                            <div className="menu-section">
                                <span className="section-title">Arrange</span>
                                <button className="menu-item" onClick={() => { tileWindows('grid'); setLayoutMenuOpen(false); }}>
                                    <span className="menu-icon">▦</span>
                                    <span className="menu-label">Tile Grid</span>
                                </button>
                                <button className="menu-item" onClick={() => { tileWindows('horizontal'); setLayoutMenuOpen(false); }}>
                                    <span className="menu-icon">▤</span>
                                    <span className="menu-label">Tile Horizontal</span>
                                </button>
                                <button className="menu-item" onClick={() => { tileWindows('vertical'); setLayoutMenuOpen(false); }}>
                                    <span className="menu-icon">▥</span>
                                    <span className="menu-label">Tile Vertical</span>
                                </button>
                                <button className="menu-item" onClick={() => { tileWindows('cascade'); setLayoutMenuOpen(false); }}>
                                    <span className="menu-icon">◫</span>
                                    <span className="menu-label">Cascade</span>
                                </button>
                            </div>

                            <div className="menu-divider" />

                            <div className="menu-section">
                                <span className="section-title">Snapping</span>
                                <button className="menu-item" onClick={() => setSnapToEdge(!snapToEdge)}>
                                    <span className="menu-icon">{snapToEdge ? '☑' : '☐'}</span>
                                    <span className="menu-label">Snap to Edge</span>
                                </button>
                                <button className="menu-item" onClick={() => setSnapToGrid(!snapToGrid)}>
                                    <span className="menu-icon">{snapToGrid ? '☑' : '☐'}</span>
                                    <span className="menu-label">Snap to Grid</span>
                                </button>
                            </div>

                            <div className="menu-divider" />

                            <div className="menu-section">
                                <span className="section-title">Saved Layouts</span>
                                <button className="menu-item" onClick={() => { setSaveDialogOpen(true); setLayoutMenuOpen(false); }}>
                                    <span className="menu-icon">+</span>
                                    <span className="menu-label">Save Current Layout</span>
                                </button>
                                {layoutPresets.map(preset => (
                                    <div key={preset.id} className="menu-item preset-item">
                                        <button className="preset-load" onClick={() => { loadLayoutPreset(preset.id); setLayoutMenuOpen(false); }}>
                                            <span className="menu-icon">◧</span>
                                            <span className="menu-label">{preset.name}</span>
                                        </button>
                                        <button className="preset-delete" onClick={() => deleteLayoutPreset(preset.id)} title="Delete">
                                            ×
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                <h1 className="app-title">POLYMARKET TERMINAL</h1>
            </div>

            <div className="header-right">
                {/* Minimized windows taskbar */}
                {minimizedWindows.length > 0 && (
                    <div className="taskbar">
                        {minimizedWindows.map(w => (
                            <button
                                key={w.id}
                                className="taskbar-item"
                                onClick={() => useWindowStore.getState().focusWindow(w.id)}
                                title={w.title}
                            >
                                {w.title.slice(0, 10)}
                            </button>
                        ))}
                    </div>
                )}

                <span className={`mode-badge ${mode === 'LIVE' ? 'live' : ''}`}>
                    {mode === 'DRY_RUN' ? 'DRY RUN' : 'LIVE'}
                </span>
            </div>

            {/* Save Layout Dialog */}
            {saveDialogOpen && (
                <div className="modal-overlay" onClick={() => setSaveDialogOpen(false)}>
                    <div className="save-dialog" onClick={e => e.stopPropagation()}>
                        <h3>Save Layout</h3>
                        <input
                            type="text"
                            placeholder="Layout name..."
                            value={presetName}
                            onChange={e => setPresetName(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSavePreset()}
                            autoFocus
                        />
                        <div className="dialog-buttons">
                            <button onClick={() => setSaveDialogOpen(false)}>Cancel</button>
                            <button className="primary" onClick={handleSavePreset}>Save</button>
                        </div>
                    </div>
                </div>
            )}
        </header>
    );
};
