import React from 'react';
import PipelineStage from './PipelineStage';
import { demoPipeline } from '../data/mockData';

const AgentPipeline = () => {
    return (
        <div className="bg-seam-panel border border-seam-border rounded-xl p-6 shadow-sm overflow-x-auto overflow-y-hidden">
            <h2 className="text-lg font-semibold text-seam-text mb-8">Agent Pipeline</h2>
            <div className="flex flex-col md:flex-row items-center justify-start min-w-max py-4 px-2">
                {demoPipeline.map((stage, index) => (
                    <PipelineStage 
                        key={stage.id} 
                        stage={stage} 
                        isLast={index === demoPipeline.length - 1} 
                    />
                ))}
            </div>
        </div>
    );
};

export default AgentPipeline;
