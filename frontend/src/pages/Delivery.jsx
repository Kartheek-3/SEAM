import React from 'react';
import { useDelivery } from '../hooks/useData';
import { Rocket, CheckCircle2, Circle, AlertTriangle } from 'lucide-react';

const Delivery = () => {
    const { delivery, loading, error } = useDelivery();
    const isReady = delivery && delivery.status === 'READY';

    if (loading) return <div className="p-6 text-seam-text-muted">Loading delivery status...</div>;
    if (error) return <div className="p-6 text-seam-error">Backend unavailable: {error}</div>;
    if (!delivery) return <div className="p-6 text-seam-text-muted">No delivery status available.</div>;

    return (
        <div className="space-y-6 h-full flex flex-col p-6">
            <div className="shrink-0">
                <h1 className="text-2xl font-bold text-seam-text">DELIVERY GATE</h1>
                <p className="text-sm text-seam-text-muted mt-1">Final artifact packaging and release authorization</p>
            </div>

            <div className="flex-1 flex items-center justify-center">
                <div className="w-full max-w-3xl bg-seam-panel border border-seam-border rounded-xl shadow-2xl overflow-hidden flex flex-col md:flex-row">
                    
                    {/* Status Side */}
                    <div className={`p-8 md:w-2/5 flex flex-col items-center justify-center text-center border-b md:border-b-0 md:border-r border-seam-border relative overflow-hidden ${isReady ? 'bg-seam-success/5' : 'bg-seam-danger/5'}`}>
                        {/* Background glow */}
                        <div className={`absolute inset-0 opacity-20 ${isReady ? 'bg-[radial-gradient(circle_at_center,_var(--color-seam-success)_0%,_transparent_70%)]' : 'bg-[radial-gradient(circle_at_center,_var(--color-seam-danger)_0%,_transparent_70%)]'}`}></div>
                        
                        <div className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center mb-6 border-2 ${isReady ? 'bg-seam-panel border-seam-success text-seam-success shadow-[0_0_30px_rgba(16,185,129,0.3)]' : 'bg-seam-panel border-seam-danger text-seam-danger shadow-[0_0_30px_rgba(239,68,68,0.3)]'}`}>
                            <Rocket className="w-10 h-10" />
                        </div>
                        
                        <h2 className={`relative z-10 text-3xl font-black tracking-tight ${isReady ? 'text-seam-success' : 'text-seam-danger'}`}>
                            {delivery.status}
                        </h2>
                        
                        <p className="relative z-10 text-sm text-seam-text-muted mt-4 font-medium">
                            {isReady ? 'All gates passed. Ready for packaging.' : 'Delivery is blocked by pending or failed gates.'}
                        </p>
                    </div>

                    {/* Details Side */}
                    <div className="p-8 md:w-3/5 flex flex-col bg-seam-bg">
                        <h3 className="text-lg font-bold text-seam-text mb-6">Delivery Checklist</h3>
                        
                        <div className="space-y-4 flex-1">
                            <div className="flex items-center justify-between p-3 bg-seam-panel rounded-lg border border-seam-border">
                                <div className="flex items-center gap-3">
                                    <CheckCircle2 className="w-5 h-5 text-seam-success" />
                                    <span className="text-sm font-medium text-seam-text">Analysis</span>
                                </div>
                            </div>
                            
                            <div className="flex items-center justify-between p-3 bg-seam-panel rounded-lg border border-seam-border">
                                <div className="flex items-center gap-3">
                                    <CheckCircle2 className="w-5 h-5 text-seam-success" />
                                    <span className="text-sm font-medium text-seam-text">Planning</span>
                                </div>
                            </div>
                            
                            <div className="flex items-center justify-between p-3 bg-seam-panel rounded-lg border border-seam-border">
                                <div className="flex items-center gap-3">
                                    <CheckCircle2 className="w-5 h-5 text-seam-success" />
                                    <span className="text-sm font-medium text-seam-text">Coding</span>
                                </div>
                            </div>
                            
                            <div className={`flex items-center justify-between p-3 bg-seam-panel rounded-lg border ${isReady ? 'border-seam-border' : 'border-seam-danger/50 bg-seam-danger/5'}`}>
                                <div className="flex items-center gap-3">
                                    {isReady ? (
                                        <CheckCircle2 className="w-5 h-5 text-seam-success" />
                                    ) : (
                                        <AlertTriangle className="w-5 h-5 text-seam-danger" />
                                    )}
                                    <span className="text-sm font-medium text-seam-text">QA Gate</span>
                                </div>
                                <span className={`text-sm font-bold ${isReady ? 'text-seam-success' : 'text-seam-danger'}`}>
                                    {delivery.passed || 0} / {delivery.required || 0} Passed
                                </span>
                            </div>
                            
                            <div className="flex items-center justify-between p-3 bg-seam-panel rounded-lg border border-seam-border opacity-50">
                                <div className="flex items-center gap-3">
                                    <Circle className="w-5 h-5 text-seam-text-muted" />
                                    <span className="text-sm font-medium text-seam-text">Delivery Execution</span>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-seam-border">
                            <button 
                                disabled={!isReady}
                                className={`w-full py-3 rounded-lg font-bold text-sm transition-all flex items-center justify-center gap-2 ${
                                    isReady 
                                        ? 'bg-seam-accent hover:bg-blue-600 text-white shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:shadow-[0_0_20px_rgba(59,130,246,0.5)]' 
                                        : 'bg-seam-panel text-seam-text-muted border border-seam-border cursor-not-allowed opacity-50'
                                }`}
                            >
                                <Rocket className="w-4 h-4" />
                                EXECUTE DELIVERY
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Delivery;
