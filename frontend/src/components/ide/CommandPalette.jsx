import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Folder, LayoutDashboard, CheckSquare, ShieldCheck, Rocket, FlaskConical, ScrollText, Terminal } from 'lucide-react';
import { useIDE } from '../../context/IDEContext';

const CommandPalette = () => {
    const { isCommandPaletteOpen, closeCommandPalette, toggleSidebar, toggleTerminal } = useIDE();
    const navigate = useNavigate();
    const inputRef = useRef(null);

    useEffect(() => {
        if (isCommandPaletteOpen) {
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    }, [isCommandPaletteOpen]);

    if (!isCommandPaletteOpen) return null;

    const commands = [
        { name: 'Go to Workspace', icon: LayoutDashboard, action: () => navigate('/workspace') },
        { name: 'Open Projects', icon: Folder, action: () => navigate('/projects') },
        { name: 'Open Experiments', icon: FlaskConical, action: () => navigate('/experiments') },
        { name: 'Open Tasks', icon: CheckSquare, action: () => navigate('/tasks') },
        { name: 'Open QA', icon: ShieldCheck, action: () => navigate('/qa') },
        { name: 'Open Delivery', icon: Rocket, action: () => navigate('/delivery') },
        { name: 'Toggle Sidebar', icon: LayoutDashboard, action: toggleSidebar },
        { name: 'Toggle Terminal', icon: Terminal, action: toggleTerminal },
        { name: 'Open Logs', icon: ScrollText, action: () => { toggleTerminal(); /* logic to open logs tab */ } },
    ];

    const executeCommand = (action) => {
        action();
        closeCommandPalette();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/50 backdrop-blur-sm" onClick={closeCommandPalette}>
            <div 
                className="w-full max-w-2xl bg-seam-panel border border-seam-border rounded-xl shadow-2xl overflow-hidden flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-center px-4 py-3 border-b border-seam-border bg-seam-bg">
                    <Search className="w-5 h-5 text-seam-text-muted mr-3" />
                    <input 
                        ref={inputRef}
                        type="text"
                        placeholder="Search commands, files, experiments..."
                        className="flex-1 bg-transparent text-seam-text outline-none placeholder:text-seam-text-muted"
                        onKeyDown={(e) => {
                            if (e.key === 'Escape') closeCommandPalette();
                        }}
                    />
                    <kbd className="hidden sm:inline-flex items-center gap-1 font-mono text-[10px] bg-seam-panel px-1.5 py-0.5 rounded border border-seam-border text-seam-text-muted">
                        ESC
                    </kbd>
                </div>
                
                <div className="max-h-[60vh] overflow-y-auto p-2 space-y-1">
                    <div className="px-3 py-2 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Suggested</div>
                    {commands.map((cmd, i) => (
                        <button
                            key={i}
                            onClick={() => executeCommand(cmd.action)}
                            className="w-full flex items-center px-3 py-2.5 rounded-lg text-sm text-seam-text hover:bg-seam-accent/10 hover:text-seam-accent transition-colors text-left group"
                        >
                            <cmd.icon className="w-4 h-4 mr-3 text-seam-text-muted group-hover:text-seam-accent" />
                            {cmd.name}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default CommandPalette;
