export const demoAgentEvents = [
    { id: 1, timestamp: '20:31:04', agent: 'Supervisor', event: 'Analysis completed', status: 'SUCCESS' },
    { id: 2, timestamp: '20:32:19', agent: 'PlanningAgent', event: 'Planning completed', status: 'SUCCESS' },
    { id: 3, timestamp: '20:34:08', agent: 'CodingAgent', event: 'CodingAgent started', status: 'RUNNING' },
    { id: 4, timestamp: '20:35:42', agent: 'CodingAgent', event: 'product.py generated', status: 'SUCCESS' },
    { id: 5, timestamp: '20:36:10', agent: 'Supervisor', event: 'QA queued', status: 'PENDING' }
];

export const demoDelivery = {
    required: 11,
    passed: 8,
    failed: 1,
    status: 'BLOCKED'
};
