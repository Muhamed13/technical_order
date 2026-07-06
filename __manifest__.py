{
    'name': 'Technical Order',
    'version': '17.0.0.1.0',
    'summary': 'Manage technical orders before creating sales orders',
    'description': """
Technical Order Management

- Create Technical Orders
- Approval Workflow
- Generate Sales Orders
""",
    'author': 'Muhamed Helmy',
    'category': 'Sales',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'product',
],

    'data': [
        'security/ir.model.access.csv',

        'data/technical_order_sequence.xml',
    ],

    'application': True,
    'installable': True,
}