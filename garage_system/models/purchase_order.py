# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    job_card_id = fields.Many2one('job.card', string='Job Card', readonly=True)

    # Updates the 'user_id' based on the selected partner.
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.user_id = rec.partner_id.user_id

    # Extends the action to view invoices and associates them with the job card.
    def action_view_invoice(self, invoices=False):
        if invoices and self.job_card_id:
            for move in invoices:
                move.job_card_id = self.job_card_id.id
        return super(PurchaseOrder, self).action_view_invoice(invoices=invoices)

    # Confirms the order, validates stock moves, and creates an invoice.
    def action_create_invoice_and_picking(self):
        self.button_confirm()
        for rec in self.picking_ids:
            for stock_move_line in rec.move_ids_without_package:
                stock_move_line.quantity_done = stock_move_line.product_uom_qty
            rec.button_validate()
        return self.action_create_invoice()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_parts_services_id = fields.Many2one('product.parts.services', string='Product Parts Services', readonly=True)
