export const demoTasks = [
    { id: 't-1', title: 'Implement Product Model', type: 'Coding', agent: 'CodingAgent', status: 'SUCCESS', attempts: 1, duration: '45s', dependencies: 'none', artifacts: ['product.py'] },
    { id: 't-2', title: 'Database Schema', type: 'Coding', agent: 'CodingAgent', status: 'SUCCESS', attempts: 2, duration: '90s', dependencies: 't-1', artifacts: ['database.py'] },
    { id: 't-3', title: 'Product API', type: 'Coding', agent: 'CodingAgent', status: 'RUNNING', attempts: 1, duration: '20s', dependencies: 't-1', artifacts: ['api.py'] },
    { id: 't-4', title: 'QA Evaluation', type: 'QA', agent: 'QAAgent', status: 'PENDING', attempts: 0, duration: '-', dependencies: 't-2, t-3', artifacts: [] }
];
