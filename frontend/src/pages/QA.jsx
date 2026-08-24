import React from 'react';
import { useQA } from '../hooks/useData';
import StatusBadge from '../components/StatusBadge';
import { ShieldCheck, AlertOctagon, AlertTriangle, Info } from 'lucide-react';
import { useIDE } from '../context/IDEContext';

const QA = () => {
    const { openFile } = useIDE();
    const { overview, tasks, loading, error } = useQA();

    const getSeverityIcon = (severity) => {
        switch (severity) {
            case 'CRITICAL': return <AlertOctagon className="w-4 h-4 text-seam-danger" />;
            case 'MAJOR': return <AlertTriangle className="w-4 h-4 text-seam-warning" />;
            case 'MINOR': return <Info className="w-4 h-4 text-seam-accent" />;
            default: return <Info className="w-4 h-4 text-seam-text-muted" />;
        }
    };

    const getSeverityClass = (severity) => {
        switch (severity) {
            case 'CRITICAL': return 'bg-seam-danger/10 border-seam-danger/30';
            case 'MAJOR': return 'bg-seam-warning/10 border-seam-warning/30';
            case 'MINOR': return 'bg-seam-accent/10 border-seam-accent/30';
            default: return 'bg-seam-panel border-seam-border';
        }
    };

    return (
        <div className="space-y-6 h-full flex flex-col p-6 overflow-hidden">
            <div className="flex justify-between items-center shrink-0">
                <div>
                    <h1 className="text-2xl font-bold text-seam-text flex items-center gap-3">
                        QA GATE
                        {overview && <StatusBadge status={overview.failed > 0 ? 'FAIL' : (overview.pending > 0 ? 'PENDING' : 'PASS')} />}
                    </h1>
                    <p className="text-sm text-seam-text-muted mt-1">Autonomous evaluation and defect tracking</p>
                </div>
            </div>

            {loading && <div className="text-seam-text-muted">Loading QA data...</div>}
            {error && <div className="text-seam-error">Backend unavailable: {error}</div>}
            {!loading && !error && !overview && <div className="text-seam-text-muted">No QA data available.</div>}

            {/* QA Overview Cards */}
            {!loading && !error && overview && (
            <>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 shrink-0">
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <span className="text-xs text-seam-text-muted font-medium uppercase">Total Tasks</span>
                    <p className="text-2xl font-bold text-seam-text mt-1">{overview.total}</p>
                </div>
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <span className="text-xs text-seam-success font-medium uppercase">Passed</span>
                    <p className="text-2xl font-bold text-seam-text mt-1">{overview.passed}</p>
                </div>
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <span className="text-xs text-seam-danger font-medium uppercase">Failed</span>
                    <p className="text-2xl font-bold text-seam-text mt-1">{overview.failed}</p>
                </div>
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <span className="text-xs text-seam-warning font-medium uppercase">Reworked</span>
                    <p className="text-2xl font-bold text-seam-text mt-1">{overview.reworked}</p>
                </div>
                <div className="bg-seam-panel border border-seam-border rounded-xl p-4">
                    <span className="text-xs text-seam-text-muted font-medium uppercase">Pending</span>
                    <p className="text-2xl font-bold text-seam-text mt-1">{overview.pending}</p>
                </div>
            </div>

            {/* QA Task List */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {tasks.map((qaTask) => (
                    <div key={qaTask.id} className={`bg-seam-panel border rounded-xl p-5 shadow-sm transition-colors ${qaTask.verdict === 'FAIL' ? 'border-seam-danger/50' : 'border-seam-border'}`}>
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-md font-semibold text-seam-text flex items-center gap-2">
                                    <ShieldCheck className="w-5 h-5 text-seam-text-muted" />
                                    {qaTask.id}
                                </h3>
                                <button 
                                    onClick={() => openFile(qaTask.target)}
                                    className="text-sm text-seam-text-muted hover:text-seam-accent transition-colors mt-1 font-mono"
                                >
                                    Target: {qaTask.target}
                                </button>
                            </div>
                            <StatusBadge status={qaTask.verdict} />
                        </div>
                        
                        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 py-4 border-y border-seam-border/50 mb-4">
                            <div>
                                <span className="block text-[10px] uppercase font-semibold text-seam-text-muted mb-1">Tests Passed</span>
                                <span className="text-sm font-bold text-seam-success">{qaTask.passed}</span>
                            </div>
                            <div>
                                <span className="block text-[10px] uppercase font-semibold text-seam-text-muted mb-1">Tests Failed</span>
                                <span className="text-sm font-bold text-seam-danger">{qaTask.failed}</span>
                            </div>
                            <div>
                                <span className="block text-[10px] uppercase font-semibold text-seam-text-muted mb-1">Critical</span>
                                <span className="text-sm font-bold text-seam-danger">{qaTask.critical}</span>
                            </div>
                            <div>
                                <span className="block text-[10px] uppercase font-semibold text-seam-text-muted mb-1">Major</span>
                                <span className="text-sm font-bold text-seam-warning">{qaTask.major}</span>
                            </div>
                            <div>
                                <span className="block text-[10px] uppercase font-semibold text-seam-text-muted mb-1">Minor</span>
                                <span className="text-sm font-bold text-seam-accent">{qaTask.minor}</span>
                            </div>
                        </div>

                        {/* Findings */}
                        {qaTask.findings.length > 0 && (
                            <div className="space-y-2">
                                <h4 className="text-xs font-semibold text-seam-text-muted uppercase tracking-wider mb-3">Findings</h4>
                                {qaTask.findings.map((finding, i) => (
                                    <div key={i} className={`p-3 rounded-lg border ${getSeverityClass(finding.severity)}`}>
                                        <div className="flex items-start gap-3">
                                            <div className="mt-0.5">{getSeverityIcon(finding.severity)}</div>
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className={`text-[10px] font-bold uppercase tracking-wider ${
                                                        finding.severity === 'CRITICAL' ? 'text-seam-danger' :
                                                        finding.severity === 'MAJOR' ? 'text-seam-warning' : 'text-seam-accent'
                                                    }`}>{finding.severity}</span>
                                                    <span className="text-xs font-mono text-seam-text-muted border-l border-seam-border/50 pl-2">
                                                        {finding.file}:{finding.line}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-seam-text font-medium">{finding.description}</p>
                                                <p className="text-xs text-seam-text-muted mt-1">Recommendation: {finding.recommendation}</p>
                                            </div>
                                            <button 
                                                onClick={() => openFile(finding.file)}
                                                className="text-xs font-medium bg-seam-bg border border-seam-border hover:border-seam-accent text-seam-text-muted hover:text-seam-accent px-2 py-1 rounded transition-colors"
                                            >
                                                Open File
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
            </>
            )}
        </div>
    );
};

export default QA;
