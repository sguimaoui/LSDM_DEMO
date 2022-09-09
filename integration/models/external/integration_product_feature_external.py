# See LICENSE file for full copyright and licensing details.

from odoo import models, fields
from odoo.tools.sql import escape_psql
import logging

_logger = logging.getLogger(__name__)


class IntegrationProductFeatureExternal(models.Model):
    _name = 'integration.product.feature.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Product Feature External'

    external_feature_value_ids = fields.One2many(
        comodel_name='integration.product.feature.value.external',
        inverse_name='external_feature_id',
        string='External Feature Values',
        readonly=True,
    )

    def try_map_by_external_reference(self, odoo_model, odoo_search_domain=False):
        self.ensure_one()

        reference_field_name = getattr(odoo_model, '_internal_reference_field', None)

        odoo_id = odoo_model.from_external(
            self.integration_id,
            self.code,
            raise_error=False
        )
        if odoo_id:
            return

        odoo_object = None
        if self.name:
            odoo_object = odoo_model.search(
                [(reference_field_name, '=ilike', escape_psql(self.name))])
            if len(odoo_object) > 1:
                odoo_object = None

        odoo_model.create_or_update_mapping(self.integration_id, odoo_object, self)

    def run_import_features(self):
        return self._run_import_elements_element('feature')
