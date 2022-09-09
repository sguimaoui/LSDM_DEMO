# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IntegrationDeliveryCarrierMapping(models.Model):
    _name = 'integration.delivery.carrier.mapping'
    _inherit = 'integration.mapping.mixin'
    _description = 'Integration Delivery Carrier Mapping'
    _mapping_fields = ('carrier_id', 'external_carrier_id')

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        ondelete='set null',
    )

    external_carrier_id = fields.Many2one(
        comodel_name='integration.delivery.carrier.external',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        (
            'uniq_mapping',
            'unique(integration_id, external_carrier_id)',
            'Delivery Carrier mapping should be unique per integration'
        ),
    ]
