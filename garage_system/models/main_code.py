# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MainCode(models.Model):
    _name = "main.code"

    name = fields.Char()
