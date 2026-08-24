import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Topbar from '../components/Topbar';
import CommandPalette from '../components/ide/CommandPalette';
import { useIDE } from '../context/IDEContext';

const IDELayout = () => {
    const { isSidebarCollapsed, openCommandPalette } = useIDE();

    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                openCommandPalette();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [openCommandPalette]);

    return (
        <div className="h-screen w-screen bg-seam-bg flex overflow-hidden text-seam-text font-sans">
            <Sidebar />
            <div className={`flex-1 flex flex-col transition-all duration-300 ${isSidebarCollapsed ? 'md:ml-16' : 'md:ml-64'}`}>
                <Topbar />
                <main className="flex-1 flex flex-col overflow-hidden relative">
                    <Outlet />
                </main>
            </div>
            <CommandPalette />
        </div>
    );
};

export default IDELayout;
