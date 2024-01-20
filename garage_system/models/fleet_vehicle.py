# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    customer_id = fields.Many2one('res.partner')
    workshop_count = fields.Integer(string='Job Cards', compute='_compute_workshop_id')

    # This _sql_constraints of code defines for a model field, indicating that the 'license_plate' field must be unique across records.
    _sql_constraints = [('fleet_license_plate_unique', 'unique(license_plate)', 'License Plate Already exist with this number')]
    
    # Computes 'workshop_count' based on related job cards for each order.
    @api.depends('model_id', 'customer_id')
    def _compute_workshop_id(self):
        for order in self:
            workshop_ids = self.env['job.card'].search([('fleet_id', '=', order.id)])
            order.workshop_count = len(workshop_ids)

    
    # Opens a view displaying related job cards for the current fleet.
    def button_view_repair(self):
        context = dict(self._context or {})
        repair_order_ids = self.env['job.card'].search([('fleet_id', '=', self.id)])
        return {
            'name': _('Job Cards'),
            'binding_view_types': 'form',
            'view_mode': 'tree,form',
            'res_model': 'job.card',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', repair_order_ids.ids)],
            'context': context,
        }
