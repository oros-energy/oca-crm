# Copyright 2015 Antiun Ingenieria S.L. - Javier Iniesta
# Copyright 2018 ForgeFlow, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import Command, api, exceptions, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    industry_id = fields.Many2one(
        comodel_name="res.partner.industry",
        string="Main Industry",
        compute="_compute_industry_id",
        store=True,
        readonly=False,
    )

    secondary_industry_ids = fields.Many2many(
        comodel_name="res.partner.industry",
        string="Secondary Industries",
        domain="[('id', '!=', industry_id)]",
        compute="_compute_secondary_industry_ids",
        store=True,
        readonly=False,
    )

    @api.constrains("industry_id", "secondary_industry_ids")
    def _check_industries(self):
        for lead in self:
            if lead.industry_id in lead.secondary_industry_ids:
                raise exceptions.UserError(
                    self.env._(
                        "The secondary industries must be different from the"
                        " main industry."
                    )
                )

    def _prepare_industry_values(self):
        return {
            "industry_id": self.industry_id.id,
            "secondary_industry_ids": [(6, 0, self.secondary_industry_ids.ids)],
        }

    def _prepare_customer_values(self, partner_name, parent_id=False):
        """Propagate industries in the creation of partner."""
        values = super()._prepare_customer_values(partner_name, parent_id=parent_id)
        values.update(self._prepare_industry_values())
        return values

    def _create_customer(self):
        """Propagate industries to the company created from the lead."""
        new_company = not self.partner_id and self.partner_name
        partner = super()._create_customer()
        if new_company and partner.parent_id:
            partner.parent_id.write(self._prepare_industry_values())
        return partner

    @api.depends("partner_id")
    def _compute_industry_id(self):
        for record in self:
            if record.partner_id and record.partner_id.industry_id:
                record.industry_id = record.partner_id.industry_id
            else:
                record.industry_id = False

    @api.depends("partner_id")
    def _compute_secondary_industry_ids(self):
        for record in self:
            if record.partner_id and record.partner_id.secondary_industry_ids:
                record.secondary_industry_ids = record.partner_id.secondary_industry_ids
            else:
                record.secondary_industry_ids = [Command.clear()]
