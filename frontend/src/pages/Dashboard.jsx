import React from 'react';
import { FlaskConical, Folder, CheckSquare, TrendingUp } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import AgentPipeline from '../components/AgentPipeline';
import RecentExperiment from '../components/RecentExperiment';
import TaskProgress from '../components/TaskProgress';
import { demoMetrics } from '../data/mockData';

const Dashboard = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-seam-text">SEAM Engineering Dashboard</h1>
                <p className="text-sm text-seam-text-muted mt-1">Autonomous multi-agent software engineering orchestration</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <MetricCard 
                    title="Experiments" 
                    value={demoMetrics.experiments} 
                    icon={FlaskConical} 
                    trend="+2 this week"
                />
                <MetricCard 
                    title="Projects" 
                    value={demoMetrics.projects} 
                    icon={Folder} 
                />
                <MetricCard 
                    title="Tasks Completed" 
                    value={demoMetrics.tasksCompleted} 
                    icon={CheckSquare} 
                />
                <MetricCard 
                    title="Success Rate" 
                    value={`${demoMetrics.successRate}%`} 
                    icon={TrendingUp} 
                    trend="+5% vs last month"
                />
            </div>

            <AgentPipeline />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <RecentExperiment />
                <TaskProgress />
            </div>
        </div>
    );
};

export default Dashboard;
