import React from 'react';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';

const PipelineStage = ({ stage, isLast }) => {
    const getIcon = () => {
        switch (stage.status?.toUpperCase()) {
            case 'SUCCESS':
                return <CheckCircle2 className="w-6 h-6 text-seam-success" />;
            case 'RUNNING':
                return <Loader2 className="w-6 h-6 text-seam-accent animate-spin" />;
            case 'FAILED':
                return <XCircle className="w-6 h-6 text-seam-danger" />;
            case 'PENDING':
            default:
                return <Circle className="w-6 h-6 text-seam-text-muted" />;
        }
    };

    const getBorderColor = () => {
        if (stage.status === 'SUCCESS') return 'border-seam-success';
        if (stage.status === 'RUNNING') return 'border-seam-accent';
        if (stage.status === 'FAILED') return 'border-seam-danger';
        return 'border-seam-border';
    };

    return (
        <div className="flex flex-col md:flex-row items-center relative">
            <div className={`flex flex-col items-center justify-center w-32 h-24 bg-seam-panel border-2 rounded-xl z-10 transition-colors ${getBorderColor()}`}>
                <div className="mb-2">{getIcon()}</div>
                <span className="text-sm font-semibold text-seam-text">{stage.name}</span>
                <span className="text-[10px] text-seam-text-muted text-center px-1 mt-0.5 leading-tight">{stage.description}</span>
            </div>
            
            {/* Horizontal Line for Desktop */}
            {!isLast && (
                <div className="hidden md:block w-8 lg:w-12 h-0.5 bg-seam-border relative">
                    {stage.id === 'qa' && (
                        /* Simulated Rework loop line */
                        <svg className="absolute -top-12 -left-32 w-48 h-12 text-seam-border" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M 12 12 Q 12 0 48 0 L 140 0 Q 180 0 180 12" strokeDasharray="4 4" />
                            <text x="75" y="-5" className="text-[10px] fill-seam-text-muted">Rework Loop</text>
                        </svg>
                    )}
                </div>
            )}
            
            {/* Vertical Line for Mobile */}
            {!isLast && (
                <div className="md:hidden h-8 w-0.5 bg-seam-border"></div>
            )}
        </div>
    );
};

export default PipelineStage;
