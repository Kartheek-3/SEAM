import React from 'react';
import { useProjects } from '../hooks/useData';
import { useNavigate } from 'react-router-dom';
import { Folder, GitBranch, Archive, CheckSquare, FlaskConical, LayoutDashboard } from 'lucide-react';

const Projects = () => {
    const { projects, loading, error } = useProjects();
    const navigate = useNavigate();

    if (loading) return <div className="p-6 text-seam-text-muted">Loading projects...</div>;
    if (error) return <div className="p-6 text-seam-error">Backend unavailable: {error}</div>;
    if (!projects || projects.length === 0) return <div className="p-6 text-seam-text-muted">No projects found.</div>;

    return (
        <div className="space-y-6 h-full flex flex-col p-6">
            <div className="shrink-0">
                <h1 className="text-2xl font-bold text-seam-text">PROJECTS</h1>
                <p className="text-sm text-seam-text-muted mt-1">Engineering target configurations</p>
            </div>

            <div className="flex-1 overflow-y-auto">
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    {projects.map((project) => (
                        <div key={project.id} className="bg-seam-panel border border-seam-border rounded-xl shadow-sm overflow-hidden flex flex-col hover:border-seam-accent/50 transition-colors">
                            
                            {/* Header */}
                            <div className="p-6 border-b border-seam-border bg-seam-bg flex justify-between items-start">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-seam-accent/10 border border-seam-accent/20 rounded-xl">
                                        <Folder className="w-8 h-8 text-seam-accent" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold text-seam-text">{project.name}</h2>
                                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 mt-1 rounded bg-seam-success/10 text-seam-success text-xs font-semibold border border-seam-success/20">
                                            <span className="w-1.5 h-1.5 rounded-full bg-seam-success"></span>
                                            {project.status}
                                        </span>
                                    </div>
                                </div>
                                <button 
                                    onClick={() => navigate('/workspace')}
                                    className="px-4 py-2 bg-seam-accent text-white text-sm font-semibold rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2 shadow-[0_0_15px_rgba(59,130,246,0.2)]"
                                >
                                    <LayoutDashboard className="w-4 h-4" />
                                    Open Workspace
                                </button>
                            </div>

                            {/* Details */}
                            <div className="p-6 flex-1 flex flex-col">
                                <p className="text-sm text-seam-text-muted mb-6">{project.description}</p>
                                
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                                    <div className="p-3 bg-seam-bg rounded-lg border border-seam-border flex flex-col gap-1">
                                        <div className="flex items-center gap-2 text-seam-text-muted">
                                            <GitBranch className="w-4 h-4" />
                                            <span className="text-xs font-semibold uppercase tracking-wider">Architecture</span>
                                        </div>
                                        <span className="text-lg font-bold text-seam-text">{project.components} Components</span>
                                    </div>
                                    <div className="p-3 bg-seam-bg rounded-lg border border-seam-border flex flex-col gap-1">
                                        <div className="flex items-center gap-2 text-seam-text-muted">
                                            <CheckSquare className="w-4 h-4" />
                                            <span className="text-xs font-semibold uppercase tracking-wider">Tasks</span>
                                        </div>
                                        <span className="text-lg font-bold text-seam-text">{project.tasks} Generated</span>
                                    </div>
                                    <div className="p-3 bg-seam-bg rounded-lg border border-seam-border flex flex-col gap-1">
                                        <div className="flex items-center gap-2 text-seam-text-muted">
                                            <Archive className="w-4 h-4" />
                                            <span className="text-xs font-semibold uppercase tracking-wider">Artifacts</span>
                                        </div>
                                        <span className="text-lg font-bold text-seam-text">{project.artifacts} Tracked</span>
                                    </div>
                                    <div className="p-3 bg-seam-bg rounded-lg border border-seam-border flex flex-col gap-1">
                                        <div className="flex items-center gap-2 text-seam-text-muted">
                                            <FlaskConical className="w-4 h-4" />
                                            <span className="text-xs font-semibold uppercase tracking-wider">Latest Run</span>
                                        </div>
                                        <span className="text-lg font-bold text-seam-text font-mono">{project.latestExperiment}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Projects;
