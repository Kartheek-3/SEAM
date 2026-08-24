import React from 'react';
import { Terminal, ScrollText, Activity, AlertTriangle, ShieldCheck, X, ChevronUp, ChevronDown } from 'lucide-react';
import { useIDE } from '../../context/IDEContext';
import { useLiveExperiment } from '../../hooks/useLiveExperiment';

const BottomTerminal = () => {
    const { isTerminalExpanded, toggleTerminal, activeTerminalTab, setActiveTerminalTab } = useIDE();
    const { events, isUnknown } = useLiveExperiment('15');

    const tabs = [
        { id: 'Terminal', icon: Terminal },
        { id: 'Logs', icon: ScrollText },
        { id: 'Events', icon: Activity },
        { id: 'Problems', icon: AlertTriangle, badge: '2' },
        { id: 'QA', icon: ShieldCheck },
    ];

    return (
        <div className={`bg-seam-panel border-t border-seam-border flex flex-col transition-all duration-300 shrink-0 z-10 ${isTerminalExpanded ? 'h-64' : 'h-10'}`}>
            {/* Header / Tabs */}
            <div className="h-10 flex items-center justify-between px-2 bg-seam-bg border-b border-seam-border">
                <div className="flex items-center h-full gap-1">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => {
                                setActiveTerminalTab(tab.id);
                                if (!isTerminalExpanded) toggleTerminal();
                            }}
                            className={`flex items-center gap-1.5 px-3 h-full text-xs font-medium transition-colors border-b-2 ${
                                activeTerminalTab === tab.id && isTerminalExpanded
                                    ? 'text-seam-text border-seam-accent bg-seam-panel'
                                    : 'text-seam-text-muted border-transparent hover:text-seam-text hover:bg-seam-panel/50'
                            }`}
                        >
                            <tab.icon className="w-3.5 h-3.5" />
                            {tab.id}
                            {tab.badge && (
                                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-seam-accent/20 text-seam-accent text-[9px] font-bold">
                                    {tab.badge}
                                </span>
                            )}
                        </button>
                    ))}
                </div>
                
                <div className="flex items-center gap-2 pr-2">
                    <button onClick={toggleTerminal} className="text-seam-text-muted hover:text-seam-text p-1 transition-colors">
                        {isTerminalExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
                    </button>
                </div>
            </div>

            {/* Content Area */}
            {isTerminalExpanded && (
                <div className="flex-1 overflow-auto bg-seam-panel font-mono text-sm p-4 text-seam-text-muted">
                    {activeTerminalTab === 'Terminal' && (
                        <div className="space-y-1">
                            <div className="text-seam-text font-bold"><span className="text-seam-accent">$</span> seam supervisor</div>
                            {isUnknown ? (
                                <div className="text-seam-text-muted mt-2">Live event stream unavailable</div>
                            ) : events && events.length > 0 ? (
                                events.map((ev, i) => (
                                    <div key={i}>[{new Date().toLocaleTimeString()}] {ev.message}</div>
                                ))
                            ) : (
                                <>
                                    <div>[20:31:04] <span className="text-seam-success">Analysis completed</span></div>
                                    <div>[20:32:19] ProjectPlan assembled</div>
                                    <div>[20:34:08] CodingAgent started</div>
                                    <div>[20:35:42] Artifact generated</div>
                                    <div>[20:36:10] <span className="text-seam-warning">QA pending</span></div>
                                </>
                            )}
                            {!isUnknown && <div className="mt-2 text-seam-text"><span className="text-seam-accent animate-pulse">_</span></div>}
                        </div>
                    )}
                    
                    {activeTerminalTab === 'Problems' && (
                        <div className="font-sans space-y-4">
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="w-4 h-4 text-seam-warning mt-0.5" />
                                <div>
                                    <h4 className="text-seam-text text-sm font-medium">ProductService missing test coverage</h4>
                                    <p className="text-xs text-seam-text-muted mt-1">tests/test_products.py</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="w-4 h-4 text-seam-warning mt-0.5" />
                                <div>
                                    <h4 className="text-seam-text text-sm font-medium">Database connection configuration pending</h4>
                                    <p className="text-xs text-seam-text-muted mt-1">config/settings.json</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTerminalTab !== 'Terminal' && activeTerminalTab !== 'Problems' && (
                        <div className="flex items-center justify-center h-full text-seam-text-muted opacity-50">
                            {activeTerminalTab} data unavailable in demo mode.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default BottomTerminal;
