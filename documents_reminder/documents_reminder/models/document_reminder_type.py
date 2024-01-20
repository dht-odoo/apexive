# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command


class ReminderDocumentType(models.Model):
    _name = "reminder.document.type"
    _description = "Reminder Document Type"

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=False,
        string="Company",
    )
    name = fields.Char(copy=False)
    image = fields.Binary()
    reminder_document_type_notify_ids = fields.Many2many(
        'reminder.document.type.notify', 'reminder_document_type_notify_default_rel',
        'reminder_document_type_id', 'reminder_document_type_notify_id',
        string='Notify Before Days')
