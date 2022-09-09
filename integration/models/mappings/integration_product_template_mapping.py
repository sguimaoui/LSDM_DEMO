# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IntegrationProductTemplateMapping(models.Model):
    _name = 'integration.product.template.mapping'
    _inherit = 'integration.mapping.mixin'
    _description = 'Integration Product Template Mapping'
    _mapping_fields = ('template_id', 'external_template_id')

    template_id = fields.Many2one(
        comodel_name='product.template',
        ondelete='cascade',
    )

    external_template_id = fields.Many2one(
        comodel_name='integration.product.template.external',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('uniq', 'unique(integration_id, template_id, external_template_id)', '')
    ]

    def run_import_products(self, import_images=False):
        if self.env.context.get('import_images'):
            import_images = self.env.context.get('import_images')

        products_external = self.mapped(
            'external_template_id'
        )

        if products_external:
            return products_external.run_import_products(import_images)

    def _retrieve_external_vals(self, integration, odoo_value, code):
        res = super(IntegrationProductTemplateMapping, self)\
            ._retrieve_external_vals(integration, odoo_value, code)

        # res['external_reference'] = odoo_value.default_code  # TODO
        return res
