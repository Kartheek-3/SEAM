import React from 'react';

const StatusBadge = ({ status }) => {
    const getStatusStyles = () => {
        switch (status?.toUpperCase()) {
            case 'SUCCESS':
            case 'PASS':
                return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
            case 'RUNNING':
            case 'ACTIVE':
                return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
            case 'FAILED':
            case 'FAIL':
                return 'bg-red-500/10 text-red-500 border-red-500/20';
            case 'PARTIAL_SUCCESS':
                return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
            case 'PENDING':
            default:
                return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
        }
    };

    return (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusStyles()}`}>
            {status}
        </span>
    );
};

export default StatusBadge;
