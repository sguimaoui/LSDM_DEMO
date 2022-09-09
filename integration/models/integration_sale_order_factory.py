# See LICENSE file for full copyright and licensing details.

from ..exceptions import NotMappedFromExternal, ApiImportError

import logging

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


_logger = logging.getLogger(__name__)


class IntegrationSaleOrderFactory(models.AbstractModel):
    _name = 'integration.sale.order.factory'
    _description = 'Integration Sale Order Factory'

    @api.model
    def create_order(self, integration, order_data):
        order = self.env['integration.sale.order.mapping'].search([
            ('integration_id', '=', integration.id),
            ('external_id.code', '=', order_data['id']),
        ]).odoo_id
        if not order:
            order = self._create_order(integration, order_data)
            order.create_mapping(integration, order_data['id'], extra_vals={'name': order.name})
            self._post_create(integration, order)
        return order

    @api.model
    def _create_order(self, integration, order_data):
        order_vals = self._prepare_order_vals(integration, order_data)
        if integration.default_sales_team_id:
            order_vals['team_id'] = integration.default_sales_team_id.id

        if integration.default_sales_person_id:
            order_vals['user_id'] = integration.default_sales_person_id.id

        if integration.order_name_ref:
            order_vals['name'] = '%s/%s' % (integration.order_name_ref, order_data['ref'])

        order = self.env['sale.order'].create(order_vals)

        if not integration.order_name_ref:
            order.name += '/%s' % order_data['ref']

        if order_data['carrier']:
            carrier = self.env['delivery.carrier'].from_external(
                integration, order_data['carrier']
            )
            order.set_delivery_line(carrier, order_data['shipping_cost'])

            delivery_line = order.order_line.filtered(lambda line: line.is_delivery)

            carrier_tax_ids = order_data.get('carrier_tax_ids')

            if delivery_line and carrier_tax_ids:
                delivery_tax_ids = self.env['account.tax']

                for carrier_tax_id in carrier_tax_ids:
                    delivery_tax_ids += self.env['account.tax'].from_external(
                        integration, carrier_tax_id
                    )

                delivery_line.tax_id = delivery_tax_ids

            if delivery_line and order_data.get('carrier_tax_rate') == 0:
                if not all(x.amount == 0 for x in delivery_line.tax_id):
                    delivery_line.tax_id = False

            if delivery_line and 'shipping_cost_tax_excl' in order_data:
                if not self._get_tax_price_included(delivery_line.tax_id):
                    delivery_line.price_unit = order_data['shipping_cost_tax_excl']

        self._create_discount_line(
            integration,
            order,
            order_data.get('total_discounts_tax_incl'),
            order_data.get('total_discounts_tax_excl'),
        )

        # Check difference of total order amount and correct it
        if order_data.get('amount_total', False):
            price_difference = float_round(
                value=order_data['amount_total'] - order.amount_total,
                precision_digits=self.env['decimal.precision'].precision_get('Product Price'),
            )

            if price_difference:
                if price_difference > 0:
                    difference_product_id = integration.positive_price_difference_product_id
                else:
                    difference_product_id = integration.negative_price_difference_product_id

                if not difference_product_id:
                    raise ApiImportError(_('Select Price Difference Product in Sale Integration'))

                difference_line = self.env['sale.order.line'].create({
                    'product_id': difference_product_id.id,
                    'order_id': order.id,
                })

                difference_line.product_id_change()
                difference_line.price_unit = price_difference
                difference_line.tax_id = False

        self._add_payment_transactions(
            order,
            integration,
            order_data.get('payment_transactions')
        )

        return order

    @api.model
    def _prepare_order_vals_hook(self, integration, original_order_data, create_order_vals):
        # Use this method to override in subclasses to define different behavior
        # of preparation of order values
        pass

    @api.model
    def _prepare_order_vals(self, integration, order_data):
        partner, shipping, billing = self._create_customer(integration, order_data)

        payment_method = self._get_payment_method(integration, order_data['payment_method'])

        delivery_notes_field_name = integration.so_delivery_note_field.name

        amount_total = order_data.get('amount_total', False)

        order_line = []
        for line in order_data['lines']:
            order_line.append((0, 0, self._prepare_order_line_vals(integration, line)))

        order_vals = {
            'integration_id': integration.id,
            'integration_amount_total': amount_total,
            'partner_id': partner.id if partner else False,
            'partner_shipping_id': shipping.id if shipping else False,
            'partner_invoice_id': billing.id if billing else False,
            'order_line': order_line,
            'payment_method_id': payment_method.id,
            delivery_notes_field_name: order_data['delivery_notes'],
        }

        current_state = order_data.get('current_order_state')
        if current_state:
            sub_status = self._get_order_sub_status(
                integration, current_state,
            )
            order_vals.update({
                'sub_status_id': sub_status.id,
            })

        pricelist = self._get_order_pricelist(integration, order_data)
        if pricelist:
            order_vals['pricelist_id'] = pricelist.id

        self._prepare_order_vals_hook(integration, order_data, order_vals)

        return order_vals

    @api.model
    def _get_order_sub_status(self, integration, ext_current_state):
        SubStatus = self.env['sale.order.sub.status']

        sub_status = SubStatus.from_external(
            integration, ext_current_state, raise_error=False)

        if not sub_status:
            integration.integrationApiImportSaleOrderStatuses()

            sub_status = SubStatus.from_external(
                integration, ext_current_state)

        return sub_status

    def _get_order_pricelist(self, integration, order_data):
        company = integration.company_id
        company_currency_iso = company.currency_id.name
        ecommerce_currency_iso = order_data.get('currency', '')

        if not all([company_currency_iso, ecommerce_currency_iso]):
            return False

        if company_currency_iso.lower() == ecommerce_currency_iso.lower():
            return False

        odoo_currency = self.env['res.currency'].search([
            ('name', '=ilike', ecommerce_currency_iso.lower()),
        ], limit=1)
        if not odoo_currency:
            raise ApiImportError(_(
                'Currency ISO code "%s" was not found in Odoo.' % ecommerce_currency_iso
            ))

        Pricelist = self.env['product.pricelist']

        pricelists = Pricelist.search([
            ('company_id', 'in', (company.id, False)),
            ('currency_id', '=', odoo_currency.id),
        ])
        pricelist = pricelists.filtered(lambda x: x.company_id == company)[:1] or pricelists[:1]

        if not pricelist:
            vals = {
                'company_id': company.id,
                'currency_id': odoo_currency.id,
                'name': f'Integration {ecommerce_currency_iso}',
            }
            pricelist = Pricelist.create(vals)

        return pricelist

    @api.model
    def _create_customer(self, integration, order_data):
        customer = False
        shipping = False
        billing = False

        if order_data.get('customer'):
            customer = self._create_partner(integration, order_data['customer'])
            customer.customer_rank = 1

        if order_data.get('shipping'):
            shipping = self._create_partner(integration, order_data['shipping'], 'delivery')

        if order_data.get('billing'):
            billing = self._create_partner(integration, order_data['billing'], 'invoice')

        return self._set_default_customer(integration, customer, shipping, billing)

    @api.model
    def _set_default_customer(self, integration, customer, shipping, billing):
        if not customer:
            if not integration.default_customer:
                raise ApiImportError(_('Default Customer is empty. Please, feel it in '
                                       'Sale Integration on the tab "Sale Order Defaults"'))

            customer = integration.default_customer

        if not shipping:
            shipping = integration.default_customer

        if not billing:
            billing = integration.default_customer

        return customer, shipping, billing

    @api.model
    def _create_partner(self, integration, partner_data, address_type=None):
        try:
            partner = self.env['res.partner'].from_external(
                integration, partner_data['id']
            )
        except NotMappedFromExternal:
            partner = None

        if partner_data.get('country'):
            country = self.env['res.country'].from_external(
                integration, partner_data.get('country')
            )
        else:
            country = self.env['res.country']

        if partner_data.get('state'):
            state = self.env['res.country.state'].from_external(
                integration, partner_data.get('state')
            )
        else:
            state = self.env['res.country.state']

        vals = {
            'name': partner_data['person_name'],
            'street': partner_data.get('street'),
            'street2': partner_data.get('street2'),
            'city': partner_data.get('city'),
            'country_id': country.id,
            'state_id': state.id,
            'zip': partner_data.get('zip'),
            'email': partner_data.get('email'),
            'phone': partner_data.get('phone'),
            'mobile': partner_data.get('mobile'),
            'integration_id': integration.id,
        }

        if partner_data.get('language'):
            language = self.env['res.lang'].from_external(
                integration, partner_data.get('language')
            )
            if language:
                vals.update({
                    'lang': language.code,
                })

        person_id_field = integration.customer_personal_id_field
        if person_id_field:
            vals.update({
                person_id_field.name: partner_data.get('person_id_number'),
            })

        if address_type:
            vals['type'] = address_type

        # Adding Company Specific fields
        if partner_data.get('company_name'):
            vals.update({
                'company_name': partner_data.get('company_name'),
            })

        company_vat_field = integration.customer_company_vat_field
        if company_vat_field and partner_data.get('company_reg_number'):
            vals.update({
                company_vat_field.name: partner_data.get('company_reg_number'),
            })

        if partner:
            partner.write(vals)
        else:
            partner = self.env['res.partner'].create(vals)
            extra_vals = {'name': partner_data['person_name']}

            partner.create_mapping(integration, partner_data['id'], extra_vals=extra_vals)

        return partner

    @api.model
    def _get_odoo_product(self, integration, variant_code, raise_error):
        product = self.env['product.product'].from_external(
            integration,
            variant_code,
            raise_error=False,
        )

        if not product and raise_error:
            raise ApiImportError(
                _('Failed to find external variant with code "%s". Please, run "IMPORT PRODUCT'
                  ' FROM EXTERNAL" using button on "Initial Import" tab on your sales integration'
                  ' with name "%s". After this make sure that all your products are mapped '
                  'in "Mappings - Products" and "Mappings - '
                  'Variants" menus.') % (variant_code, integration.name)
            )

        return product

    @api.model
    def _try_get_odoo_product(self, integration, line):
        variant_code = line['product_id']
        product = self._get_odoo_product(integration, variant_code, False)

        if product:
            return product

        # Looks like this is new product in e-Commerce system
        # Or it is not fully mapped. In any case let's try to repeat mapping
        # for only this product and then try to find it again
        # If not found in this case, raise error
        template_code = variant_code.split('-')[0]
        integration.import_external_product(template_code)

        product = self._get_odoo_product(integration, variant_code, True)

        return product

    @api.model
    def _prepare_order_line_vals(self, integration, line):
        product = self._try_get_odoo_product(integration, line)

        vals = {
            'integration_external_id': line['id'],
            'product_id': product.id,
        }

        if 'product_uom_qty' in line:
            vals.update(product_uom_qty=line['product_uom_qty'])

        taxes = self.env['account.tax'].browse()

        if 'taxes' in line:
            for tax_id in line['taxes']:
                taxes |= self.env['account.tax'].from_external(
                    integration, tax_id
                )
            vals.update(tax_id=[(6, 0, taxes.ids)])

        if taxes and self._get_tax_price_included(taxes):
            if 'price_unit_tax_incl' in line:
                vals.update(price_unit=line['price_unit_tax_incl'])
        else:
            if 'price_unit' in line:
                vals.update(price_unit=line['price_unit'])

        if 'discount' in line:
            vals.update(discount=line['discount'])

        return vals

    @api.model
    def _post_create(self, integration, order):
        pass

    @api.model
    def _get_tax_price_included(self, taxes):
        price_include = all([tax.price_include for tax in taxes])

        if not price_include and any([tax.price_include for tax in taxes]):
            raise ApiImportError(_('One line has different Included In Price parameter in Taxes'))

        return price_include

    def _create_discount_line(self, integration, order, discount_tax_incl, discount_tax_excl):
        if not discount_tax_incl or not discount_tax_excl:
            return

        if not integration.discount_product_id:
            raise ApiImportError(_('Select Discount Product in Sale Integration'))

        precision = self.env['decimal.precision'].precision_get('Product Price')

        discount_tax_incl = discount_tax_incl * -1
        discount_tax_excl = discount_tax_excl * -1
        discount_taxes = discount_tax_incl - discount_tax_excl

        discount_line = self.env['sale.order.line'].create({
            'product_id': integration.discount_product_id.id,
            'order_id': order.id,
        })

        discount_line.product_id_change()

        # Discount without taxes
        if float_is_zero(discount_taxes, precision_digits=precision):
            discount_line.price_unit = discount_tax_excl
            discount_line.tax_id = False
            return

        # if all taxes on product lines are the same then set tax from product line
        product_lines = order.order_line.filtered(
            lambda x: x.tax_id and not x.is_delivery and x.id != discount_line.id
        )

        if product_lines:
            if all(product_lines[0].tax_id == x.tax_id for x in product_lines):
                discount_line.tax_id = product_lines[0].tax_id

        price_tax_included = self._get_tax_price_included(discount_line.tax_id)

        if price_tax_included:
            discount_line.price_unit = discount_tax_incl
        else:
            discount_line.price_unit = discount_tax_excl

        # Discount with taxes and was created correct
        if float_compare(discount_line.price_tax, discount_taxes, precision_digits=precision) == 0:
            return

        # The calculated taxes do not match the value from E-Commerce System
        # Try to pick up the values of discount with taxes
        discount_line.price_unit = (
            discount_line.price_unit * discount_taxes / discount_line.price_tax
        )

        difference = discount_line.price_tax - discount_taxes

        min_price = 10 ** (-1 * precision)

        # If difference = 1 cent try to plus/minus several cents to make the values the same
        # It may happened when taxes >50%
        if float_compare(abs(difference), min_price, precision_digits=precision) == 0:
            for x in range(10):
                discount_line.price_unit -= difference

                if float_compare(
                    discount_line.price_tax,
                    discount_taxes,
                    precision_digits=precision
                ) == 0:
                    break

        # # If taxes are still wrong then delete discount
        # if float_compare(discount_line.price_tax, discount_taxes, precision_digits=precision)!=0:
        #     discount_line.unlink()
        #     _logger.warning('Failed discount creation in Sale Order ID %s ' % order.id)
        #     return

        # If taxes are correct then create another one line without taxes
        discount_line2 = self.env['sale.order.line'].create({
            'product_id': integration.discount_product_id.id,
            'order_id': order.id,
        })

        discount_line2.product_id_change()
        discount_line2.tax_id = False
        discount_line2.price_unit = discount_tax_incl - discount_line.price_total

    def _add_payment_transactions(self, order, integration, payment_transactions):
        if not payment_transactions or not integration.import_payments:
            return
        # In Odoo standard it is not possible to add payments to sales order
        # So we are checking if special field exists for this
        # for now we allow to work with this OCA module
        # https://github.com/OCA/sale-workflow/tree/15.0/sale_advance_payment
        # TODO: Integrate functionality in integration module
        if 'account_payment_ids' not in self.env['sale.order']._fields:
            return

        precision = self.env['decimal.precision'].precision_get('Product Price')
        for transaction in payment_transactions:
            # we skip zero transaction as they doesn't make sense
            if float_is_zero(transaction['amount'], precision_digits=precision):
                _logger.warning(_('Order % was received with payment amount equal to 0.0. '
                                  'Skipping payment attachment to the order') % order.name)
                continue
            if not transaction['transaction_id']:
                _logger.warning(_('Order % payment doesn\'t have transaction id specified.'
                                  ' Skipping payment attachment to the order') % order.name)
                continue

            # Currency is not required field for transaction,
            # so we calculate it either from pricelist
            # or from company related to SO
            # And then try to get it from received SO
            currency_id = order.pricelist_id.currency_id.id or order.company_id.currency_id.id
            if transaction.get('currency'):
                odoo_currency = self.env['res.currency'].search([
                    ('name', '=ilike', transaction['currency'].lower()),
                ], limit=1)
                if not odoo_currency:
                    raise ApiImportError(
                        _('Currency ISO code "%s" was not found in Odoo.') % transaction['currency']
                    )
                currency_id = odoo_currency.id

            # Get Payment journal based on the payment method
            external_payment_method = order.payment_method_id.to_external_record(integration)

            if not external_payment_method.payment_journal_id:
                raise UserError(
                    _('No Payment Journal defined for Payment Method "%s". '
                      'Please, define it in menu "e-Commerce Integration -> Auto-Workflow -> '
                      'Payment Methods" in the "Payment Journal" column')
                    % order.payment_method_id.name
                )
            payment_vals = {
                "date": transaction['transaction_date'],
                "amount": abs(transaction['amount']),  # can be negative, so taking absolute value
                "payment_type": 'inbound' if transaction['amount'] > 0.0 else 'outbound',
                "partner_type": "customer",
                "ref": transaction['transaction_id'],
                "journal_id": external_payment_method.payment_journal_id.id,
                "currency_id": currency_id,
                "partner_id": order.partner_invoice_id.commercial_partner_id.id,
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"  # TODO: set smth else
                ).id,
            }

            payment_obj = self.env["account.payment"]
            payment = payment_obj.create(payment_vals)
            order.account_payment_ids |= payment
            payment.action_post()

    @api.model
    def _get_payment_method(self, integration, ext_payment_method):
        PaymentMethod = self.env['sale.order.payment.method']

        payment_method = PaymentMethod.from_external(
            integration, ext_payment_method, raise_error=False)

        if not payment_method:
            payment_method = PaymentMethod.search([
                ('name', '=', ext_payment_method),
                ('integration_id', '=', integration.id),
            ])

            if not payment_method:
                payment_method = PaymentMethod.create({
                    'integration_id': integration.id,
                    'name': ext_payment_method,
                })

            self.env['integration.sale.order.payment.method.mapping'].create_integration_mapping(
                integration, payment_method, ext_payment_method)

        return payment_method

    def _apply_shipping_tax(self, integration, order_data, order):
        delivery_line = order.order_line.filtered(lambda line: line.is_delivery)

        taxes = self.env['account.tax']

        for tax_code in order_data.get('shipping_tax', []):
            taxes |= self._retrieve_from_external(integration, tax_code)

        delivery_line.write({
            'tax_id': [(6, 0, taxes.ids)],
        })

    def _retrieve_from_external(self, integration, tax_code):
        tax = self.env['account.tax'].from_external(
            integration,
            tax_code,
        )
        return tax
