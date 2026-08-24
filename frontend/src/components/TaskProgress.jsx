import React from 'react';

const TaskProgress = () => {
    return (
        <div className="bg-seam-panel border border-seam-border rounded-xl p-6 shadow-sm h-full flex flex-col">
            <h2 className="text-lg font-semibold text-seam-text mb-6">Task Progress</h2>
            
            <div className="space-y-6 flex-1">
                {/* Coding Progress */}
                <div>
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-seam-text">Coding Tasks</span>
                        <span className="text-sm font-medium text-seam-text-muted">11 / 11</span>
                    </div>
                    <div className="w-full bg-seam-border/50 rounded-full h-2.5 overflow-hidden">
                        <div className="bg-seam-success h-2.5 rounded-full" style={{ width: '100%' }}></div>
                    </div>
                    <p className="text-xs text-seam-text-muted mt-1.5 text-right">100%</p>
                </div>

                {/* QA Progress */}
                <div>
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-seam-text">QA Tasks</span>
                        <span className="text-sm font-medium text-seam-text-muted">0 / 11</span>
                    </div>
                    <div className="w-full bg-seam-border/50 rounded-full h-2.5 overflow-hidden">
                        <div className="bg-seam-accent h-2.5 rounded-full animate-pulse" style={{ width: '10%' }}></div>
                    </div>
                    <p className="text-xs text-seam-text-muted mt-1.5 text-right">0%</p>
                </div>

                {/* Delivery Progress */}
                <div>
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-seam-text">Delivery</span>
                        <span className="text-xs font-medium px-2 py-0.5 rounded bg-slate-500/10 text-slate-400">Pending</span>
                    </div>
                    <div className="w-full bg-seam-border/50 rounded-full h-2.5 overflow-hidden">
                        <div className="bg-seam-border h-2.5 rounded-full" style={{ width: '0%' }}></div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TaskProgress;
