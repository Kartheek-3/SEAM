import React from 'react';

const MetricCard = ({ title, value, icon: Icon, trend }) => {
    return (
        <div className="bg-seam-panel border border-seam-border rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-seam-text-muted">{title}</h3>
                {Icon && <Icon className="w-5 h-5 text-seam-accent" />}
            </div>
            <div className="flex items-end justify-between">
                <span className="text-3xl font-bold text-seam-text">{value}</span>
                {trend && (
                    <span className="text-xs font-medium text-seam-success">
                        {trend}
                    </span>
                )}
            </div>
        </div>
    );
};

export default MetricCard;
