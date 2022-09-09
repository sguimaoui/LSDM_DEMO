# See LICENSE file for full copyright and licensing details.

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class IntegrationDeliveryCarrierExternal(models.Model):
    _name = 'integration.delivery.carrier.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Delivery Carrier External'

    def _fix_unmapped_shipping(self, integration):
        unmapped_shipping_methods = self.env['integration.delivery.carrier.mapping'].search([
            ('integration_id', '=', integration.id),
            ('carrier_id', '=', False),
        ])

        for mapping in unmapped_shipping_methods:
            delivery_service_vals = {
                'name': mapping.external_carrier_id.name,
                'default_code': mapping.external_carrier_id.code,
                'type': 'service',
                'sale_ok': False,
                'purchase_ok': False,
                'list_price': 0.0,
                'categ_id': self.env.ref('delivery.product_category_deliveries').id,
                'integration_ids': [(5, 0, 0)],
            }
            delivery_service = self.env['product.template'].create(delivery_service_vals)
            delivery_method_vals = {
                'name': mapping.external_carrier_id.name,
                'product_id': delivery_service.product_variant_ids[:1].id,
            }
            delivery_method = self.env['delivery.carrier'].create(delivery_method_vals)
            mapping.write({
                'carrier_id': delivery_method.id,
            })
