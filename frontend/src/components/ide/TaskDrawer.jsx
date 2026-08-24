import React from 'react';
import { X, Clock, User, CheckCircle2, Package, GitMerge } from 'lucide-react';
import { useIDE } from '../../context/IDEContext';
import StatusBadge from '../StatusBadge';

const TaskDrawer = () => {
    const { isTaskDrawerOpen, closeTaskDrawer, selectedTask, openFile } = useIDE();

    if (!isTaskDrawerOpen || !selectedTask) return null;

    return (
        <div className="fixed inset-0 z-40 flex justify-end">
            {/* Overlay */}
            <div 
                className="absolute inset-0 bg-black/20 backdrop-blur-sm transition-opacity" 
                onClick={closeTaskDrawer}
            />
            
            {/* Drawer */}
            <div className="w-[400px] max-w-[90vw] h-full bg-seam-panel border-l border-seam-border shadow-2xl relative flex flex-col z-50 transform transition-transform duration-300">
                
                {/* Header */}
                <div className="h-16 flex items-center justify-between px-6 border-b border-seam-border shrink-0 bg-seam-bg">
                    <div>
                        <span className="text-xs text-seam-text-muted font-mono">{selectedTask.id}</span>
                        <h2 className="text-lg font-semibold text-seam-text leading-tight">{selectedTask.title || 'Task Details'}</h2>
                    </div>
                    <button 
                        onClick={closeTaskDrawer}
                        className="p-2 text-seam-text-muted hover:text-seam-text hover:bg-seam-border/50 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-8">
                    
                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-seam-bg border border-seam-border p-3 rounded-xl">
                            <span className="text-[10px] uppercase font-semibold text-seam-text-muted block mb-1">Status</span>
                            <StatusBadge status={selectedTask.status} />
                        </div>
                        <div className="bg-seam-bg border border-seam-border p-3 rounded-xl">
                            <span className="text-[10px] uppercase font-semibold text-seam-text-muted block mb-1">Type</span>
                            <span className="text-sm font-medium text-seam-text">{selectedTask.type}</span>
                        </div>
                    </div>

                    {/* Details List */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between py-2 border-b border-seam-border/50">
                            <div className="flex items-center gap-2 text-seam-text-muted">
                                <User className="w-4 h-4" />
                                <span className="text-sm">Agent</span>
                            </div>
                            <span className="text-sm font-medium text-seam-text">{selectedTask.agent}</span>
                        </div>
                        <div className="flex items-center justify-between py-2 border-b border-seam-border/50">
                            <div className="flex items-center gap-2 text-seam-text-muted">
                                <Clock className="w-4 h-4" />
                                <span className="text-sm">Duration</span>
                            </div>
                            <span className="text-sm font-medium text-seam-text">{selectedTask.duration}</span>
                        </div>
                        <div className="flex items-center justify-between py-2 border-b border-seam-border/50">
                            <div className="flex items-center gap-2 text-seam-text-muted">
                                <GitMerge className="w-4 h-4" />
                                <span className="text-sm">Dependencies</span>
                            </div>
                            <span className="text-sm font-medium text-seam-text">{selectedTask.dependencies}</span>
                        </div>
                    </div>

                    {/* Artifacts */}
                    {selectedTask.artifacts && selectedTask.artifacts.length > 0 && (
                        <div>
                            <h3 className="text-sm font-semibold text-seam-text mb-3 flex items-center gap-2">
                                <Package className="w-4 h-4 text-seam-accent" />
                                Generated Artifacts
                            </h3>
                            <div className="space-y-2">
                                {selectedTask.artifacts.map((artifact, i) => (
                                    <button 
                                        key={i}
                                        onClick={() => openFile(artifact)}
                                        className="w-full flex items-center justify-between p-3 bg-seam-bg border border-seam-border rounded-lg hover:border-seam-accent/50 hover:bg-seam-accent/5 transition-colors group"
                                    >
                                        <span className="text-sm font-mono text-seam-text">{artifact}</span>
                                        <span className="text-xs text-seam-text-muted group-hover:text-seam-accent">Open in Editor →</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TaskDrawer;
