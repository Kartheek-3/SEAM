export const demoExperiments = [
    {
        id: '#15',
        scenario: 'ecommerce-catalog',
        model: 'llama3.1',
        mode: 'REAL',
        duration: 'Running',
        tasks: '8/11',
        status: 'RUNNING',
        llmCalls: 45,
        stages: [
            { name: 'Analysis', status: 'SUCCESS', duration: '1m 15s' },
            { name: 'Planning', status: 'SUCCESS', duration: '2m 30s' },
            { name: 'ProjectPlan', status: 'SUCCESS', duration: '5s' },
            { name: 'Supervisor', status: 'SUCCESS', duration: 'ongoing' },
            { name: 'Coding', status: 'RUNNING', duration: '12m 10s' },
            { name: 'QA', status: 'PENDING', duration: '-' },
            { name: 'Rework', status: 'PENDING', duration: '-' },
            { name: 'Delivery', status: 'PENDING', duration: '-' }
        ]
    },
    {
        id: '#14',
        scenario: 'ecommerce-catalog',
        model: 'llama3.1',
        mode: 'REAL',
        duration: '74m',
        tasks: '8/16',
        status: 'FAILED',
        llmCalls: 210,
        stages: [
            { name: 'Analysis', status: 'SUCCESS', duration: '1m 10s' },
            { name: 'Planning', status: 'SUCCESS', duration: '2m 20s' },
            { name: 'ProjectPlan', status: 'SUCCESS', duration: '4s' },
            { name: 'Supervisor', status: 'SUCCESS', duration: '74m' },
            { name: 'Coding', status: 'SUCCESS', duration: '65m' },
            { name: 'QA', status: 'FAILED', duration: '5m' },
            { name: 'Rework', status: 'PENDING', duration: '-' },
            { name: 'Delivery', status: 'PENDING', duration: '-' }
        ]
    }
];
