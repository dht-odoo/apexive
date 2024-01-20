# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions


class ResPartner(models.Model):
    _inherit = "res.partner"

    code = fields.Char(string="Code")
    first_contract_date = fields.Date()
    last_services_jobcard_id = fields.Char()
    last_visit_date = fields.Date()
    max_discount = fields.Float(string="Max Discount")
    vehicle_count = fields.Integer(string='Vehicles', compute='_compute_vehicle')
    workshop_count = fields.Integer(string='Job Cards', compute='_compute_workshop_id')

    # Computes the 'workshop_count' based on related job cards.
    @api.depends('name')
    def _compute_workshop_id(self):
        for rec in self:
            workshop_ids = self.env['job.card'].search([('client_id', '=', rec.id)])
            rec.workshop_count = len(workshop_ids)

    # Computes the 'vehicle_count' based on related fleet vehicles.
    @api.depends('name')
    def _compute_vehicle(self):
        for order in self:
            vehicle_ids = self.env['fleet.vehicle'].search([('customer_id', '=', order.id)])
            order.vehicle_count = len(vehicle_ids)

    # Define an action to view repair orders related to the client
    def button_view_repair(self):
        context = dict(self._context or {})
        repair_order_ids = self.env['job.card'].search([('client_id', '=', self.id)])
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

    # Opens a view displaying related job cards for the current client.
    def button_view_fleet(self):
        context = dict(self._context or {})
        fleet_ids = self.env['fleet.vehicle'].search([('customer_id', '=', self.id)])
        return {
            'name': _('Fleet Vehicles'),
            'binding_view_types': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fleet.vehicle',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', fleet_ids.ids)],
            'context': context,
        }

    # Override name_get
    def (self):
        res = []
        for record in self:
            name = record.name
            if record.mobile:
                name = name + ' / ' + record.mobile
            res.append((record.id, name))
        return res

    # Override _name_search
    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        if name:
            fleet_vehicle_rec = self.env['fleet.vehicle'].search([('license_plate','ilike', name)]).mapped('customer_id.name')
            args += ['|', '|', '|',('name', operator, name), ('phone', operator, name), ('mobile', operator, name), ('name', 'in', fleet_vehicle_rec)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
