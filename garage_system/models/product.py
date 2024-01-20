# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    code = fields.Char(string="Code")
    main_code_id = fields.Many2one('main.code', string="Main Code")
