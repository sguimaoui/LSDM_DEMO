# See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo PrestaShop Connector PRO',
    'summary': "Export products and your current stock from Odoo,"
               " and get orders from PrestaShop."
               " Update order status and provide tracking numbers to your customers; "
               "all this automatically and instantly!",
    'category': 'Sales',
    'version': '15.0.1.7.0',
    'images': ['static/description/images/banner.gif'],
    'author': 'VentorTech',
    'website': 'https://ventor.tech',
    'support': 'support@ventor.tech',
    'license': 'OPL-1',
    'live_test_url': 'https://odoo.ventor.tech/',
    'price': 224.00,
    'currency': 'EUR',
    'depends': [
        'integration',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/product_ecommerce_fields.xml',
        'views/sale_integration.xml',
        'views/external/integration_product_public_category_external_views.xml',
        'wizard/configuration_wizard_prestashop.xml',
        'views/res_partner_views.xml',
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': ['prestapyt'],
    },
    'installable': True,
    'application': True,
    "cloc_exclude": [
        "**/*"
    ]
}
