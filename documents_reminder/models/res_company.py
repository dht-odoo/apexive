# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    total_allowed_documents = fields.Integer(string='Total Allowed Documents', default=500)
    total_allowed_partners = fields.Integer(string="Total Allowed Partners", default=2500)
    total_documents = fields.Integer(string='Total Documents', compute="_compute_total")
    total_partners = fields.Integer(string='Total Partners' ,compute="_compute_total")

    # This method is decorated with @api.depends_context('uid') to depend on the user's context.
    @api.depends_context('uid')
    def _compute_total(self):
        for company in self:
            documents = company.env['reminder.document'].search([
                ('company_id', '=', company.id),
                ('notify', '=', True)
            ])
            company.total_documents = len(documents)
            partners = self.env['res.partner'].search([('company_id', '=', company.id)])
            company.total_partners = len(partners)
