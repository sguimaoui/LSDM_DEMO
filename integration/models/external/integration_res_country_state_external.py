# See LICENSE file for full copyright and licensing details.

from odoo import models, api

import logging
import re

_logger = logging.getLogger(__name__)


class IntegrationResCountryStateExternal(models.Model):
    _name = 'integration.res.country.state.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Res Country State External'

    def _get_state_domain(self, code, integration):
        state_domain = None
        # States should have external reference like {countrycode_statecode}
        # for example, 'US_CA'
        if not code or '_' not in code:
            return state_domain

        cleaned_code = re.sub(r'\(.*?\)', '', code)  # for example 'PL_PLL-30(123)' --> skip (123)
        country_code, state_code = cleaned_code.split('_')
        external_country = self.env['integration.res.country.external'].search([
            ('integration_id', '=', integration.id),
            ('external_reference', '=', country_code),
        ], limit=1)
        if external_country:
            odoo_country = self.env['res.country']\
                .from_external(external_country.integration_id,
                               external_country.code,
                               raise_error=False
                               )
            if odoo_country:
                state_domain = [
                    ('country_id', '=', odoo_country.id),
                    ('code', '=ilike', state_code),
                ]

        return state_domain

    def try_map_by_external_reference(self, odoo_model, odoo_search_domain=False):
        self.ensure_one()
        odoo_state = odoo_model.from_external(self.integration_id,
                                              self.code,
                                              raise_error=False)
        # If state is mapped, no need to go further
        if odoo_state:
            return
        state_domain = self._get_state_domain(self.external_reference, self.integration_id)
        if state_domain:
            super(IntegrationResCountryStateExternal, self).\
                try_map_by_external_reference(odoo_model, state_domain)

    @api.model
    def fix_unmapped(self, integration):
        # odoo has bug (depending on the version) that they use incorrect ISO Codes fro below states
        # [IN_UT] Uttarakhand -> in Odoo it is IN_UK
        # [IN_CT] Chhattisgarh -> in Odoo it is IN_CG
        # [IN_TG] Telangana -> in Odoo it is IN_TS
        # [MX_AGS] Aguascalientes -> in Odoo it is MX_AGU
        # Maybe in next versions Odoo will fix, but for now we have to have this method
        fixing_mapping = {
            'IN_UT': 'IN_UK',
            'IN_CT': 'IN_CG',
            'IN_TG': 'IN_TS',
            'MX_AGS': 'MX_AGU',
        }
        problematic_states = self.search([
            ('integration_id', '=', integration.id),
            ('external_reference', 'in', list(fixing_mapping.keys()))
        ])
        odoo_model = self.env['res.country.state']
        for problematic_state in problematic_states:
            odoo_value_code = fixing_mapping[problematic_state.external_reference]
            mapping = self.env['integration.res.country.state.mapping'].search([
                ('integration_id', '=', integration.id),
                ('external_state_id', '=', problematic_state.id),
            ], limit=1)

            # If state is mapped, or no mapping exists
            # No need to go further
            if not mapping or mapping.state_id:
                continue

            state_domain = self._get_state_domain(odoo_value_code, integration)
            if state_domain:
                odoo_state = odoo_model.search(state_domain, limit=1)
                if odoo_state:
                    mapping.state_id = odoo_state.id
