import React, { createContext, useContext, useState } from 'react';

const IDEContext = createContext();

export const useIDE = () => {
    return useContext(IDEContext);
};

export const IDEProvider = ({ children }) => {
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
    const [isTerminalExpanded, setIsTerminalExpanded] = useState(false);
    const [activeTerminalTab, setActiveTerminalTab] = useState('Terminal');
    const [isAIPanelOpen, setIsAIPanelOpen] = useState(true);
    
    // Editor State
    const [openTabs, setOpenTabs] = useState([{ id: 'main.py', type: 'Python' }]);
    const [activeTab, setActiveTab] = useState('main.py');
    const [activeProject, setActiveProject] = useState('E-Commerce Catalog');
    
    // Task Drawer
    const [selectedTask, setSelectedTask] = useState(null);
    const [isTaskDrawerOpen, setIsTaskDrawerOpen] = useState(false);

    const toggleSidebar = () => setIsSidebarCollapsed(!isSidebarCollapsed);
    const toggleTerminal = () => setIsTerminalExpanded(!isTerminalExpanded);
    const toggleAIPanel = () => setIsAIPanelOpen(!isAIPanelOpen);
    
    const openCommandPalette = () => setIsCommandPaletteOpen(true);
    const closeCommandPalette = () => setIsCommandPaletteOpen(false);

    const openTaskDrawer = (task) => {
        setSelectedTask(task);
        setIsTaskDrawerOpen(true);
    };
    
    const closeTaskDrawer = () => {
        setIsTaskDrawerOpen(false);
        setTimeout(() => setSelectedTask(null), 300); // clear after animation
    };

    const openFile = (filename) => {
        if (!openTabs.find(tab => tab.id === filename)) {
            setOpenTabs([...openTabs, { id: filename, type: 'File' }]);
        }
        setActiveTab(filename);
    };

    const closeTab = (filename) => {
        const newTabs = openTabs.filter(tab => tab.id !== filename);
        setOpenTabs(newTabs);
        if (activeTab === filename && newTabs.length > 0) {
            setActiveTab(newTabs[newTabs.length - 1].id);
        } else if (newTabs.length === 0) {
            setActiveTab(null);
        }
    };

    const value = {
        isSidebarCollapsed, toggleSidebar,
        isCommandPaletteOpen, openCommandPalette, closeCommandPalette,
        isTerminalExpanded, toggleTerminal, setIsTerminalExpanded,
        activeTerminalTab, setActiveTerminalTab,
        isAIPanelOpen, toggleAIPanel,
        openTabs, activeTab, openFile, closeTab, setActiveTab,
        activeProject, setActiveProject,
        selectedTask, isTaskDrawerOpen, openTaskDrawer, closeTaskDrawer
    };

    return (
        <IDEContext.Provider value={value}>
            {children}
        </IDEContext.Provider>
    );
};
