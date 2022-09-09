# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class IntegrationProductAttributeValueExternal(models.Model):
    _name = 'integration.product.attribute.value.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Product Attribute Value External'

    external_attribute_id = fields.Many2one(
        comodel_name='integration.product.attribute.external',
        string='External Attribute',
        readonly=True,
        ondelete='cascade',
    )

    @api.model
    def fix_unmapped(self, integration):
        self._fix_unmapped_element(integration, 'attribute')

    def _post_import_external_one(self, adapter_external_record):
        self._post_import_external_element(adapter_external_record, 'attribute')
