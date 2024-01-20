# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command


class ReminderDocumentTag(models.Model):
    _name = "reminder.document.tag"
    _description = "Reminder Document Tag"

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=False,
        string="Company",
    )
    name = fields.Char(copy=False)
