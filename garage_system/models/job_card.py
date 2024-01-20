# -*- coding: utf-8 -*-
# Part of Preciseways See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools,_
from datetime import date, time, datetime
from odoo.exceptions import UserError, ValidationError,Warning

# List of fuel types.
FUEL_TYPES = [
    ('diesel', 'Diesel'),
    ('gasoline', 'Gasoline'),
    ('full_hybrid', 'Full Hybrid'),
    ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
    ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'),
    ('cng', 'CNG'),
    ('lpg', 'LPG'),
    ('hydrogen', 'Hydrogen'),
    ('electric', 'Electric'),
]


class JobCard(models.Model):
    _name = 'job.card'
    _rec_name = 'name'
    _inherit = ['mail.thread']
    _description = "Job Card"
    _order = 'id desc'

    name = fields.Char(required=True, copy=False)
    client_id = fields.Many2one('res.partner', 'Customer', required=True)
    contact_name = fields.Char()
    mobile = fields.Char()
    phone = fields.Char()
    email = fields.Char()
    user_id = fields.Many2one('res.users', 'Sales Person', required=True)
    mechanic_id = fields.Many2one('res.users')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('in_process', 'In Process'),
            ('worksheet_done', 'Process Done'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')], 'Status', default="draft", readonly=True, copy=False, help="Gives the status of the fleet Inspection.")
    receipt_date = fields.Date('Date Opened')
    date_closed = fields.Date('Promise Date')
    priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority')
    comment = fields.Text()
    fleet_id = fields.Many2one('fleet.vehicle','Fleet') 
    license_plate = fields.Char(compute="_compute_fleet", store=True)
    chassis_number = fields.Char(compute="_compute_fleet", store=True)
    model_id = fields.Many2one('fleet.vehicle.model', compute="_compute_fleet", store=True)
    fuel_type= fields.Selection(FUEL_TYPES, 'Fuel Type', help='Fuel Used by the vehicle', compute="_compute_fleet", store=True)
    registration_number = fields.Char()
    last_odometer = fields.Float()
    product_parts_services_ids = fields.One2many('product.parts.services', 'job_card_id')
    consumable_product_parts_services_ids = fields.One2many('product.parts.services', 'job_card2_id')
    total_cost = fields.Float(compute="_compute_amount", store=True)
    total_sale_price = fields.Float(compute="_compute_amount", store=True)
    saleorder_count = fields.Integer(compute="_compute_order_counts")
    purchaseorder_count = fields.Integer(compute="_compute_order_counts")
    invoice_count = fields.Integer(compute="_compute_order_counts")
    vendor_bill_count = fields.Integer(compute="_compute_order_counts")
    worksheet_ids = fields.One2many('job.card.worksheet', 'job_card_id', string='Worksheets')
    worksheet_count = fields.Integer(string='Work Sheet', compute='_compute_order_counts')
    invoice_created = fields.Boolean(compute="_compute_order_counts")
    purchase_order_created = fields.Boolean()
    vat = fields.Char(readonly=True)
    first_contract_date = fields.Date(related="client_id.first_contract_date")
    fts_payment_type = fields.Selection([('cash', 'CASH'),
                            ('credit', 'CREDIT'),
                            ], copy=False, string="Payment Type")


    # This _sql_constraints of code defines for a model field, indicating that the 'job_card' field must be unique across records.
    _sql_constraints = [('job_card_name_unique', 'unique(name)', 'Job Card Already exist with this name')]

    # Sets the default value for 'receipt_date' to the current datetime during record creation.
    @api.model
    def default_get(self, fields):
        res = super(JobCard, self).default_get(fields)
        res['receipt_date'] = datetime.now()
        return res

    # Sets the default value for 'receipt_date' to the current datetime during record creation.
    @api.depends('name', 'state', 'product_parts_services_ids')
    def _compute_order_counts(self):
        for rec in self:
            rec.saleorder_count = len(self.env['sale.order'].search([('job_card_id', '=', rec.id)]))
            rec.purchaseorder_count = len(self.env['purchase.order'].search([('job_card_id', '=', rec.id)]))
            rec.invoice_count = len(self.env['account.move'].search([('job_card_id', '=', rec.id), ('move_type', '=', 'out_invoice')]))
            rec.vendor_bill_count = len(self.env['account.move'].search([('job_card_id', '=', rec.id), ('move_type', '=', 'in_invoice')]))
            rec.worksheet_count = len(self.env['job.card.worksheet'].search([('job_card_id', '=', rec.id)]))
            rec.invoice_created = True if False not in rec.product_parts_services_ids.mapped('is_invoiced') else False
            rec.purchase_order_created = True

    # Computes and updates several fields based on the associated fleet information.
    @api.depends('fleet_id')
    def _compute_fleet(self):
        for rec in self:
            rec.license_plate = False
            rec.chassis_number = False
            rec.model_id = False
            rec.fuel_type = False
            # rec.vehicle_no = False
            # rec.registration_number = False
            if rec.fleet_id:
                rec.license_plate = rec.fleet_id.license_plate
                rec.chassis_number = rec.fleet_id.vin_sn
                rec.model_id = rec.fleet_id.model_id.id
                rec.fuel_type = rec.fleet_id.model_id.default_fuel_type
                # rec.vehicle_no = rec.fleet_id.vehicle_no
                # rec.registration_number = rec.fleet_id.registration_number

    # Computes 'total_cost' and 'total_sale_price'.
    @api.depends('consumable_product_parts_services_ids', 'product_parts_services_ids', 'invoice_count', 'saleorder_count', 'vendor_bill_count', 'state', 'invoice_created', 'purchase_order_created')
    def _compute_amount(self):
        for rec in self:
            total_cost =  sum(rec.consumable_product_parts_services_ids.mapped('standard_price'))
            total_cost += sum(self.env['account.move'].search([('job_card_id', '=', rec.id), ('move_type', '=', 'in_invoice'), ('state', 'not in', ['cancel'])]).mapped('amount_total'))
            rec.total_cost = total_cost
            rec.total_sale_price = sum(self.env['account.move'].search([('job_card_id', '=', rec.id), ('move_type', '=', 'out_invoice'), ('state', 'not in', ['draft', 'cancel'])]).mapped('amount_total'))

    # Updates various fields based on the selected client information.
    @api.onchange('client_id')
    def onchange_client_id(self):
        for rec in self:
            rec.fleet_id = False
            if rec.client_id:
                rec.phone = rec.client_id.phone
                rec.mobile = rec.client_id.mobile
                rec.email = rec.client_id.email
                rec.contact_name = rec.client_id.name
                rec.vat = rec.client_id.vat
                rec.first_contract_date = rec.client_id.first_contract_date
                rec.user_id = rec.client_id.user_id

    # Updates 'last_odometer' based on the selected fleet's odometer reading.            
    @api.onchange('fleet_id', 'fleet_id.odometer')
    def onchange_fleet_id(self):
        for rec in self:
            if rec.fleet_id:
                rec.last_odometer = rec.fleet_id.odometer
            else:
                rec.last_odometer = False

    # Override create method
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not vals.get('first_contract_date'):
            res.first_contract_date = res.receipt_date
            res.client_id.first_contract_date = res.receipt_date
            res.client_id.last_services_jobcard_id = res.name
        if 'last_odometer' in vals :
            res.fleet_id.odometer = vals.get('last_odometer')
        return res

    # Updates a record and performs additional actions, such as updating fleet odometer and client's last job card.
    def write(self, vals):
        res = super(JobCard, self).write(vals)
        if 'last_odometer' in vals :
            self.fleet_id.odometer = vals.get('last_odometer')
        if 'name' in vals :
            self.client_id.last_services_jobcard_id = vals.get('name')
        return res

    # Prepares data for plan lines based on input line information.
    def _prepare_plan_lines(self, line):
        return {
                'product_id': line.product_id.id or False,
                'name': line.product_id.name or ' ',
                'product_uom_qty': line.quantity or 1,
                'product_uom': line.uom_id.id or False,
                'price_unit' : line.price_unit or 0.0,
                'product_parts_services_id': line.id,
                'cost' : line.standard_price or 0.0
            }  

    # Creates a sale order based on the information from the current job card.
    def create_sale_order(self):
        lines = [(0, 0, self._prepare_plan_lines(line)) for line in self.product_parts_services_ids]
        quote_vals = {
            'partner_id': self.client_id.id or False,
            'state': 'draft',
            'job_card_id': self.id,
            'order_line' : lines,
            'user_id': self.user_id.id,
            'fleet_id': self.fleet_id.id,
            'fts_payment_type': self.fts_payment_type

        }
        order_id = self.env['sale.order'].create(quote_vals)
        return {
                'name': _('Sale order'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': order_id.id,
                # 'domain': [('diagnose_id', '=', self.id)],
        }

    # Opens a view displaying related sale orders for the current job card.
    def button_view_saleorder(self):
        context = dict(self._context or {})
        return {
            'name': _('Sale'),
            'binding_view_types': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('job_card_id', '=', self.id)],
            'context': context,
        }

    # Prepares data for purchase order lines based on input line information.
    def _prepare_purchase_order_lines(self, line):
        return {
                'product_id': line.product_id.id or False,
                'name': line.product_id.name or ' ',
                'product_uom_qty': line.quantity or 1,
                'product_uom': line.uom_id.id or False,
                'price_unit' : line.price_unit or 0.0,
                'product_parts_services_id': line.id
            }

    # Creates a purchase order based on non-service product lines from the current job card.
    def create_purchase_order(self):
        lines = [(0, 0, self._prepare_purchase_order_lines(line)) for line in self.product_parts_services_ids.filtered(lambda line: not line.is_service)]
        quote_vals = {
            'partner_id': self.client_id.id or False,
            'state': 'draft',
            'job_card_id': self.id,
            'order_line' : lines
        }
        order_id = self.env['purchase.order'].create(quote_vals)
        return {
            'name': _('Purchase order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': order_id.id,
            # 'domain': [('product_id','=',self.id)],
        }

    # Opens a view displaying related purchase orders for the current job card.
    def button_view_purchase_order(self):
        context = dict(self._context or {})
        return {
            'name': _('Purchase Order'),
            'binding_view_types': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('job_card_id', '=', self.id)],
            'context': context,
        }

    # Prepares invoice lines based on non-invoiced product lines from the current job card.
    @api.model
    def _prepare_invoce_lines(self):
        line_ids = []
        for line in self.product_parts_services_ids:
            if not line.is_invoiced:
                line.is_invoiced = True
                line_ids.append((0, 0, {
                    'product_parts_services_id': line.id,
                    'product_id': line.product_id.id or False,
                    'quantity': line.quantity or 1.0,
                    'product_uom_id': line.uom_id.id or False,
                    'price_unit' : line.price_unit or 0.0,
                    'cost' : line.standard_price or 0.0,
                }))
        return line_ids

    # Creates an invoice based on non-invoiced product lines from the current job card.   
    def create_invoice(self):
        lines = self._prepare_invoce_lines()
        vals = {'partner_id':self.client_id.id,'job_card_id': self.id, 'ref' :self.name,'move_type':'out_invoice','invoice_line_ids':lines,'fleet_id' : self.fleet_id.id,'fts_payment_type' : self.fts_payment_type,}
        invoice_id = self.env['account.move'].create(vals)
        return {
            'name': _('Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'res_id': invoice_id.id,
            'type': 'ir.actions.act_window',
        }

    # Opens a view displaying related account invoices for the current job card.
    def action_view_invoice(self):
        return {
            'name': _('Account Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('job_card_id', '=', self.id),  ('move_type', '=', 'out_invoice')],
        }

    # Opens a view displaying related vendor bills for the current job card.
    def action_view_vendor_bill(self):
        return {
            'name': _('Vendor Bills'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('job_card_id', '=', self.id),  ('move_type', '=', 'in_invoice')],
        }

    # Creates a worksheet based on the information from the current job card.
    def create_worksheet(self):
        for rec in self:
            wo_vals = {
                'name': rec.name,
                'job_card_id': rec.id,
                'client_id': rec.client_id.id or False,
                'priority': rec.priority,
                'state': 'draft',
                'mechanic_id': rec.mechanic_id.id or False,
                'date_planned': rec.receipt_date,
                'date_planned_end': rec.date_closed,
                'product_parts_services_ids': [(6, 0, rec.product_parts_services_ids.ids)] if rec.product_parts_services_ids else False,
                'consumable_product_parts_services_ids': [(6, 0, rec.consumable_product_parts_services_ids.ids)] if rec.consumable_product_parts_services_ids else False,
            }
        
        work_order_id = self.env['job.card.worksheet'].create(wo_vals)
    
        return {
            'name': _('Worksheet'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'job.card.worksheet',
            'res_id': work_order_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    # Opens a view displaying related work orders for the current job card.
    def button_view_worksheet(self):
        context = dict(self._context or {})
        work_order_ids = self.env['job.card.worksheet'].search([('job_card_id', '=', self.id)])
        return {
            'name': _('Work Order'),
            'binding_view_types': 'form',
            'view_mode': 'tree,form',
            'res_model': 'job.card.worksheet',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', work_order_ids.ids)],
            'context': context,
        }

    # Create a stock picking for stock adjustments, including moves for consumable products and non-service product parts
    def stock_adjustments(self):
        group_id = self.env['procurement.group'].create({'name': self.name, 'move_type': 'direct'})
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)])
        stock_picking_id = self.env['stock.picking'].create({
                'picking_type_id': warehouse_id.out_type_id.id,
                'partner_id': self.client_id.id,
                'user_id': self.user_id.id,
                'date': fields.Datetime.now(),
                'origin': self.name,
                'location_id': warehouse_id.out_type_id.default_location_src_id.id,
                'location_dest_id': self.client_id.property_stock_customer.id,
                'company_id': self.env.company.id,
                'job_card_id': self.id,
            })

        for line in self.consumable_product_parts_services_ids:
            if not line.product_id.type == 'service':
                move_values = {
                    'name': self.name,
                    'company_id': self.env.company.id,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'quantity_done': line.quantity,
                    'partner_id': self.client_id.id,
                    'location_id': warehouse_id.out_type_id.default_location_src_id.id,
                    'location_dest_id': self.client_id.property_stock_customer.id,
                    'procure_method': 'make_to_order',
                    'origin': self.name,
                    'picking_type_id': warehouse_id.out_type_id.id,
                    'group_id': group_id.id,
                    'warehouse_id': warehouse_id.id,
                    'date': fields.Datetime.now(),
                    'picking_id': stock_picking_id.id,
                }

                move = self.with_context(default_picking=stock_picking_id.id).env['stock.move'].create(move_values)

        for line in self.product_parts_services_ids:
            if not line.is_service and line.delivery_state == 'pending':
                move_values = {
                    'name': self.name,
                    'company_id': self.env.company.id,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'quantity_done': line.quantity,
                    'partner_id': self.client_id.id,
                    'location_id': warehouse_id.out_type_id.default_location_src_id.id,
                    'location_dest_id': self.client_id.property_stock_customer.id,
                    'procure_method': 'make_to_order',
                    'origin': self.name,
                    'picking_type_id': warehouse_id.out_type_id.id,
                    'group_id': group_id.id,
                    'warehouse_id': warehouse_id.id,
                    'date': fields.Datetime.now(),
                    'picking_id': stock_picking_id.id,
                }

                move = self.with_context(default_picking=stock_picking_id.id).env['stock.move'].create(move_values)

        stock_picking_id.action_confirm()
        stock_picking_id.button_validate()

    # Updates state to confirm
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    # Updates state to done and do stock adjustment
    def action_done(self):
        for rec in self:
            rec.state = 'done'
            rec.stock_adjustments()

    # Updates state to cancel
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    # Updates state to draft
    def action_move_to_draft(self):
        for rec in self:
            rec.state = 'draft'

class ProductPartsServices(models.Model):
    _name = 'product.parts.services'
    _description = "Spare Part Lines"
    _order = 'id desc'

    cost = fields.Float()
    default_code = fields.Char(string='Product Code')
    delivery_state = fields.Selection([
            ('pending', 'Pending Delivery'),
            ('partial', 'Partially Delivered'),
            ('delivered', 'Delivered')], 'Delivery Status', compute="_compute_delivery_state")
    delivered_quantity = fields.Float(string='Delivered Quantity')
    description = fields.Text()
    is_service = fields.Boolean(compute='_compute_is_service', store=True)
    is_invoiced = fields.Boolean()
    job_card_id = fields.Many2one('job.card', string='Job Card')
    job_card2_id = fields.Many2one('job.card', string='Job Card 2')
    job_card_worksheet_id = fields.Many2one('job.card.worksheet', string='Job Card Worksheet')
    job_card_worksheet2_id = fields.Many2one('job.card.worksheet', string='Job Card Worksheet 2')
    name = fields.Char(string='Description')
    price_unit = fields.Float(string='Unit Price')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])
    quantity = fields.Float(string='Quantity', required=True, default=1)
    standard_price = fields.Float(string='Cost')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")

    # Computes the 'delivery_state' based on the quantity and delivered quantity.
    @api.depends('quantity', 'delivered_quantity')
    def _compute_delivery_state(self):
        for rec in self:
            if rec.delivered_quantity == rec.quantity:
                rec.delivery_state = 'delivered'
            elif rec.delivered_quantity == 0:
                rec.delivery_state = 'pending'
            else:
                rec.delivery_state = 'partial'

    # Computes the 'is_service' field based on the product type.
    @api.depends('product_id')
    def _compute_is_service(self):
        for rec in self:
            rec.is_service = True if rec.product_id.type == 'service' else False

    # Updates certain fields based on the selected product.
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if self.product_id:
            res = {'default_code': self.product_id.default_code,
            'price_unit': self.product_id.lst_price,
            'standard_price': self.product_id.standard_price,
            'uom_id': self.product_id.uom_id}
        return {'value': res}
