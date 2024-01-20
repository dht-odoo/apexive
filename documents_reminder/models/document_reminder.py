# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime, date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ReminderDocument(models.Model):
    _name = "reminder.document"
    _rec_name = 'reminder_document_type_id'
    _description = "Reminder Documents"

    copy_link = fields.Text(compute='_compute_copy_clipboard')
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="partner_id.company_id",
        store=True   
    )
    description = fields.Text(copy=False)
    document_link = fields.Text()
    document_number = fields.Char()
    document_one = fields.Binary('Document 1', copy=False)
    document_two = fields.Binary('Document 2', copy=False)
    expired_days = fields.Integer(compute="_compute_expired_days" , store=True)
    expiry_date = fields.Date(copy=False)
    last_reminder_date = fields.Date(copy=False)
    next_reminder_date = fields.Date(compute="_compute_next_reminder_date", store=True)
    notify = fields.Boolean(default=True, copy=False)
    partner_id = fields.Many2one('res.partner', 'Contact', required=True)
    reminder_document_type_id = fields.Many2one(
        'reminder.document.type', 'Document Type', copy=False)
    reminder_document_tag_ids = fields.Many2many(
        'reminder.document.tag', 'coderexpert_document_tag_default_rel',
        'reminder_document_id', 'tag_id', string='Tags')
    reminder_document_notify_ids = fields.Many2many(
        'reminder.document.type.notify', 'reminder_document_notify_default_rel',
        'reminder_document_id', 'reminder_document_type_notify_id',
        string='Notify Before Days')

    # Update the 'copy_link' field for each record based on the 'document_link' field value
    @api.depends('document_link')
    def _compute_copy_clipboard(self):
        for record in self:     
            record.copy_link = record.document_link

    # Check and restrict the creation of new documents reminder record based on the total_allowed_documents limit for the specified company.
    @api.model
    def create(self, vals):
        if vals and vals.get('company_id') and vals.get('partner_id'):
            partners = self.env['reminder.document'].search([('company_id', '=', vals.get('company_id'))])
            company = self.env['res.company'].browse(vals.get('company_id'))
            if company.total_allowed_documents <= len(partners):
                raise ValidationError(_('You cannot create any more new document reminder records. Please contact the admin')) 
        return super(ReminderDocument, self).create(vals)

    # Calculate the 'expired_days' field value based on the difference between 'expiry_date' and today's date.
    @api.depends('expiry_date')
    def _compute_expired_days(self):
        for partner_rec in self:
            expired_days = 0
            if partner_rec.expiry_date:
                expired_days = (partner_rec.expiry_date - fields.Date.today()).days
            partner_rec.expired_days = expired_days

    # Calculates the 'next_reminder_date' value.
    @api.depends('reminder_document_notify_ids', 'expiry_date', 'last_reminder_date')
    def _compute_next_reminder_date(self):
        for partner_rec in self:
            days = [notify.days for notify in partner_rec.reminder_document_notify_ids]
            if days and partner_rec.expiry_date:
                days.sort()
                diff = (partner_rec.expiry_date - partner_rec.last_reminder_date).days if partner_rec.last_reminder_date else 0
                if diff in days:
                    day = days.index(diff)
                    partner_rec.next_reminder_date = partner_rec.expiry_date - timedelta(days=days[day - 1]) if day != 0 else partner_rec.expiry_date
                else:
                    partner_rec.next_reminder_date = partner_rec.expiry_date - timedelta(days=days[-1])
            else:
                partner_rec.next_reminder_date = False

    # Update 'reminder_document_notify_ids' value based on 'reminder_document_type_id' onchange.
    @api.onchange('reminder_document_type_id')
    def _onchange_reminder_document_type_id(self):
        if self.reminder_document_type_id and self.reminder_document_type_id.reminder_document_type_notify_ids:
            self.write({'reminder_document_notify_ids': [(6, 0, self.reminder_document_type_id.reminder_document_type_notify_ids.ids)]})
        if not self.reminder_document_type_id:
            self.write({'reminder_document_notify_ids': [(5, 0, 0)]})

    # Update 'last_reminder_date' value and validate 'expiry_date' changes.
    @api.onchange('expiry_date')
    def _onchange_expiry_date(self):
        if self.expiry_date:
            self.last_reminder_date = False
        if self.expiry_date and self.expiry_date <= fields.Date.today():
            raise ValidationError(_('You cannot select current date or past date.'))

    # Send email reminders for documents with 'next_reminder_date' set to today and 'notify' flag enabled.
    def email_reminder(self):
        for document in self.env['reminder.document'].search([('next_reminder_date', '=', fields.Date.today()), ('notify', '=', True)]):
            template = self.env.ref('reminder_documents.mail_template_reminder_documents_email_reminder').sudo()
            template.send_mail(document.id)
            if document.partner_id.responsible_partner_id:
                template = self.env.ref('reminder_documents.mail_template_reminder_documents_email_reminder_responsible').sudo()
                template.send_mail(document.id)
            document.last_reminder_date = fields.Date.today()

    # This method, `get_document_data`, is a part of a dashboard and is designed to retrieve and organize document-related data in dashboard.
    @api.model
    def get_document_data(self):
        document_data = defaultdict(lambda: defaultdict(int))
        sections_data = {
            'document_type': 'Total',
            'Expired/Past Due': 0,
            '30 Days': 0,
            '7 Days': 0,
            'Total': 0
        }

        documents = self.search([
            ('company_id', '=', self.env.company.id),
            ('notify', '=', True)
        ])

        for document in documents:
            section = ''
            if document.expired_days < 0:
                section = 'Expired/Past Due'
            elif document.expired_days in range(1, 8):
                section = '7 Days'
            elif document.expired_days in range(8, 31):
                section = '30 Days'

            if not section:
                continue

            sections_data[section] += 1
            sections_data['Total'] += 1

            document_data[document.reminder_document_type_id.name][section] += 1
            document_data[document.reminder_document_type_id.name]['Total'] += 1
            document_data[document.reminder_document_type_id.name]['document_type'] = document.reminder_document_type_id.name

        document_data.update({'Total': sections_data})
        self.env.company.sudo()._compute_total()

        return {
            'document_data': list(document_data.values()),
            'sections_data': sections_data,
            'company_data': {
                'total_documents': self.env.company.total_documents,
                'total_allowed_documents': self.env.company.total_allowed_documents,
                'documents_percentage': round((self.env.company.total_documents / (self.env.company.total_allowed_documents or 1)) * 100, 2),
                'total_partners': self.env.company.total_partners,
                'total_allowed_partners': self.env.company.total_allowed_partners,
                'partners_percentage': round((self.env.company.total_partners / (self.env.company.total_allowed_partners or 1)) * 100, 2)
            }
        }


    # Method to generate an action opening a document form view for a single record.
    def action_open_document_form(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('documents_reminder.reminder_document_action')
        action.update({
            'view_mode': 'form',
            'view_id': self.env.ref('documents_reminder.reminder_document_form').id,
            'views': [(self.env.ref('documents_reminder.reminder_document_form').id, 'form')],
            'res_id': self.id,
        })
        return action
