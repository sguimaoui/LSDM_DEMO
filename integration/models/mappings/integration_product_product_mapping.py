# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IntegrationProductProductMapping(models.Model):
    _name = 'integration.product.product.mapping'
    _inherit = 'integration.mapping.mixin'
    _description = 'Integration Product Product Mapping'
    _mapping_fields = ('product_id', 'external_product_id')

    product_id = fields.Many2one(
        comodel_name='product.product',
        ondelete='cascade',
    )

    external_product_id = fields.Many2one(
        comodel_name='integration.product.product.external',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('uniq', 'unique(integration_id, product_id, external_product_id)', '')
    ]

    def _retrieve_external_vals(self, integration, odoo_value, code):
        res = super(IntegrationProductProductMapping, self)\
            ._retrieve_external_vals(integration, odoo_value, code)

        # res['external_reference'] = odoo_value.default_code
        return res
