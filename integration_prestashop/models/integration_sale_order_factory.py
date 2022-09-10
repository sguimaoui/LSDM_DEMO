# See LICENSE file for full copyright and licensing details.

from odoo import models, api
from datetime import datetime
from .sale_integration import DATETIME_FORMAT


class IntegrationSaleOrderFactory(models.AbstractModel):
    _inherit = 'integration.sale.order.factory'

    @api.model
    def _create_order(self, integration, order_data):
        is_prestashop = integration.is_prestashop()

        if is_prestashop and order_data['carrier']:
            carrier_code = order_data['carrier']
            carrier = self.env['delivery.carrier'].from_external(
                integration,
                carrier_code,
                raise_error=False,
            )
            if not carrier:
                integration.integrationApiImportDeliveryMethods()

        order = super(IntegrationSaleOrderFactory, self)._create_order(integration, order_data)

        return order

    @api.model
    def _create_partner(self, integration, partner_data, address_type=None):
        vals = {}
        is_prestashop = integration.is_prestashop()

        partner = super(IntegrationSaleOrderFactory, self)._create_partner(
            integration, partner_data, address_type
        )

        if is_prestashop:

            if 'newsletter' in partner_data:
                subscribed_to_newsletter_field = integration.subscribed_to_newsletter_id
                if subscribed_to_newsletter_field:
                    vals[subscribed_to_newsletter_field.name] = \
                        partner_data.get('newsletter', False)

            if 'newsletter_date_add' in partner_data:
                newsletter_registration_date_field = integration.newsletter_registration_date_id
                if newsletter_registration_date_field:
                    try:
                        newsletter_registration_date = datetime.strptime(
                            partner_data['newsletter_date_add'], DATETIME_FORMAT)
                    except ValueError:
                        newsletter_registration_date = False
                    vals[newsletter_registration_date_field.name] = newsletter_registration_date

            if 'customer_date_add' in partner_data:
                customer_registration_date_field = integration.customer_registration_date_id
                if customer_registration_date_field:
                    try:
                        customer_registration_date = datetime.strptime(
                            partner_data['customer_date_add'], DATETIME_FORMAT)
                    except ValueError:
                        customer_registration_date = False
                    vals[customer_registration_date_field.name] = customer_registration_date

        if vals:
            partner.write(vals)

        return partner
