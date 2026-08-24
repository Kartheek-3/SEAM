export const demoProjects = [
    {
        id: 'p-1',
        name: 'E-Commerce Catalog',
        status: 'Active',
        components: 4,
        tasks: 16,
        artifacts: 11,
        latestExperiment: '#15',
        description: 'Product catalog service for the SEAM ecommerce platform.',
        tree: [
            {
                name: 'ecommerce-catalog',
                type: 'folder',
                children: [
                    {
                        name: 'src',
                        type: 'folder',
                        children: [
                            { name: 'api', type: 'folder', children: [{ name: 'routes.py', type: 'file' }] },
                            { name: 'models', type: 'folder', children: [{ name: 'product.py', type: 'file' }] },
                            { name: 'services', type: 'folder', children: [{ name: 'catalog.py', type: 'file' }] },
                            { name: 'main.py', type: 'file' }
                        ]
                    },
                    { name: 'tests', type: 'folder', children: [{ name: 'test_products.py', type: 'file' }] },
                    { name: 'config', type: 'folder', children: [{ name: 'settings.json', type: 'file' }] },
                    { name: 'requirements.txt', type: 'file' },
                    { name: 'README.md', type: 'file' }
                ]
            }
        ]
    }
];
