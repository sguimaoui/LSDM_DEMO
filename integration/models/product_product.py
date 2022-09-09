# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from ..exceptions import NotMappedToExternal

import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'integration.model.mixin']
    _internal_reference_field = 'default_code'

    product_variant_image_ids = fields.One2many(
        comodel_name='product.image',
        inverse_name='product_variant_id',
        string='Extra Variant Images',
    )

    variant_extra_price = fields.Float(
        string='Variant Extra Price',
        digits='Product Price',
    )

    integration_ids = fields.Many2many(
        comodel_name='sale.integration',
        relation='sale_integration_product_variant',
        column1='product_id',
        column2='sale_integration_id',
        domain=[('state', '=', 'active')],
        string='Sales Integrations',
        copy=False,
        default=lambda self: self._prepare_default_integration_ids(),
        help='Allow to select which channel this product should be synchronized to. '
             'By default it syncs to all.',
    )

    @api.model
    def create(self, vals_list):
        # We need to avoid calling export separately
        # from product.template and product.product
        ctx = dict(self.env.context, from_product_product=True, from_product_create=True)
        from_product_template = ctx.pop('from_product_template', False)

        if from_product_template:
            template = self.product_tmpl_id.browse(
                vals_list.get('product_tmpl_id')
            )
            if template.integration_ids:
                vals_list['integration_ids'] = [(6, 0, template.integration_ids.ids)]

        products = super(ProductProduct, self.with_context(ctx)).create(vals_list)

        if not from_product_template:
            export_images = self._need_export_images(vals_list)
            products.mapped('product_tmpl_id').trigger_export(export_images=export_images)

        return products

    def write(self, vals):
        # We need to avoid calling export separately
        # from product.template and product.product
        ctx = dict(self.env.context, from_product_product=True)
        from_product_template = ctx.pop('from_product_template', False)

        result = super(ProductProduct, self.with_context(ctx)).write(vals)

        if not from_product_template:
            export_images = self._need_export_images(vals)
            self.mapped('product_tmpl_id').trigger_export(export_images=export_images)

        return result

    def export_images_to_integration(self):
        return self.product_tmpl_id.export_images_to_integration()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        form_data = super().fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )

        if view_type == 'search':
            form_data = self._update_variant_form_architecture(form_data)

        return form_data

    def change_external_integration_variant(self):
        templates = self.mapped('product_tmpl_id')
        return templates.change_external_integration_template()

    @api.model
    def _need_export_images(self, vals_list):
        return self._check_fields_changed(
            [
                'image_1920',
                'product_variant_image_ids',
            ],
            vals_list
        )

    def to_export_format(self, integration):
        self.ensure_one()

        try:
            product_external_code = self.to_external(integration)
        except NotMappedToExternal:
            product_external_code = None

        # attributes
        attribute_values = []
        for attribute_value in self.product_template_attribute_value_ids:
            value = attribute_value.product_attribute_value_id.\
                to_export_format_or_export(integration)

            attribute_values.append(value)

        result = {
            'id': self.id,
            'external_id': product_external_code,
            'attribute_values': attribute_values,
        }

        search_domain = self._variant_ecommerce_field_domain(integration, product_external_code)

        for field in self.env['product.ecommerce.field.mapping'].\
                search(search_domain).mapped('ecommerce_field_id'):
            result[field.technical_name] = integration.calculate_field_value(self, field)

        return result

    def get_used_in_kits_recursively(self):
        tmpl = self.env['product.template']

        if not self.mrp_enabled:
            return tmpl

        kits = self.env['mrp.bom'].search([
            ('bom_line_ids.product_id', 'in', self.ids),
            ('type', '=', 'phantom'),
        ])

        if not kits:
            return tmpl

        return (
            kits.product_tmpl_id
            + kits.product_tmpl_id.product_variant_ids.get_used_in_kits_recursively()
        )

    @api.depends('product_template_attribute_value_ids.price_extra', 'variant_extra_price')
    def _compute_product_price_extra(self):
        super(ProductProduct, self)._compute_product_price_extra()

        for product in self:
            product.price_extra += product.variant_extra_price

    def _variant_ecommerce_field_domain(self, integration, external_code):
        search_domain = [
            ('integration_id', '=', integration.id),
            ('odoo_model_id', '=', self.env.ref('product.model_product_product').id),
        ]
        if external_code:
            search_domain.append(('send_on_update', '=', True))

        return search_domain

    def _update_variant_form_architecture(self, form_data):
        return self.product_tmpl_id._update_template_form_architecture(form_data)
