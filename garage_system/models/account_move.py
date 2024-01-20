# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = "account.move"

    chassis_number = fields.Char(related="fleet_id.vin_sn", store=True)
    cost = fields.Float(string="Total Cost" ,compute='_compute_total_cost_amt', store=True ,readonly=True)
    fleet_id = fields.Many2one('fleet.vehicle','Fleet', required=False)
    fts_payment_type = fields.Selection([('cash', 'CASH'),
                            ('credit', 'CREDIT'),
                            ], copy=False, string="Payment Type")
    invoice_date = fields.Date(
        string='Invoice/Bill Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
        copy=False,
        default=lambda self: fields.Date.context_today(self)
    )
    job_card_id = fields.Many2one('job.card', string='Job Card', readonly=True)
    license_plate = fields.Char(related="fleet_id.license_plate", store=True)
    last_odometer = fields.Float()
    total_discount_amt = fields.Float(string='Total Discount Amount', compute='_compute_total_discount_amt', store=True ,readonly=True)

    # Updates last_odometer value based on fleet_id onchange
    @api.onchange('fleet_id', 'fleet_id')
    def onchange_fleet_id(self):
        for rec in self:
            if rec.fleet_id:
                rec.last_odometer = rec.fleet_id.odometer
            else:
                rec.last_odometer = False

    # Updates invoice_user_id field based on partner_id
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            rec.fleet_id = False
            if rec.partner_id:
                rec.invoice_user_id = rec.partner_id.user_id

    # Extends default create; updates fleet odometer if 'last_odometer' is provided.
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'last_odometer' in vals :
            res.fleet_id.odometer = vals.get('last_odometer')
        return res

    # Extends default write; updates fleet odometer if 'last_odometer' is provided.
    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        if 'last_odometer' in vals :
            self.fleet_id.odometer = vals.get('last_odometer')
        return res

    # Computes 'total_discount_amt' based on the sum of discount amounts from related invoice lines.
    @api.depends('name', 'invoice_line_ids.discount_amt', 'invoice_line_ids')
    def _compute_total_discount_amt(self):
        for rec in self:
            rec.total_discount_amt = sum(rec.invoice_line_ids.mapped('discount_amt'))

    # Computes 'total_cost_amt' based on the sum of total amounts from related invoice lines.
    @api.depends('name', 'invoice_line_ids.cost', 'invoice_line_ids')
    def _compute_total_cost_amt(self):
        for rec in self:
            rec.cost = sum(rec.invoice_line_ids.mapped('cost'))


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cost = fields.Float()
    discount_amt = fields.Float(string='Discount Amt')
    product_parts_services_id = fields.Many2one('product.parts.services', string='Product Parts Services', readonly=True)

    # Calculates default discount in percentage based on discout_amt
    @api.onchange('discount_amt', 'price_unit', 'quantity')
    def _onchange_discount_amount(self):
        if self.price_unit and self.discount_amt:
            self.discount = (self.discount_amt / (self.price_unit * self.quantity)) * 100
        else:
            self.discount = 0

    # This onchange method is triggered when the 'partner_id' field is changed.
    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.cost = rec.product_id.standard_price
