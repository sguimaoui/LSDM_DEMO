# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ProductTemplateFeatureLine(models.Model):
    _name = 'product.template.feature.line'
    _description = 'Feature Line'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template',
        index=True
    )
    feature_id = fields.Many2one(
        comodel_name='product.feature',
        string='Feature',
        ondelete='cascade',
        required=True,
    )
    feature_value_id = fields.Many2one(
        comodel_name='product.feature.value',
        string='Value',
        ondelete='cascade',
        required=True,
        domain="[('feature_id', '=', feature_id)]"
    )
