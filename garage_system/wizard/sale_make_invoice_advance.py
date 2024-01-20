# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    # Override the _create_invoices method to set the job_card_id for each created invoice
    def _create_invoices(self, sale_orders):
        res = super(SaleAdvancePaymentInv, self)._create_invoices(sale_orders=sale_orders)
        for move in res:
            move.job_card_id = self.sale_order_ids.job_card_id.id
        return res
