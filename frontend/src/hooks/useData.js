import { useState, useEffect } from 'react';
import { getProjects, getTasks, getExperiments, getExperiment, getArtifacts, getQAResults, getDeliveryStatus } from '../services/api';

export const useProjects = () => {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        getProjects()
            .then(res => setProjects(res.data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);
    return { projects, loading, error };
};

export const useTasks = () => {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        getTasks()
            .then(res => setTasks(res.data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);
    return { tasks, loading, error };
};

export const useExperiments = () => {
    const [experiments, setExperiments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        getExperiments()
            .then(res => setExperiments(res.data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);
    return { experiments, loading, error };
};

export const useExperiment = (id) => {
    const [experiment, setExperiment] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        getExperiment(id)
            .then(res => setExperiment(res.data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, [id]);
    return { experiment, loading, error };
};

export const useArtifacts = () => {
    const [artifacts, setArtifacts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        getArtifacts()
            .then(res => setArtifacts(res.data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);
    return { artifacts, loading, error };
};

export const useQA = (taskId = null) => {
    const [qaData, setQaData] = useState({ overview: null, tasks: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        getQAResults()
            .then(res => setQaData(res.data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);
    return { ...qaData, loading, error };
};

export const useDelivery = (projectId = null) => {
    const [delivery, setDelivery] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        getDeliveryStatus()
            .then(res => setDelivery(res.data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);
    return { delivery, loading, error };
};
