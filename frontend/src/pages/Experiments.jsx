import React from 'react';
import { useNavigate } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge';
import { useExperiments } from '../hooks/useData';
import { Play, Filter, Download } from 'lucide-react';

const Experiments = () => {
    const { experiments, loading, error } = useExperiments();
    const navigate = useNavigate();

    if (loading) return <div className="p-6 text-seam-text-muted">Loading experiments...</div>;
    if (error) return <div className="p-6 text-seam-error">Backend unavailable: {error}</div>;
    if (!experiments || experiments.length === 0) return <div className="p-6 text-seam-text-muted">No experiments found.</div>;

    return (
        <div className="space-y-6 h-full flex flex-col p-6">
            <div className="flex justify-between items-center shrink-0">
                <div>
                    <h1 className="text-2xl font-bold text-seam-text">EXPERIMENTS</h1>
                    <p className="text-sm text-seam-text-muted mt-1">Experiment observability and telemetry</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-3 py-1.5 border border-seam-border hover:bg-seam-border/50 text-seam-text-muted hover:text-seam-text text-sm font-medium rounded-lg transition-colors">
                        <Filter className="w-4 h-4" />
                        Filters
                    </button>
                    <button className="flex items-center gap-2 px-3 py-1.5 border border-seam-border hover:bg-seam-border/50 text-seam-text-muted hover:text-seam-text text-sm font-medium rounded-lg transition-colors">
                        <Download className="w-4 h-4" />
                        Export
                    </button>
                    <button className="flex items-center gap-2 px-4 py-1.5 bg-seam-accent hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors">
                        <Play className="w-4 h-4" />
                        New Run
                    </button>
                </div>
            </div>

            <div className="bg-seam-panel border border-seam-border rounded-xl flex-1 flex flex-col min-h-0 overflow-hidden shadow-sm">
                <div className="overflow-auto flex-1">
                    <table className="w-full text-left border-collapse">
                        <thead className="sticky top-0 bg-seam-panel border-b border-seam-border z-10 shadow-sm">
                            <tr>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Experiment</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Scenario</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Model</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Mode</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Duration</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">LLM Calls</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Tasks</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-seam-border">
                            {experiments.map((exp) => (
                                <tr 
                                    key={exp.id} 
                                    onClick={() => navigate(`/experiments/${exp.id.replace('#', '')}`)}
                                    className="hover:bg-seam-bg/30 transition-colors cursor-pointer group"
                                >
                                    <td className="p-4 text-sm font-bold text-seam-text group-hover:text-seam-accent transition-colors">{exp.id}</td>
                                    <td className="p-4 text-sm text-seam-text-muted">{exp.scenario}</td>
                                    <td className="p-4 text-sm text-seam-text-muted"><span className="font-mono bg-seam-bg px-1.5 py-0.5 rounded">{exp.model}</span></td>
                                    <td className="p-4 text-sm text-seam-text-muted">{exp.mode}</td>
                                    <td className="p-4 text-sm text-seam-text-muted">{exp.duration}</td>
                                    <td className="p-4 text-sm text-seam-text-muted">{exp.llmCalls}</td>
                                    <td className="p-4 text-sm text-seam-text-muted">{exp.tasks}</td>
                                    <td className="p-4">
                                        <StatusBadge status={exp.status} />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Experiments;
