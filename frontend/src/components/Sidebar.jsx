import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
    LayoutDashboard, Folder, FlaskConical, CheckSquare, 
    ShieldCheck, Rocket, GitBranch, Archive, ScrollText, 
    BookOpen, Settings, Activity 
} from 'lucide-react';
import { useIDE } from '../context/IDEContext';

const Sidebar = () => {
    const { isSidebarCollapsed, toggleSidebar } = useIDE();

    const primaryNav = [
        { name: 'Workspace', path: '/workspace', icon: LayoutDashboard },
        { name: 'Projects', path: '/projects', icon: Folder },
        { name: 'Experiments', path: '/experiments', icon: FlaskConical },
        { name: 'Tasks', path: '/tasks', icon: CheckSquare },
        { name: 'QA', path: '/qa', icon: ShieldCheck },
        { name: 'Delivery', path: '/delivery', icon: Rocket },
    ];

    const secondaryNav = [
        { name: 'Git', path: '#', icon: GitBranch },
        { name: 'Artifacts', path: '#', icon: Archive },
        { name: 'Logs', path: '#', icon: ScrollText },
        { name: 'Knowledge', path: '#', icon: BookOpen },
        { name: 'Settings', path: '/settings', icon: Settings },
    ];

    const renderNavItems = (items) => (
        items.map((item) => (
            <NavLink
                key={item.name}
                to={item.path}
                title={isSidebarCollapsed ? item.name : undefined}
                className={({ isActive }) =>
                    `flex items-center ${isSidebarCollapsed ? 'justify-center' : 'gap-3'} px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                        isActive && item.path !== '#'
                            ? 'bg-seam-accent/10 text-seam-accent' 
                            : 'text-seam-text-muted hover:text-seam-text hover:bg-seam-border/50'
                    }`
                }
            >
                <item.icon className="w-5 h-5 shrink-0" />
                {!isSidebarCollapsed && <span>{item.name}</span>}
            </NavLink>
        ))
    );

    return (
        <aside className={`${isSidebarCollapsed ? 'w-16' : 'w-64'} bg-seam-panel border-r border-seam-border flex flex-col h-screen fixed left-0 top-0 hidden md:flex transition-all duration-300 z-20`}>
            {/* Header */}
            <div className={`p-4 flex items-center ${isSidebarCollapsed ? 'justify-center' : 'justify-between'} h-16 border-b border-seam-border shrink-0 cursor-pointer`} onClick={toggleSidebar}>
                {!isSidebarCollapsed && (
                    <div className="flex flex-col overflow-hidden">
                        <span className="font-bold text-seam-text truncate">SEAM OS</span>
                    </div>
                )}
                {isSidebarCollapsed && <span className="font-bold text-seam-accent">S</span>}
            </div>
            
            {/* Nav */}
            <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-6">
                <nav className="px-2 space-y-1">
                    {renderNavItems(primaryNav)}
                </nav>
                <nav className="px-2 space-y-1 mt-auto">
                    {renderNavItems(secondaryNav)}
                </nav>
            </div>

            {/* Footer */}
            <div className={`p-4 border-t border-seam-border shrink-0 flex items-center ${isSidebarCollapsed ? 'justify-center' : 'gap-3'} cursor-help`} title="System Status: Ollama Online (REAL Mode)">
                <div className="relative flex h-3 w-3 shrink-0">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-seam-success opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-seam-success"></span>
                </div>
                {!isSidebarCollapsed && (
                    <div className="flex flex-col">
                        <span className="text-xs font-semibold text-seam-text truncate">Ollama Online</span>
                        <span className="text-[10px] text-seam-text-muted font-mono truncate">REAL Mode</span>
                    </div>
                )}
            </div>
        </aside>
    );
};

export default Sidebar;
