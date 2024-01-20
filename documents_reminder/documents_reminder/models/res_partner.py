# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError

class Partner(models.Model):
    _inherit = "res.partner"

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=True,
        string="Company",
    )   
    is_notify_documents = fields.Boolean('Notify Documents', default=True, copy=False)
    reminder_document_ids = fields.One2many(
        'reminder.document', 'partner_id', string='Documents')
    responsible_partner_id = fields.Many2one('res.partner', 'Responsible')

    # Update the 'notify' field in related reminder documents based on the value of 'is_notify_documents'.
    @api.onchange('is_notify_documents')
    def _onchange_is_notify_documents(self):
        if self.is_notify_documents:
            self.reminder_document_ids.filtered(
                lambda a: not a.notify).write({'notify': True})
        else:
            self.reminder_document_ids.filtered(
                lambda a: a.notify).write({'notify': False})

    # Override create method to check if the total allowed partners for a company is reached before creating a new partner.
    @api.model
    def create(self, vals):
        if vals and vals.get('company_id'):
            partners = self.env['res.partner'].search([('company_id', '=', vals.get('company_id'))])
            company = self.env['res.company'].browse(vals.get('company_id'))
            if company.total_allowed_partners <= len(partners):
                raise ValidationError(_('You cannot create any more new contacts. Please contact the admin')) 
        return super(Partner, self).create(vals)
