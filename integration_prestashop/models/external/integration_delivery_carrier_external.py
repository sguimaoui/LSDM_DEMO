
from odoo import models, api


class IntegrationDeliveryCarrierExternal(models.Model):
    _inherit = 'integration.delivery.carrier.external'

    def _fix_prestashop_unmapped_shipping(self, integration):
        unmapped_shipping_methods = self.env['integration.delivery.carrier.mapping'].search([
            ('integration_id', '=', integration.id),
            ('carrier_id', '=', False),
        ])
        for mapping in unmapped_shipping_methods:
            prestashop_data = integration.get_parent_delivery_methods(
                mapping.external_carrier_id.code,
            )
            id_list = [data['id'] for data in prestashop_data]
            mapped_methods = self.env['integration.delivery.carrier.mapping'].search(
                [
                    ('integration_id', '=', integration.id),
                    ('carrier_id', '!=', False),
                    ('external_carrier_id.code', 'in', id_list),
                ], order='id desc', limit=1)
            if mapped_methods:
                mapping.write({
                    'carrier_id': mapped_methods.carrier_id.id,
                })

    @api.model
    def fix_unmapped(self, integration):
        if integration.is_prestashop():
            return self._fix_prestashop_unmapped_shipping(integration)

        return super(IntegrationDeliveryCarrierExternal, self).fix_unmapped(integration)
