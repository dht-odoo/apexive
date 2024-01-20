# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions


class StockPicking(models.Model):
    _inherit = "stock.picking"

    job_card_id = fields.Many2one('job.card', string='Job Card', readonly=True, copy=False)
