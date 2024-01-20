# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command


class ReminderDocumentTypeNotify(models.Model):
    _name = "reminder.document.type.notify"
    _description = "Reminder Document Type Notify"
    _order = "days desc"

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=False,
        string="Company",
    )
    days = fields.Integer(copy=False)
    name = fields.Char(copy=False)

    # Overrides the default 'name_get' method to include 'days' in the display name if it is present.
    @api.depends('name', 'days')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.days:
                name = name + ' - ' + str(record.days)
            res.append((record.id, name))
        return res
