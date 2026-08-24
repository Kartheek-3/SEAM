import React from 'react';
import { useNavigate } from 'react-router-dom';
import StatusBadge from './StatusBadge';
import { demoExperiments } from '../data/mockData';

const RecentExperiment = () => {
    const navigate = useNavigate();
    const latest = demoExperiments[0]; // Get the first one as latest

    return (
        <div className="bg-seam-panel border border-seam-border rounded-xl p-6 shadow-sm h-full flex flex-col">
            <h2 className="text-lg font-semibold text-seam-text mb-4">Latest Experiment</h2>
            
            <div className="flex-1 space-y-4">
                <div>
                    <span className="text-xs text-seam-text-muted font-medium uppercase tracking-wider">Experiment ID</span>
                    <p className="text-2xl font-bold text-seam-text mt-1">{latest.id}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <span className="text-xs text-seam-text-muted font-medium uppercase tracking-wider">Scenario</span>
                        <p className="text-sm text-seam-text font-medium mt-1">{latest.scenario}</p>
                    </div>
                    <div>
                        <span className="text-xs text-seam-text-muted font-medium uppercase tracking-wider">Model</span>
                        <p className="text-sm text-seam-text font-medium mt-1">{latest.model}</p>
                    </div>
                    <div>
                        <span className="text-xs text-seam-text-muted font-medium uppercase tracking-wider">Mode</span>
                        <p className="text-sm text-seam-text font-medium mt-1">{latest.mode}</p>
                    </div>
                    <div>
                        <span className="text-xs text-seam-text-muted font-medium uppercase tracking-wider">Status</span>
                        <div className="mt-1">
                            <StatusBadge status={latest.status} />
                        </div>
                    </div>
                </div>
                
                {/* Simulated detailed stages */}
                <div className="pt-4 border-t border-seam-border">
                    <span className="text-xs text-seam-text-muted font-medium uppercase tracking-wider mb-2 block">Stages</span>
                    <div className="space-y-2">
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-seam-text">Analysis</span>
                            <span className="text-seam-success">✓</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-seam-text">Planning</span>
                            <span className="text-seam-success">✓</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-seam-text">Coding</span>
                            <span className="text-seam-accent animate-pulse">●</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-seam-text-muted">QA</span>
                            <span className="text-seam-text-muted">○</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-seam-text-muted">Delivery</span>
                            <span className="text-seam-text-muted">○</span>
                        </div>
                    </div>
                </div>
            </div>

            <button 
                onClick={() => navigate('/experiments')}
                className="mt-6 w-full py-2 bg-seam-border/30 hover:bg-seam-border/60 text-seam-text text-sm font-medium rounded-lg transition-colors border border-seam-border"
            >
                View Experiment
            </button>
        </div>
    );
};

export default RecentExperiment;
