import React, { useRef, useState, useCallback, useEffect } from 'react';
import { useWindowStore } from '../stores/windowStore';
import './ToolWindow.css';

interface ToolWindowProps {
    id: string;
    title: string;
    children: React.ReactNode;
    onSettings?: () => void;
    hasSettings?: boolean;
}

/**
 * Bloomberg-style draggable, resizable window widget.
 * Features: Free-form drag, resize from edges/corners, minimize/maximize/close
 */
export const ToolWindow: React.FC<ToolWindowProps> = ({
    id,
    title,
    children,
    onSettings,
    hasSettings = false
}) => {
    const windowRef = useRef<HTMLDivElement>(null);
    const {
        windows,
        activeWindowId,
        focusWindow,
        closeWindow,
        minimizeWindow,
        maximizeWindow,
        restoreWindow,
        moveWindow,
        resizeWindow,
    } = useWindowStore();

    const window = windows.find(w => w.id === id);
    if (!window) return null;

    const isActive = activeWindowId === id;

    // Drag state
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

    // Resize state
    const [isResizing, setIsResizing] = useState(false);
    const [resizeDirection, setResizeDirection] = useState<string>('');
    const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0, posX: 0, posY: 0 });

    // Handle mouse down on title bar (start drag)
    const handleTitleMouseDown = useCallback((e: React.MouseEvent) => {
        if (window.isMaximized) return;
        e.preventDefault();
        focusWindow(id);
        setIsDragging(true);
        setDragOffset({
            x: e.clientX - window.position.x,
            y: e.clientY - window.position.y,
        });
    }, [id, window.position, window.isMaximized, focusWindow]);

    // Handle mouse down on resize handles
    const handleResizeMouseDown = useCallback((e: React.MouseEvent, direction: string) => {
        if (window.isMaximized) return;
        e.preventDefault();
        e.stopPropagation();
        focusWindow(id);
        setIsResizing(true);
        setResizeDirection(direction);
        setResizeStart({
            x: e.clientX,
            y: e.clientY,
            width: window.size.width,
            height: window.size.height,
            posX: window.position.x,
            posY: window.position.y,
        });
    }, [id, window, focusWindow]);

    // Handle mouse move (for drag and resize)
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                const newX = e.clientX - dragOffset.x;
                const newY = e.clientY - dragOffset.y;
                moveWindow(id, { x: Math.max(0, newX), y: Math.max(0, newY) });
            }

            if (isResizing) {
                const deltaX = e.clientX - resizeStart.x;
                const deltaY = e.clientY - resizeStart.y;

                let newWidth = resizeStart.width;
                let newHeight = resizeStart.height;
                let newX = resizeStart.posX;
                let newY = resizeStart.posY;

                // Handle resize directions
                if (resizeDirection.includes('e')) {
                    newWidth = resizeStart.width + deltaX;
                }
                if (resizeDirection.includes('w')) {
                    newWidth = resizeStart.width - deltaX;
                    newX = resizeStart.posX + deltaX;
                }
                if (resizeDirection.includes('s')) {
                    newHeight = resizeStart.height + deltaY;
                }
                if (resizeDirection.includes('n')) {
                    newHeight = resizeStart.height - deltaY;
                    newY = resizeStart.posY + deltaY;
                }

                // Apply minimum size constraints
                if (newWidth >= 300) {
                    if (resizeDirection.includes('w')) {
                        moveWindow(id, { x: newX, y: window.position.y });
                    }
                    resizeWindow(id, { width: newWidth, height: window.size.height });
                }

                if (newHeight >= 200) {
                    if (resizeDirection.includes('n')) {
                        moveWindow(id, { x: window.position.x, y: newY });
                    }
                    resizeWindow(id, { width: window.size.width, height: newHeight });
                }
            }
        };

        const handleMouseUp = () => {
            setIsDragging(false);
            setIsResizing(false);
        };

        if (isDragging || isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, isResizing, dragOffset, resizeStart, resizeDirection, id, moveWindow, resizeWindow, window]);

    // Control button handlers
    const handleClose = (e: React.MouseEvent) => {
        e.stopPropagation();
        closeWindow(id);
    };

    const handleMinimize = (e: React.MouseEvent) => {
        e.stopPropagation();
        minimizeWindow(id);
    };

    const handleMaximize = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (window.isMaximized) {
            restoreWindow(id);
        } else {
            maximizeWindow(id);
        }
    };

    const handleSettings = (e: React.MouseEvent) => {
        e.stopPropagation();
        onSettings?.();
    };

    const handleDoubleClick = () => {
        if (window.isMaximized) {
            restoreWindow(id);
        } else {
            maximizeWindow(id);
        }
    };

    if (window.isMinimized) return null;

    // Calculate styles based on maximized state
    const windowStyle: React.CSSProperties = window.isMaximized
        ? {
            position: 'fixed',
            left: 0,
            top: 60, // Below header
            width: '100vw',
            height: 'calc(100vh - 60px)',
            zIndex: window.zIndex + 1000,
        }
        : {
            position: 'absolute',
            left: window.position.x,
            top: window.position.y,
            width: window.size.width,
            height: window.size.height,
            zIndex: window.zIndex,
        };

    return (
        <div
            ref={windowRef}
            className={`tool-window ${isActive ? 'active' : ''} ${window.isMaximized ? 'maximized' : ''} ${isDragging ? 'dragging' : ''}`}
            style={windowStyle}
            onMouseDown={() => focusWindow(id)}
        >
            {/* Title bar */}
            <div
                className="tool-window-header"
                onMouseDown={handleTitleMouseDown}
                onDoubleClick={handleDoubleClick}
            >
                <span className="tool-window-title">{title}</span>
                <div className="tool-window-controls">
                    {hasSettings && (
                        <button className="control-btn settings" onClick={handleSettings} title="Settings">
                            ⚙
                        </button>
                    )}
                    <button className="control-btn minimize" onClick={handleMinimize} title="Minimize">
                        −
                    </button>
                    <button className="control-btn maximize" onClick={handleMaximize} title={window.isMaximized ? 'Restore' : 'Maximize'}>
                        {window.isMaximized ? '◱' : '□'}
                    </button>
                    <button className="control-btn close" onClick={handleClose} title="Close">
                        ×
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="tool-window-content">
                {children}
            </div>

            {/* Resize handles */}
            {!window.isMaximized && (
                <>
                    <div className="resize-handle resize-n" onMouseDown={(e) => handleResizeMouseDown(e, 'n')} />
                    <div className="resize-handle resize-s" onMouseDown={(e) => handleResizeMouseDown(e, 's')} />
                    <div className="resize-handle resize-e" onMouseDown={(e) => handleResizeMouseDown(e, 'e')} />
                    <div className="resize-handle resize-w" onMouseDown={(e) => handleResizeMouseDown(e, 'w')} />
                    <div className="resize-handle resize-ne" onMouseDown={(e) => handleResizeMouseDown(e, 'ne')} />
                    <div className="resize-handle resize-nw" onMouseDown={(e) => handleResizeMouseDown(e, 'nw')} />
                    <div className="resize-handle resize-se" onMouseDown={(e) => handleResizeMouseDown(e, 'se')} />
                    <div className="resize-handle resize-sw" onMouseDown={(e) => handleResizeMouseDown(e, 'sw')} />
                </>
            )}
        </div>
    );
};
