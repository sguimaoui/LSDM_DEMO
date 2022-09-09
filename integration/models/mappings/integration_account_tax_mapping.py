# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IntegrationAccountTaxMapping(models.Model):
    _name = 'integration.account.tax.mapping'
    _inherit = 'integration.mapping.mixin'
    _description = 'Integration Account Tax Mapping'
    _mapping_fields = ('tax_id', 'external_tax_id')

    tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Odoo Tax',
        ondelete='cascade',
        domain="[('type_tax_use','=','sale')]",
    )
    external_tax_id = fields.Many2one(
        comodel_name='integration.account.tax.external',
        string='External Tax',
        required=True,
        ondelete='cascade',
    )

    # TODO: remove in Odoo 16 as Deprecated
    external_tax_group_id = fields.Many2one(
        comodel_name='integration.account.tax.group.external',
        string='External Tax Group',
    )

    # TODO: add constain

    def import_taxes(self):
        tax_external = self.mapped('external_tax_id')

        if tax_external:
            return tax_external.import_taxes()
