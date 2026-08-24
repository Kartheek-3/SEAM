import { useState, useEffect, useRef } from 'react';
import { getExperimentLive, getExperimentTasksLive, getExperimentEvents } from '../services/api';

export const useLiveExperiment = (experimentId, pollingInterval = 3000) => {
    const [liveState, setLiveState] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isPolling, setIsPolling] = useState(false);
    
    // Store latest state in ref to avoid dependency cycles in interval
    const liveStateRef = useRef(liveState);
    useEffect(() => {
        liveStateRef.current = liveState;
    }, [liveState]);

    useEffect(() => {
        if (!experimentId) return;

        let pollTimer;
        let isMounted = true;

        const fetchData = async () => {
            if (!isMounted) return;
            try {
                // Determine if we should stop polling based on latest state
                const currentStatus = liveStateRef.current?.status;
                if (currentStatus === 'SUCCESS' || currentStatus === 'FAILED' || currentStatus === 'CANCELLED' || currentStatus === 'COMPLETED') {
                    setIsPolling(false);
                    return; // Stop polling
                }

                setIsPolling(true);

                const [liveRes, tasksRes, eventsRes] = await Promise.all([
                    getExperimentLive(experimentId),
                    getExperimentTasksLive(experimentId).catch(() => ({ data: [] })),
                    getExperimentEvents(experimentId).catch(() => ({ data: [] }))
                ]);

                if (isMounted) {
                    setLiveState(liveRes.data);
                    setTasks(tasksRes.data);
                    
                    // Simple append for events, or just replace depending on API design
                    // If API returns all events, we replace.
                    setEvents(eventsRes.data);
                    
                    setError(null);
                }
            } catch (err) {
                if (isMounted) {
                    setError(err.message);
                    setIsPolling(false); // Pause polling on error, or could keep trying
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                    
                    // Schedule next poll if still running and mounted
                    const latestStatus = liveStateRef.current?.status;
                    if (latestStatus !== 'SUCCESS' && latestStatus !== 'FAILED' && latestStatus !== 'CANCELLED' && latestStatus !== 'COMPLETED') {
                        pollTimer = setTimeout(fetchData, pollingInterval);
                    } else {
                        setIsPolling(false);
                    }
                }
            }
        };

        // Initial fetch
        fetchData();

        return () => {
            isMounted = false;
            if (pollTimer) clearTimeout(pollTimer);
        };
    }, [experimentId, pollingInterval]);

    return {
        liveState,
        tasks,
        events,
        loading,
        error,
        isPolling,
        isUnknown: liveState?.status === 'unknown'
    };
};
