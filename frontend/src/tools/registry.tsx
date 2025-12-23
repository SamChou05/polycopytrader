/**
 * Tool Registry - Central configuration for all available tools.
 * 
 * To add a new tool:
 * 1. Create a component in src/tools/YourTool.tsx
 * 2. Create settings interface in this file
 * 3. Add entry to TOOL_REGISTRY
 * 4. That's it! The tool will appear in the menu and be fully functional.
 */

import React from 'react';

// ============================================
// Tool Configuration Types
// ============================================

export interface ToolConfig {
    id: string;
    name: string;
    icon: string;
    description: string;
    component: React.LazyExoticComponent<React.FC<ToolProps>> | React.FC<ToolProps>;

    // Settings
    defaultSettings: Record<string, unknown>;
    settingsSchema?: SettingsField[];

    // Permissions/Requirements
    requiresAuth?: boolean;
    requiresConnection?: boolean;

    // UI
    minWidth?: number;   // Minimum grid columns
    minHeight?: number;  // Minimum grid rows

    // Status
    enabled: boolean;
    comingSoon?: boolean;
}

export interface ToolProps {
    windowId: string;
    settings: Record<string, unknown>;
    onSettingsChange: (settings: Record<string, unknown>) => void;
}

export interface SettingsField {
    key: string;
    label: string;
    type: 'text' | 'number' | 'toggle' | 'select' | 'color';
    options?: { value: string; label: string }[];
    min?: number;
    max?: number;
    step?: number;
    description?: string;
}

// ============================================
// Tool Components (Lazy loaded for performance)
// ============================================

const CopyTrader = React.lazy(() =>
    import('./CopyTrader').then(m => ({ default: m.CopyTrader }))
);

// Placeholder for future tools
const PlaceholderTool: React.FC<ToolProps> = () => (
    <div style= {{ padding: 20, textAlign: 'center', color: '#666' }}>
        <p>Coming Soon </p>
            </div>
);

// ============================================
// Tool Registry
// ============================================

export const TOOL_REGISTRY: Record<string, ToolConfig> = {
    'copy-trader': {
        id: 'copy-trader',
        name: 'Copy Trader',
        icon: '📊',
        description: 'Monitor and copy trades from target wallets',
        component: CopyTrader,
        enabled: true,
        requiresConnection: true,
        defaultSettings: {
            mode: 'percentage',
            percentage: 0.1,
            minSize: 0.1,
            executionMode: 'alert', // 'alert' | 'execute'
            dryRun: true,
        },
        settingsSchema: [
            {
                key: 'executionMode',
                label: 'Execution Mode',
                type: 'select',
                options: [
                    { value: 'alert', label: 'Alert Only' },
                    { value: 'execute', label: 'Execute Trades' },
                ],
                description: 'Whether to just alert or actually execute trades',
            },
            {
                key: 'dryRun',
                label: 'Dry Run',
                type: 'toggle',
                description: 'Simulate trades without placing real orders',
            },
            {
                key: 'mode',
                label: 'Sizing Mode',
                type: 'select',
                options: [
                    { value: 'percentage', label: 'Percentage' },
                    { value: 'fixed', label: 'Fixed Size' },
                    { value: 'portfolio', label: 'Portfolio Scaling' },
                ],
            },
            {
                key: 'percentage',
                label: 'Copy Percentage',
                type: 'number',
                min: 0.01,
                max: 1,
                step: 0.01,
                description: 'Percentage of target trade size to copy',
            },
            {
                key: 'minSize',
                label: 'Minimum Size',
                type: 'number',
                min: 0.1,
                step: 0.1,
                description: 'Minimum trade size to copy',
            },
        ],
    },

    'market-scanner': {
        id: 'market-scanner',
        name: 'Market Scanner',
        icon: '🔍',
        description: 'Scan markets for opportunities',
        component: PlaceholderTool,
        enabled: false,
        comingSoon: true,
        defaultSettings: {},
    },

    'portfolio': {
        id: 'portfolio',
        name: 'Portfolio',
        icon: '💼',
        description: 'View and manage your portfolio',
        component: PlaceholderTool,
        enabled: false,
        comingSoon: true,
        requiresAuth: true,
        defaultSettings: {},
    },

    'charts': {
        id: 'charts',
        name: 'Charts',
        icon: '📈',
        description: 'Price and volume charts',
        component: PlaceholderTool,
        enabled: false,
        comingSoon: true,
        defaultSettings: {},
    },

    'order-book': {
        id: 'order-book',
        name: 'Order Book',
        icon: '📋',
        description: 'Real-time order book viewer',
        component: PlaceholderTool,
        enabled: false,
        comingSoon: true,
        defaultSettings: {},
    },
};

// ============================================
// Helper Functions
// ============================================

export function getEnabledTools(): ToolConfig[] {
    return Object.values(TOOL_REGISTRY).filter(t => t.enabled);
}

export function getAllTools(): ToolConfig[] {
    return Object.values(TOOL_REGISTRY);
}

export function getToolById(id: string): ToolConfig | undefined {
    return TOOL_REGISTRY[id];
}

export function isToolEnabled(id: string): boolean {
    return TOOL_REGISTRY[id]?.enabled ?? false;
}
