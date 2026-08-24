import React, { useState } from 'react';
import { ChevronRight, ChevronDown, File, Folder as FolderIcon } from 'lucide-react';
import { useIDE } from '../../context/IDEContext';
import { useProjects } from '../../hooks/useData';
import { useLiveExperiment } from '../../hooks/useLiveExperiment';

const FileNode = ({ node, level = 0 }) => {
    const [isOpen, setIsOpen] = useState(true);
    const { activeTab, openFile } = useIDE();

    const isFolder = node.type === 'folder';
    const isFile = node.type === 'file';
    const isPython = isFile && node.name.endsWith('.py');
    const isMarkdown = isFile && node.name.endsWith('.md');
    const isJson = isFile && node.name.endsWith('.json');

    const handleClick = () => {
        if (isFolder) {
            setIsOpen(!isOpen);
        } else {
            openFile(node.name);
        }
    };

    const getFileColor = () => {
        if (isPython) return 'text-blue-400';
        if (isJson) return 'text-amber-400';
        if (isMarkdown) return 'text-emerald-400';
        return 'text-seam-text-muted';
    };

    return (
        <div className="select-none">
            <div 
                className={`flex items-center gap-1.5 py-1 px-2 cursor-pointer text-sm transition-colors
                    ${activeTab === node.name ? 'bg-seam-accent/20 text-seam-accent' : 'text-seam-text-muted hover:bg-seam-border/50 hover:text-seam-text'}
                `}
                style={{ paddingLeft: `${level * 12 + 8}px` }}
                onClick={handleClick}
            >
                {isFolder ? (
                    <span className="text-seam-text-muted">
                        {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    </span>
                ) : (
                    <span className="w-3.5 h-3.5 flex-shrink-0" /> // spacer
                )}
                
                {isFolder ? (
                    <FolderIcon className={`w-4 h-4 ${isOpen ? 'text-seam-accent' : 'text-seam-text-muted'}`} />
                ) : (
                    <File className={`w-4 h-4 ${getFileColor()}`} />
                )}
                <span className="truncate">{node.name}</span>
            </div>
            
            {isFolder && isOpen && node.children && (
                <div>
                    {node.children.map((child, i) => (
                        <FileNode key={i} node={child} level={level + 1} />
                    ))}
                </div>
            )}
        </div>
    );
};

const ProjectExplorer = () => {
    const { projects } = useProjects();
    const { liveState, isUnknown } = useLiveExperiment('15');
    const activeProject = projects[0];

    return (
        <div className="w-64 bg-seam-panel border-r border-seam-border flex flex-col h-full hidden lg:flex shrink-0">
            <div className="p-4 border-b border-seam-border bg-seam-bg shrink-0">
                <span className="text-[10px] font-semibold text-seam-text-muted uppercase tracking-wider block mb-1">Current Experiment</span>
                <div className="text-sm font-bold text-seam-text mb-2">Experiment #15</div>
                
                <span className="text-[10px] font-semibold text-seam-text-muted uppercase tracking-wider block mb-1">Status</span>
                <div className="flex items-center gap-2 mb-2">
                    {isUnknown ? (
                        <>
                            <div className="w-2 h-2 rounded-full bg-seam-text-muted"></div>
                            <span className="text-xs font-semibold text-seam-text-muted uppercase">OFFLINE</span>
                        </>
                    ) : (
                        <>
                            <div className="w-2 h-2 rounded-full bg-seam-accent animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
                            <span className="text-xs font-bold text-seam-accent uppercase">● RUNNING</span>
                        </>
                    )}
                </div>
            </div>
            <div className="p-3 text-xs font-semibold text-seam-text-muted uppercase tracking-wider border-b border-seam-border shrink-0">
                Explorer
            </div>
            <div className="flex-1 overflow-y-auto py-2">
                {activeProject?.tree?.map((node, i) => (
                    <FileNode key={i} node={node} />
                ))}
            </div>
        </div>
    );
};

export default ProjectExplorer;
