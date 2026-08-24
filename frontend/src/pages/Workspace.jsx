import React from 'react';
import ProjectExplorer from '../components/ide/ProjectExplorer';
import CodeEditor from '../components/ide/CodeEditor';
import AIPanel from '../components/ide/AIPanel';
import BottomTerminal from '../components/ide/BottomTerminal';
import TaskDrawer from '../components/ide/TaskDrawer';

const Workspace = () => {
    return (
        <div className="flex-1 flex flex-col h-full w-full overflow-hidden">
            {/* Main Editor Area */}
            <div className="flex-1 flex overflow-hidden">
                <ProjectExplorer />
                <CodeEditor />
                <AIPanel />
            </div>
            
            {/* Bottom Terminal */}
            <BottomTerminal />
            
            {/* Task Drawer */}
            <TaskDrawer />
        </div>
    );
};

export default Workspace;
