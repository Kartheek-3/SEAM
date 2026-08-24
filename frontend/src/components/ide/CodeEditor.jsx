import React from 'react';
import { X, Lock, CheckCircle2 } from 'lucide-react';
import { useIDE } from '../../context/IDEContext';
import { useArtifacts } from '../../hooks/useData';

const CodeEditor = () => {
    const { openTabs, activeTab, closeTab, setActiveTab } = useIDE();
    const { artifacts } = useArtifacts();

    const activeArtifact = artifacts.find(a => a.id === activeTab);

    if (openTabs.length === 0) {
        return (
            <div className="flex-1 bg-seam-bg flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 rounded-2xl bg-seam-panel border border-seam-border flex items-center justify-center mx-auto mb-4 shadow-sm">
                        <span className="text-2xl font-bold text-seam-accent">S</span>
                    </div>
                    <p className="text-seam-text-muted">Select a file to open</p>
                    <div className="mt-4 flex items-center justify-center gap-2 text-xs text-seam-text-muted">
                        <kbd className="px-1.5 py-0.5 rounded border border-seam-border bg-seam-panel">Ctrl</kbd>
                        <span>+</span>
                        <kbd className="px-1.5 py-0.5 rounded border border-seam-border bg-seam-panel">K</kbd>
                        <span>to open commands</span>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col min-w-0 bg-seam-bg">
            {/* Tabs */}
            <div className="flex items-end h-10 border-b border-seam-border bg-seam-panel overflow-x-auto no-scrollbar shrink-0">
                {openTabs.map((tab) => (
                    <div 
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 h-full px-4 border-r border-seam-border min-w-[120px] max-w-[200px] cursor-pointer group ${
                            activeTab === tab.id 
                                ? 'bg-seam-bg border-t-2 border-t-seam-accent text-seam-text' 
                                : 'bg-seam-panel text-seam-text-muted hover:bg-seam-bg/50'
                        }`}
                    >
                        <span className="truncate text-sm flex-1">{tab.id}</span>
                        <button 
                            onClick={(e) => { e.stopPropagation(); closeTab(tab.id); }}
                            className={`p-0.5 rounded hover:bg-seam-border/50 ${activeTab === tab.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
                        >
                            <X className="w-3.5 h-3.5" />
                        </button>
                    </div>
                ))}
            </div>

            {/* Editor Header */}
            {activeArtifact && (
                <div className="h-8 bg-seam-bg border-b border-seam-border flex items-center px-4 gap-4 text-xs shrink-0">
                    <span className="font-medium text-seam-text-muted">Agent: <span className="text-seam-accent">{activeArtifact.agent}</span></span>
                    <div className="h-3 w-px bg-seam-border"></div>
                    <span className="text-seam-text-muted truncate">Task: <span className="text-seam-text">{activeArtifact.task}</span></span>
                    <div className="flex-1"></div>
                    <div className="flex items-center gap-1.5 text-seam-success font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Generated
                    </div>
                    <div className="flex items-center gap-1.5 text-seam-text-muted bg-seam-panel px-2 py-0.5 rounded border border-seam-border">
                        <Lock className="w-3 h-3" />
                        Read Only
                    </div>
                </div>
            )}

            {/* Code Area */}
            <div className="flex-1 flex overflow-hidden relative">
                {/* Main Content */}
                <div className="flex-1 overflow-auto bg-seam-bg font-mono text-sm leading-relaxed p-4">
                    {activeArtifact ? (
                        <div className="flex">
                            {/* Line Numbers */}
                            <div className="w-8 text-right pr-4 text-seam-border select-none border-r border-seam-border shrink-0">
                                {activeArtifact.content.split('\n').map((_, i) => (
                                    <div key={i}>{i + 1}</div>
                                ))}
                            </div>
                            {/* Code */}
                            <div className="pl-4 text-seam-text whitespace-pre overflow-x-auto">
                                {activeArtifact.content}
                            </div>
                        </div>
                    ) : (
                        <div className="text-seam-text-muted">
                            // Source not available for {activeTab}
                        </div>
                    )}
                </div>
                
                {/* Visual Minimap Placeholder */}
                {activeArtifact && (
                    <div className="hidden lg:block w-16 bg-seam-panel border-l border-seam-border p-1 shrink-0">
                        <div className="w-full h-32 bg-seam-bg/50 rounded overflow-hidden">
                            {/* Fake lines */}
                            {Array(20).fill(0).map((_, i) => (
                                <div key={i} className={`h-0.5 mb-0.5 rounded-full bg-seam-text-muted/20 ${Math.random() > 0.5 ? 'w-full' : 'w-2/3'}`}></div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CodeEditor;
