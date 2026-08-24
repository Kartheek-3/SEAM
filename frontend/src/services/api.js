import axios from 'axios';
import { demoProjects } from '../data/projectData';
import { demoTasks } from '../data/taskData';
import { demoExperiments } from '../data/experimentData';
import { demoArtifacts } from '../data/artifactData';
import { demoQAOverview, demoQATasks } from '../data/qaData';
import { demoDelivery } from '../data/agentData';

const MODE = import.meta.env.VITE_DATA_MODE || 'mock';

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    timeout: 10000,
});

export const getProjects = async () => {
    if (MODE === 'mock') return Promise.resolve({ data: demoProjects });
    return apiClient.get('/projects');
};

export const getProject = async (id) => {
    if (MODE === 'mock') {
        const project = demoProjects.find(p => p.id === id);
        return project ? Promise.resolve({ data: project }) : Promise.reject(new Error("Not found"));
    }
    return apiClient.get(`/projects/${id}`);
};

export const getExperiments = async () => {
    if (MODE === 'mock') return Promise.resolve({ data: demoExperiments });
    return apiClient.get('/experiments');
};

export const getExperiment = async (id) => {
    if (MODE === 'mock') {
        const exp = demoExperiments.find(e => e.id === id);
        return exp ? Promise.resolve({ data: exp }) : Promise.reject(new Error("Not found"));
    }
    return apiClient.get(`/experiments/${id}`);
};

export const getTasks = async () => {
    if (MODE === 'mock') return Promise.resolve({ data: demoTasks });
    return apiClient.get('/tasks');
};

export const getTask = async (id) => {
    if (MODE === 'mock') {
        const task = demoTasks.find(t => t.id === id);
        return task ? Promise.resolve({ data: task }) : Promise.reject(new Error("Not found"));
    }
    return apiClient.get(`/tasks/${id}`);
};

export const getQAResults = async () => {
    if (MODE === 'mock') return Promise.resolve({ data: { overview: demoQAOverview, tasks: demoQATasks } });
    // Since task details are not persisted backend, we mock or return empty structure
    // Or return 404 from backend and let frontend handle it
    return apiClient.get('/qa/dummy').catch(() => ({ data: { overview: { testsPassed: 0, testsFailed: 0, testsTotal: 0, critical: 0, major: 0, minor: 0 }, tasks: [] } }));
};

export const getDeliveryStatus = async () => {
    if (MODE === 'mock') return Promise.resolve({ data: demoDelivery });
    return apiClient.get('/delivery/dummy').catch(() => ({ data: { status: "blocked", qa_passed: 0, qa_total: 0, critical_defects: 0 } }));
};

export const getArtifacts = async () => {
    if (MODE === 'mock') return Promise.resolve({ data: demoArtifacts });
    return apiClient.get('/artifacts');
};

export const getExperimentLive = async (id) => {
    if (MODE === 'mock') {
        // Mock a running state if it's the specific demo experiment
        if (id === '#15' || id === '15' || id === 'exp-15') {
            return Promise.resolve({
                data: {
                    experiment_id: id,
                    status: "running",
                    current_stage: "coding",
                    started_at: new Date().toISOString(),
                    elapsed_seconds: 123,
                    stages: {
                        analysis: { status: "SUCCESS" },
                        planning: { status: "SUCCESS" },
                        supervisor: { status: "RUNNING" },
                        coding: { status: "RUNNING" },
                        qa: { status: "PENDING" },
                        rework: { status: "PENDING" },
                        delivery: { status: "PENDING" }
                    }
                }
            });
        }
        return Promise.resolve({ data: { status: "unknown" } });
    }
    return apiClient.get(`/experiments/${id.replace('#', '')}/live`);
};

export const getExperimentTasksLive = async (id) => {
    if (MODE === 'mock') {
        if (id === '#15' || id === '15' || id === 'exp-15') {
            return Promise.resolve({ data: demoTasks });
        }
        return Promise.resolve({ data: [] });
    }
    return apiClient.get(`/experiments/${id.replace('#', '')}/tasks/live`);
};

export const getExperimentEvents = async (id) => {
    if (MODE === 'mock') {
        if (id === '#15' || id === '15' || id === 'exp-15') {
            return Promise.resolve({ data: [{ type: "task_started", message: "Started Coding task Product Service" }] });
        }
        return Promise.resolve({ data: [] });
    }
    return apiClient.get(`/experiments/${id.replace('#', '')}/events`);
};

export default apiClient;
