import React from 'react';
import { Menu, Search, Bell, User, ChevronDown } from 'lucide-react';
import { useIDE } from '../context/IDEContext';

const Topbar = () => {
    const { toggleSidebar, openCommandPalette, activeProject } = useIDE();

    return (
        <header className="h-12 bg-seam-panel border-b border-seam-border flex items-center justify-between px-4 sticky top-0 z-10 w-full shrink-0">
            {/* Left: Project Context */}
            <div className="flex items-center gap-4 flex-1">
                <button onClick={toggleSidebar} className="md:hidden text-seam-text-muted hover:text-seam-text">
                    <Menu className="w-5 h-5" />
                </button>
                
                <div className="hidden md:flex items-center gap-2 text-sm">
                    <span className="font-semibold text-seam-text border-r border-seam-border pr-2">{activeProject}</span>
                    <button className="flex items-center gap-1 text-seam-text-muted hover:text-seam-text transition-colors">
                        <span className="font-mono text-xs bg-seam-accent/10 text-seam-accent px-1.5 py-0.5 rounded">main</span>
                        <ChevronDown className="w-3 h-3" />
                    </button>
                </div>
            </div>
            
            {/* Center: Command Palette Trigger */}
            <div className="flex-1 flex justify-center">
                <button 
                    onClick={openCommandPalette}
                    className="flex items-center gap-24 px-3 py-1.5 bg-seam-bg border border-seam-border hover:border-seam-accent/50 rounded-md text-sm text-seam-text-muted transition-colors w-full max-w-md group"
                >
                    <div className="flex items-center gap-2">
                        <Search className="w-4 h-4 group-hover:text-seam-accent transition-colors" />
                        <span>Search commands, files...</span>
                    </div>
                    <kbd className="hidden sm:inline-flex items-center gap-1 font-mono text-[10px] bg-seam-panel px-1.5 py-0.5 rounded border border-seam-border text-seam-text-muted">
                        <span className="text-xs">⌘</span>K
                    </kbd>
                </button>
            </div>

            {/* Right: Status & Profile */}
            <div className="flex items-center gap-4 flex-1 justify-end">
                <div className="hidden lg:flex items-center gap-3 text-xs">
                    <span className="text-seam-text-muted font-medium">Model: <span className="text-seam-text font-mono">llama3.1</span></span>
                    <div className="h-3 w-px bg-seam-border"></div>
                    <span className="px-1.5 py-0.5 bg-seam-accent/10 text-seam-accent font-mono font-bold rounded">REAL</span>
                </div>
                
                <div className="h-4 w-px bg-seam-border hidden sm:block"></div>
                
                <button className="text-seam-text-muted hover:text-seam-text relative">
                    <Bell className="w-4 h-4" />
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-seam-accent rounded-full"></span>
                </button>
                <button className="w-6 h-6 rounded-full bg-seam-accent/20 border border-seam-accent flex items-center justify-center text-seam-accent hover:bg-seam-accent hover:text-white transition-colors">
                    <User className="w-3.5 h-3.5" />
                </button>
            </div>
        </header>
    );
};

export default Topbar;
