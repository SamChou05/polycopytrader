/**
 * Settings Panel Component
 * Renders settings for any tool based on its settingsSchema from the registry.
 */

import React from 'react';
import type { SettingsField } from '../tools/registry';
import './SettingsPanel.css';

interface SettingsPanelProps {
    toolId: string;
    title: string;
    schema: SettingsField[];
    values: Record<string, unknown>;
    onChange: (key: string, value: unknown) => void;
    onClose: () => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
    title,
    schema,
    values,
    onChange,
    onClose,
}) => {
    const renderField = (field: SettingsField) => {
        const value = values[field.key];

        switch (field.type) {
            case 'text':
                return (
                    <input
                        type="text"
                        value={(value as string) ?? ''}
                        onChange={(e) => onChange(field.key, e.target.value)}
                        className="settings-input"
                    />
                );

            case 'number':
                return (
                    <input
                        type="number"
                        value={(value as number) ?? 0}
                        min={field.min}
                        max={field.max}
                        step={field.step}
                        onChange={(e) => onChange(field.key, parseFloat(e.target.value))}
                        className="settings-input"
                    />
                );

            case 'toggle':
                return (
                    <label className="settings-toggle">
                        <input
                            type="checkbox"
                            checked={(value as boolean) ?? false}
                            onChange={(e) => onChange(field.key, e.target.checked)}
                        />
                        <span className="toggle-slider"></span>
                    </label>
                );

            case 'select':
                return (
                    <select
                        value={(value as string) ?? ''}
                        onChange={(e) => onChange(field.key, e.target.value)}
                        className="settings-select"
                    >
                        {field.options?.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>
                );

            default:
                return <span>Unsupported field type</span>;
        }
    };

    return (
        <div className="settings-panel">
            <div className="settings-header">
                <h3>{title} Settings</h3>
                <button className="close-btn" onClick={onClose}>×</button>
            </div>

            <div className="settings-content">
                {schema.map((field) => (
                    <div key={field.key} className="settings-field">
                        <div className="field-header">
                            <label className="field-label">{field.label}</label>
                            {field.description && (
                                <span className="field-description">{field.description}</span>
                            )}
                        </div>
                        <div className="field-input">
                            {renderField(field)}
                        </div>
                    </div>
                ))}
            </div>

            <div className="settings-footer">
                <button className="save-btn" onClick={onClose}>Save & Close</button>
            </div>
        </div>
    );
};
