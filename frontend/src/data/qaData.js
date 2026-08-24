export const demoQAOverview = {
    total: 11,
    passed: 8,
    failed: 1,
    reworked: 2,
    pending: 2
};

export const demoQATasks = [
    { 
        id: 'qa-1', 
        target: 'product.py', 
        verdict: 'PASS', 
        passed: 12, 
        failed: 0, 
        critical: 0, 
        major: 0, 
        minor: 1,
        findings: [
            { severity: 'MINOR', description: 'Unused import typing.List', file: 'product.py', line: 2, recommendation: 'Remove unused import' }
        ]
    },
    { 
        id: 'qa-2', 
        target: 'api.py', 
        verdict: 'FAIL', 
        passed: 4, 
        failed: 2, 
        critical: 1, 
        major: 1, 
        minor: 0,
        findings: [
            { severity: 'CRITICAL', description: 'Authentication endpoint missing validation', file: 'api.py', line: 45, recommendation: 'Add token validation dependency' },
            { severity: 'MAJOR', description: 'Product API missing error handling for 404', file: 'api.py', line: 78, recommendation: 'Add try-except block and raise HTTPException' }
        ]
    }
];
