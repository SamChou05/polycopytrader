import React, { Suspense, useState, useCallback } from 'react';
import { useWindowStore } from './stores/windowStore';
import { Header } from './components/Header';
import { ToolWindow } from './components/ToolWindow';
import { SettingsPanel } from './components/SettingsPanel';
import { useSocket } from './hooks/useSocket';
import { TOOL_REGISTRY, getToolById, type ToolProps } from './tools/registry';
import './App.css';

function App() {
  const { windows, openWindow } = useWindowStore();
  const [settingsOpen, setSettingsOpen] = useState<string | null>(null);
  const [toolSettings, setToolSettings] = useState<Record<string, Record<string, unknown>>>({});

  // Initialize WebSocket connection
  useSocket();

  const handleOpenTool = useCallback((toolId: string) => {
    const tool = getToolById(toolId);
    if (!tool || !tool.enabled) return;

    // Initialize settings with defaults
    if (!toolSettings[toolId]) {
      setToolSettings(prev => ({
        ...prev,
        [toolId]: { ...tool.defaultSettings },
      }));
    }

    // Open new window (store handles positioning)
    openWindow(toolId, tool.name);
  }, [toolSettings, openWindow]);

  const handleOpenSettings = useCallback((toolId: string) => {
    setSettingsOpen(toolId);
  }, []);

  const handleCloseSettings = useCallback(() => {
    setSettingsOpen(null);
  }, []);

  const handleSettingChange = useCallback((toolId: string, key: string, value: unknown) => {
    setToolSettings(prev => ({
      ...prev,
      [toolId]: {
        ...prev[toolId],
        [key]: value,
      },
    }));
  }, []);

  // Open Copy Trader by default on first load (maximized)
  const initializedRef = React.useRef(false);
  React.useEffect(() => {
    if (!initializedRef.current && windows.length === 0) {
      initializedRef.current = true;
      openWindow('copy-trader', 'COPY TRADER', {
        isMaximized: true,
        position: { x: 0, y: 0 },
        size: { width: window.innerWidth, height: window.innerHeight - 60 },
      });
    }
  }, [windows.length, openWindow]);

  // Get settings for open tool
  const settingsTool = settingsOpen ? getToolById(settingsOpen) : null;

  return (
    <div className="app">
      <Header onOpenTool={handleOpenTool} />

      {/* Free-form workspace for Bloomberg-style widgets */}
      <main className="workspace">
        {windows.map(window => {
          const tool = TOOL_REGISTRY[window.toolId];
          if (!tool) return null;

          const ToolComponent = tool.component as React.FC<ToolProps>;
          const settings = toolSettings[window.toolId] || tool.defaultSettings;

          return (
            <ToolWindow
              key={window.id}
              id={window.id}
              title={window.title}
              onSettings={() => handleOpenSettings(window.toolId)}
              hasSettings={!!tool.settingsSchema?.length}
            >
              <Suspense fallback={<div className="loading">Loading...</div>}>
                <ToolComponent
                  windowId={window.id}
                  settings={settings}
                  onSettingsChange={(newSettings) => {
                    setToolSettings(prev => ({
                      ...prev,
                      [window.toolId]: newSettings,
                    }));
                  }}
                />
              </Suspense>
            </ToolWindow>
          );
        })}

        {windows.filter(w => !w.isMinimized).length === 0 && (
          <div className="empty-workspace">
            <div className="empty-content">
              <h2>Welcome to Polymarket Terminal</h2>
              <p>Open tools from the menu above to get started</p>
              <button className="open-tool-btn" onClick={() => handleOpenTool('copy-trader')}>
                📊 Open Copy Trader
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Settings Modal */}
      {settingsTool && settingsTool.settingsSchema && (
        <div className="modal-overlay" onClick={handleCloseSettings}>
          <div onClick={(e) => e.stopPropagation()}>
            <SettingsPanel
              toolId={settingsTool.id}
              title={settingsTool.name}
              schema={settingsTool.settingsSchema}
              values={toolSettings[settingsTool.id] || settingsTool.defaultSettings}
              onChange={(key, value) => handleSettingChange(settingsTool.id, key, value)}
              onClose={handleCloseSettings}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
