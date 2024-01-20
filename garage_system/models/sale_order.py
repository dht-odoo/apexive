# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cost = fields.Float(string="Total Cost" ,compute='_compute_total_cost_amt', store=True ,readonly=True)
    chassis_number = fields.Char(related="fleet_id.vin_sn", store=True)
    fleet_id = fields.Many2one('fleet.vehicle')
    fts_payment_type = fields.Selection([('cash', 'CASH'),
                            ('credit', 'CREDIT'),
                            ], copy=False, string="Payment Type")
    job_card_id = fields.Many2one('job.card', string='Job Card', readonly=True, copy=False)
    last_odometer = fields.Float()
    license_plate = fields.Char(related="fleet_id.license_plate", store=True)
    total_discount_amt = fields.Float(string='Total Discount Amount', compute='_compute_total_discount_amt', store=True, readonly=True )

    # Updates 'last_odometer' based on selected fleet.
    @api.onchange('fleet_id', 'fleet_id.odometer')
    def onchange_fleet_id(self):
        for rec in self:
            if rec.fleet_id:
                rec.last_odometer = rec.fleet_id.odometer
            else:
                rec.last_odometer = False

    # Resets 'fleet_id' and updates 'user_id' based on selected client.
    @api.onchange('client_id')
    def onchange_client_id(self):
        for rec in self:
            rec.fleet_id = False
            if rec.client_id:
                rec.user_id = rec.client_id.user_id

    # Override create method
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'last_odometer' in vals :
            res.fleet_id.odometer = vals.get('last_odometer')
        return res

    # Override write method
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'last_odometer' in vals :
            self.fleet_id.odometer = vals.get('last_odometer')
        return res

    # Computes 'total_discount_amt' based on order line discounts.
    @api.depends('name', 'order_line.discount_amt', 'order_line')
    def _compute_total_discount_amt(self):
        for rec in self:
            rec.total_discount_amt = sum(rec.order_line.mapped('discount_amt'))

    # Computes 'cost' based on order line costs.
    @api.depends('name', 'order_line.cost', 'order_line')
    def _compute_total_cost_amt(self):
        for rec in self:
            rec.cost = sum(rec.order_line.mapped('cost'))

    # Handles onchange for partner discount validation.
    @api.onchange('partner_id', 'total_discount_amt')
    def _onchange_discount(self):
        for rec in self:
            if rec.partner_id.max_discount and rec.total_discount_amt > rec.partner_id.max_discount:
                raise exceptions.ValidationError("Discount Cannot Exceed Max Discount {}%.".format(rec.partner_id.max_discount))

    # Extends invoice creation and sets additional fields.
    def _create_invoices(self, grouped=False, final=False, date=None):
        res = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final, date=date)
        for move in res:
            move.job_card_id = self.job_card_id.id
            move.fleet_id = self.fleet_id.id
            move.license_plate = self.license_plate
            move.chassis_number = self.chassis_number
            move.last_odometer = self.last_odometer
            move.fts_payment_type = self.fts_payment_type
        return res

    # Creates a job card based on the sale order data.
    def action_create_job_card(self):
        for rec in self:
            job_card_data = {'client_id': rec.partner_id.id, 'user_id': rec.user_id.id, 'name': 'JOB No: ' + rec.name}
            if rec.fleet_id:
                job_card_data.update({'fleet_id': rec.fleet_id.id})
            job_card_id = self.env['job.card'].create(job_card_data)
            rec.job_card_id = job_card_id
            for line_data in rec.order_line:
                self.env['product.parts.services'].create({
                    'product_id': line_data.product_id.id,
                    'quantity': line_data.product_uom_qty,
                    'uom_id': line_data.product_id.uom_id.id,
                    'price_unit': line_data.price_unit,
                    'job_card_id': job_card_id.id,
                    'standard_price' : line_data.cost or 0.0,
                })
            job_card_id.onchange_fleet_id()
            job_card_id.onchange_client_id()
            return {
                'name': _('Job Card'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'job.card',
                'res_id': job_card_id.id,
            }

    # Confirms the sale order, validates the picking, and creates invoices.
    def action_create_invoice_and_picking(self):
        self.action_confirm()
        for rec in self.picking_ids:
            for stock_move_line in rec.move_ids_without_package :
                stock_move_line.quantity_done = stock_move_line.product_uom_qty
            rec.button_validate()
        self._create_invoices()
        return {
            'name': 'account.move.form',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_ids[0].id,
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    cost = fields.Float()
    discount_amt = fields.Float(string="Discount Amt")
    product_parts_services_id = fields.Many2one('product.parts.services', string='Product Parts Services', readonly=True)

    # Calculate Discount Amount
    @api.onchange('discount_amt', 'price_unit', 'product_uom_qty')
    def _onchange_discountamt_topercentage(self):
        if self.price_unit and self.discount_amt:
            self.discount = (self.discount_amt / (self.price_unit * self.product_uom_qty)) * 100
        else:
            self.discount = 0

    # Extends preparation of invoice line data with custom fields.
    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['discount_amt'] = self.discount_amt
        res['cost'] = self.cost
        return res

    # Updates delivered quantity in related product parts/services.
    @api.onchange('qty_delivered', 'product_parts_services_id', 'qty')
    def _onchange_delivered_qty(self):
        if self.qty_delivered:
            self.product_parts_services_id.delivered_quantity = self.qty_delivered

    # Updates the cost based on the standard price of the selected product.
    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.cost = rec.product_id.standard_price
