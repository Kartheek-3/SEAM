import React, { useState } from 'react';
import { useIDE } from '../context/IDEContext';
import { useTasks } from '../hooks/useData';
import StatusBadge from '../components/StatusBadge';

const TaskGraph = ({ tasks, onSelect }) => {
    return (
        <div className="bg-seam-panel border border-seam-border rounded-xl p-6 shadow-sm overflow-x-auto overflow-y-hidden mb-6 h-64 flex items-center relative">
            <h3 className="absolute top-4 left-4 text-sm font-semibold text-seam-text-muted uppercase tracking-wider">Dependency Graph</h3>
            
            <div className="min-w-max mx-auto flex items-center justify-center pt-8">
                {/* Simplified static representation of a DAG for demo */}
                <div className="flex items-center gap-8">
                    <div className="flex flex-col gap-6">
                        <div className="px-4 py-2 bg-seam-bg border-2 border-seam-success rounded-lg text-seam-text text-sm cursor-pointer shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                            Analysis ✓
                        </div>
                        <div className="px-4 py-2 bg-seam-bg border-2 border-seam-success rounded-lg text-seam-text text-sm cursor-pointer shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                            Planning ✓
                        </div>
                    </div>
                    
                    <div className="w-8 h-0.5 bg-seam-border relative">
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-t-4 border-t-transparent border-b-4 border-b-transparent border-l-4 border-l-seam-border"></div>
                    </div>
                    
                    <div className="flex flex-col gap-4">
                        {tasks.filter(t => t.type === 'Coding').map(task => (
                            <div 
                                key={task.id}
                                onClick={() => onSelect(task)}
                                className={`px-4 py-2 bg-seam-bg border-2 rounded-lg text-seam-text text-sm cursor-pointer transition-colors ${
                                    task.status === 'SUCCESS' ? 'border-seam-success hover:border-emerald-400' :
                                    task.status === 'RUNNING' ? 'border-seam-accent shadow-[0_0_15px_rgba(59,130,246,0.3)]' :
                                    'border-seam-border hover:border-seam-text-muted'
                                }`}
                            >
                                {task.title} {task.status === 'SUCCESS' ? '✓' : task.status === 'RUNNING' ? '●' : '○'}
                            </div>
                        ))}
                    </div>
                    
                    <div className="w-8 h-0.5 bg-seam-border relative">
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-t-4 border-t-transparent border-b-4 border-b-transparent border-l-4 border-l-seam-border"></div>
                    </div>
                    
                    <div className="flex flex-col gap-4">
                        <div 
                            onClick={() => onSelect(tasks.find(t => t.type === 'QA'))}
                            className="px-4 py-2 bg-seam-bg border-2 border-seam-border rounded-lg text-seam-text-muted text-sm cursor-pointer hover:border-seam-text-muted"
                        >
                            QA Gate ○
                        </div>
                    </div>
                    
                    <div className="w-8 h-0.5 bg-seam-border relative">
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-t-4 border-t-transparent border-b-4 border-b-transparent border-l-4 border-l-seam-border"></div>
                    </div>
                    
                    <div className="flex flex-col gap-4">
                        <div className="px-4 py-2 bg-seam-bg border-2 border-seam-border rounded-lg text-seam-text-muted text-sm cursor-not-allowed opacity-50">
                            Delivery ○
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const Tasks = () => {
    const { tasks, loading, error } = useTasks();
    const { openTaskDrawer } = useIDE();
    const [filter, setFilter] = useState('All');
    
    const filters = ['All', 'Coding', 'QA', 'Delivery', 'Completed', 'Running'];

    const filteredTasks = tasks.filter(task => {
        if (filter === 'All') return true;
        if (filter === 'Completed') return task.status === 'SUCCESS';
        if (filter === 'Running') return task.status === 'RUNNING';
        return task.type === filter;
    });

    return (
        <div className="space-y-6 h-full flex flex-col p-6">
            <div className="flex justify-between items-center shrink-0">
                <div>
                    <h1 className="text-2xl font-bold text-seam-text">TASKS</h1>
                    <p className="text-sm text-seam-text-muted mt-1">Dependency graph and agent execution state</p>
                </div>
            </div>

            {loading && <div className="text-seam-text-muted">Loading tasks...</div>}
            {error && <div className="text-seam-error">Backend unavailable: {error}</div>}
            {!loading && !error && tasks.length === 0 && <div className="text-seam-text-muted">No tasks found.</div>}

            {!loading && !error && tasks.length > 0 && (
                <>
                    <TaskGraph tasks={tasks} onSelect={openTaskDrawer} />

            <div className="flex items-center gap-2 mb-2 shrink-0">
                {filters.map(f => (
                    <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                            filter === f
                                ? 'bg-seam-accent/20 text-seam-accent border-seam-accent/50'
                                : 'bg-seam-panel text-seam-text-muted border-seam-border hover:bg-seam-border/30 hover:text-seam-text'
                        }`}
                    >
                        {f}
                    </button>
                ))}
            </div>

            <div className="bg-seam-panel border border-seam-border rounded-xl flex-1 flex flex-col min-h-0 overflow-hidden shadow-sm">
                <div className="overflow-auto flex-1">
                    <table className="w-full text-left border-collapse">
                        <thead className="sticky top-0 bg-seam-panel border-b border-seam-border z-10">
                            <tr>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Task</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Type</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Agent</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Status</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Duration</th>
                                <th className="p-4 text-xs font-semibold text-seam-text-muted uppercase tracking-wider">Dependencies</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-seam-border">
                            {filteredTasks.map((task) => (
                                <tr 
                                    key={task.id} 
                                    onClick={() => openTaskDrawer(task)}
                                    className="hover:bg-seam-bg/30 transition-colors cursor-pointer group"
                                >
                                    <td className="p-4 text-sm font-medium text-seam-text group-hover:text-seam-accent transition-colors">
                                        <div className="flex flex-col">
                                            <span className="font-mono text-xs text-seam-text-muted mb-0.5">{task.id}</span>
                                            <span>{task.title}</span>
                                        </div>
                                    </td>
                                    <td className="p-4 text-sm text-seam-text-muted">{task.type}</td>
                                    <td className="p-4 text-sm text-seam-text-muted">{task.agent}</td>
                                    <td className="p-4">
                                        <StatusBadge status={task.status} />
                                    </td>
                                    <td className="p-4 text-sm text-seam-text-muted font-mono">{task.duration}</td>
                                    <td className="p-4 text-sm text-seam-text-muted font-mono text-xs">{task.dependencies}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            </>
            )}
        </div>
    );
};

export default Tasks;
