import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, Activity, Target, MessageSquareCode } from 'lucide-react';
import { useExperiment } from '../hooks/useData';
import { useLiveExperiment } from '../hooks/useLiveExperiment';
import StatusBadge from '../components/StatusBadge';
import PipelineStage from '../components/PipelineStage';

const ExperimentDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { experiment: exp, loading, error } = useExperiment(id);
    const { liveState, isUnknown: isLiveUnknown } = useLiveExperiment(id);
    
    if (loading && !liveState) return <div className="p-6 text-seam-text-muted">Loading experiment...</div>;
    if (error && !liveState) return <div className="p-6 text-seam-error">Backend unavailable: {error}</div>;
    if (!exp && !liveState) return <div className="p-6 text-seam-text-muted">Experiment not found.</div>;

    const displayExp = exp || liveState;
    const isRunning = liveState && liveState.status === 'running';

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto w-full h-full flex flex-col overflow-y-auto">
            {/* Header */}
            <div className="flex items-center gap-4 shrink-0">
                <button 
                    onClick={() => navigate('/experiments')}
                    className="p-2 bg-seam-panel border border-seam-border rounded-lg hover:bg-seam-border/50 text-seam-text-muted hover:text-seam-text transition-colors"
                >
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold text-seam-text flex items-center gap-3">
                        REAL Experiment {displayExp.id || displayExp.experiment_id}
                        {isRunning ? (
                            <span className="px-2 py-0.5 rounded text-xs font-bold bg-seam-accent text-white animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.5)]">● LIVE</span>
                        ) : (
                            <StatusBadge status={displayExp.status} />
                        )}
                    </h1>
                </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 shrink-0">
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2 text-seam-text-muted">
                        <span className="text-xs font-semibold uppercase tracking-wider">Scenario</span>
                        <Target className="w-4 h-4" />
                    </div>
                    <p className="text-sm font-semibold text-seam-text truncate">{exp.scenario}</p>
                </div>
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2 text-seam-text-muted">
                        <span className="text-xs font-semibold uppercase tracking-wider">Model</span>
                        <MessageSquareCode className="w-4 h-4" />
                    </div>
                    <p className="text-sm font-semibold text-seam-text font-mono">{exp.model}</p>
                </div>
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2 text-seam-text-muted">
                        <span className="text-xs font-semibold uppercase tracking-wider">Mode</span>
                    </div>
                    <p className="text-sm font-semibold text-seam-text font-mono text-seam-accent">{exp.mode}</p>
                </div>
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2 text-seam-text-muted">
                        <span className="text-xs font-semibold uppercase tracking-wider">Duration</span>
                        <Clock className="w-4 h-4" />
                    </div>
                    <p className="text-sm font-semibold text-seam-text">{exp.duration}</p>
                </div>
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2 text-seam-text-muted">
                        <span className="text-xs font-semibold uppercase tracking-wider">LLM Calls</span>
                        <Activity className="w-4 h-4" />
                    </div>
                    <p className="text-sm font-semibold text-seam-text">{displayExp.llmCalls || '-'}</p>
                </div>
            </div>

            {/* Timeline View */}
            <div className="bg-seam-panel border border-seam-border rounded-xl p-6 shadow-sm flex-1">
                <h2 className="text-lg font-semibold text-seam-text mb-8">Execution Timeline</h2>
                
                <div className="flex flex-col md:flex-row items-center justify-start min-w-max py-4 px-2 overflow-x-auto">
                    {displayExp.stages && (Array.isArray(displayExp.stages) ? displayExp.stages : Object.entries(displayExp.stages).map(([k,v])=>({name: k, status: v?.status || 'PENDING', duration: '-'}))).map((stage, index, arr) => (
                        <div key={index} className="flex flex-col md:flex-row items-center relative group cursor-pointer">
                            <div className="flex flex-col items-center justify-center w-32 h-24 bg-seam-bg border-2 border-seam-border rounded-xl z-10 transition-colors hover:border-seam-accent">
                                <StatusBadge status={stage.status} />
                                <span className="text-sm font-semibold text-seam-text mt-2 capitalize">{stage.name}</span>
                                <span className="text-[10px] text-seam-text-muted mt-1 font-mono">{stage.duration}</span>
                            </div>
                            
                            {/* Horizontal Line for Desktop */}
                            {index !== arr.length - 1 && (
                                <div className="hidden md:block w-8 lg:w-12 h-0.5 bg-seam-border relative"></div>
                            )}
                            
                            {/* Vertical Line for Mobile */}
                            {index !== arr.length - 1 && (
                                <div className="md:hidden h-8 w-0.5 bg-seam-border"></div>
                            )}
                        </div>
                    ))}
                </div>
                
                <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="h-48 border border-seam-border bg-seam-bg rounded-lg flex items-center justify-center">
                        <span className="text-seam-text-muted">Stage Duration Chart Placeholder</span>
                    </div>
                    <div className="h-48 border border-seam-border bg-seam-bg rounded-lg flex items-center justify-center">
                        <span className="text-seam-text-muted">LLM Calls By Agent Chart Placeholder</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ExperimentDetail;
