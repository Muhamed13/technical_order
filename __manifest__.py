{
    'name': 'Technical Order',
    'version': '17.0.0.1.0',
    'summary': 'Manage technical orders before creating sales orders',
    'description': """
Technical Order Management

Features:
- Create and manage technical orders.
- Approval workflow with email notification.
- Generate sales orders from approved technical orders.
- Prevent sales order quantities from exceeding requested quantities.
- Track related sales orders through smart buttons.
""",

    'author': 'Muhamed Helmy',
    'category': 'Sales',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'product',
        'mail',
        'sale_management',
],

    'data': [
        'security/ir.model.access.csv',

        'data/technical_order_sequence.xml',

        'views/technical_order_view.xml',
        'views/base_menu.xml',

        'wizard/technical_order_wizard.xml',

        'reports/technical_order.xml',
    ],

    'application': True,
    'installable': True,
}