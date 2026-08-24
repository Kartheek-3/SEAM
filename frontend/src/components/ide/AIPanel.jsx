import React from 'react';
import { Bot, Send, Paperclip, ChevronRight, CheckCircle2, Circle, Loader2 } from 'lucide-react';
import { useIDE } from '../../context/IDEContext';
import { useLiveExperiment } from '../../hooks/useLiveExperiment';

const AIPanel = () => {
    const { isAIPanelOpen } = useIDE();
    const { liveState, isUnknown, loading } = useLiveExperiment('15');

    if (!isAIPanelOpen) return null;

    return (
        <div className="w-80 bg-seam-panel border-l border-seam-border flex flex-col h-full shrink-0 hidden md:flex">
            {/* Header */}
            <div className="h-12 border-b border-seam-border flex items-center justify-between px-4 shrink-0 bg-seam-bg">
                <div className="flex items-center gap-2">
                    <Bot className="w-5 h-5 text-seam-accent" />
                    <span className="font-semibold text-seam-text">SEAM AGENT</span>
                </div>
                <div className="flex items-center gap-1.5">
                    {isUnknown ? (
                        <>
                            <div className="w-2 h-2 rounded-full bg-seam-text-muted"></div>
                            <span className="text-[10px] uppercase font-bold text-seam-text-muted tracking-wider">Offline</span>
                        </>
                    ) : (
                        <>
                            <div className="w-2 h-2 rounded-full bg-seam-success animate-pulse"></div>
                            <span className="text-[10px] uppercase font-bold text-seam-success tracking-wider">Supervising</span>
                        </>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                
                {/* Current Agent/Task */}
                <div className="space-y-4">
                    <div>
                        <span className="text-[10px] font-semibold text-seam-text-muted uppercase tracking-wider block mb-1">Current Agent</span>
                        <div className="flex items-center gap-2 bg-seam-bg border border-seam-border rounded-lg p-2.5">
                            <div className="w-6 h-6 rounded bg-seam-accent/20 flex items-center justify-center">
                                <Loader2 className="w-4 h-4 text-seam-accent animate-spin" />
                            </div>
                            <span className="text-sm font-medium text-seam-text">
                                {isUnknown ? 'Unknown' : 'CodingAgent'}
                            </span>
                        </div>
                    </div>
                    
                    <div>
                        <span className="text-[10px] font-semibold text-seam-text-muted uppercase tracking-wider block mb-1">Current Task</span>
                        <p className="text-sm text-seam-text">{isUnknown ? 'Live monitoring unavailable' : 'Implement Product Service'}</p>
                    </div>

                    <div>
                        <div className="flex justify-between items-center mb-1">
                            <span className="text-[10px] font-semibold text-seam-text-muted uppercase tracking-wider">Progress</span>
                            <span className="text-[10px] font-bold text-seam-accent">82%</span>
                        </div>
                        <div className="w-full bg-seam-border rounded-full h-1.5 overflow-hidden">
                            <div className="bg-seam-accent h-1.5 rounded-full" style={{ width: '82%' }}></div>
                        </div>
                    </div>
                </div>

                {/* Dependencies */}
                <div>
                    <span className="text-[10px] font-semibold text-seam-text-muted uppercase tracking-wider block mb-2">Dependencies</span>
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                            <CheckCircle2 className="w-4 h-4 text-seam-success" />
                            <span className="text-seam-text-muted line-through">Product model</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                            <CheckCircle2 className="w-4 h-4 text-seam-success" />
                            <span className="text-seam-text-muted line-through">Database schema</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                            <Circle className="w-4 h-4 text-seam-text-muted" />
                            <span className="text-seam-text">QA</span>
                        </div>
                    </div>
                </div>

                {/* Recent Events */}
                <div>
                    <span className="text-[10px] font-semibold text-seam-text-muted uppercase tracking-wider block mb-2">Recent Events</span>
                    <div className="space-y-3 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-seam-border before:to-transparent">
                        <div className="relative flex items-start gap-3">
                            <div className="w-4 h-4 mt-0.5 rounded-full bg-seam-panel border border-seam-accent flex items-center justify-center shrink-0 z-10">
                                <div className="w-1.5 h-1.5 rounded-full bg-seam-accent"></div>
                            </div>
                            <div>
                                <p className="text-xs text-seam-text">CodingAgent generated product.py</p>
                                <span className="text-[10px] text-seam-text-muted">Just now</span>
                            </div>
                        </div>
                        <div className="relative flex items-start gap-3">
                            <div className="w-4 h-4 mt-0.5 rounded-full bg-seam-panel border border-seam-border flex items-center justify-center shrink-0 z-10"></div>
                            <div>
                                <p className="text-xs text-seam-text-muted">CodingAgent generated service.py</p>
                                <span className="text-[10px] text-seam-text-muted">2m ago</span>
                            </div>
                        </div>
                        <div className="relative flex items-start gap-3">
                            <div className="w-4 h-4 mt-0.5 rounded-full bg-seam-panel border border-seam-border flex items-center justify-center shrink-0 z-10"></div>
                            <div>
                                <p className="text-xs text-seam-text-muted">QA pending</p>
                                <span className="text-[10px] text-seam-text-muted">queued</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Chat Input */}
            <div className="p-4 border-t border-seam-border bg-seam-bg">
                <div className="bg-seam-panel border border-seam-border rounded-xl focus-within:border-seam-accent transition-colors flex flex-col p-2">
                    <textarea 
                        rows="2" 
                        placeholder="Ask SEAM about this project..."
                        className="w-full bg-transparent text-sm text-seam-text resize-none outline-none placeholder:text-seam-text-muted"
                    ></textarea>
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-seam-border/50">
                        <button className="text-seam-text-muted hover:text-seam-text p-1 transition-colors">
                            <Paperclip className="w-4 h-4" />
                        </button>
                        <button className="bg-seam-accent hover:bg-blue-600 text-white p-1.5 rounded-lg transition-colors">
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AIPanel;
