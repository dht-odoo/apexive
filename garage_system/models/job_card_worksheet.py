# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date, time, datetime, timedelta

class JobCardWorksheet(models.Model):
    _name = "job.card.worksheet"
    _description ="Job Card Worksheet"
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    # Computes the planned end date based on planned date and hours.
    def get_planned_end_date(self):
        res = {}
        for wo_obj in self:
            if wo_obj.date_planned and wo_obj.hour:
                planned_date = datetime.strptime(wo_obj.date_planned, "%Y-%m-%d %H:%M:%S")
                planned_end_date = planned_date + timedelta(hours=wo_obj.hour)
                res[wo_obj.id] = planned_end_date
        return res

    client_id = fields.Many2one('res.partner', string='Client', required=True)
    consumable_product_parts_services_ids = fields.One2many('product.parts.services', 'job_card_worksheet2_id')
    date = fields.Date(string='Date', default=fields.Date.today())
    date_finished = fields.Datetime(string='End Date', )
    date_planned = fields.Datetime(string='Scheduled Date')
    date_planned_end =  fields.Date( string='End Date',)
    date_start = fields.Datetime(string='Start Date', readonly=True)
    delay = fields.Float(string='Working Hours', readonly=True)
    description = fields.Text(string='Fault Description')
    hour = fields.Float(string='Number of Hours')
    job_card_id = fields.Many2one('job.card')
    mechanic_id = fields.Many2one('res.users', string='Mechanic')
    name = fields.Char(string='Work Sheet', required=True)
    priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority')
    product_parts_services_ids = fields.One2many('product.parts.services', 'job_card_worksheet_id')
    state = fields.Selection([
        ('draft','Draft'),
        ('cancel','Cancelled'),
        ('pause','Pending'),
        ('startworking', 'In Progress'),
        ('done','Finished')],'Status', readonly=True, copy=False,
       help="* When a work order is created it is set in 'Draft' status.\n" \
               "* When user sets work order in start mode that time it will be set in 'In Progress' status.\n" \
               "* When work order is in running mode, during that time if user wants to stop or to make changes in order then can set in 'Pending' status.\n" \
               "* When the user cancels the work order it will be set in 'Canceled' status.\n" \
               "* When order is completely processed that time it is set in 'Finished' status.")

    # Updates related job card's product and consumable product lines.
    def write(self, vals):
        updated_product_parts_services_ids = vals.get('product_parts_services_ids')
        updated_consumable_product_parts_services_ids = vals.get('consumable_product_parts_services_ids')

        if updated_product_parts_services_ids or updated_consumable_product_parts_services_ids:
            if self.job_card_id:
                job_card = self.job_card_id
                if updated_product_parts_services_ids:
                    job_card.write({
                        'product_parts_services_ids': updated_product_parts_services_ids
                    })
                if updated_consumable_product_parts_services_ids:
                    job_card.write({
                        'consumable_product_parts_services_ids': updated_consumable_product_parts_services_ids
                    })
        return super(JobCardWorksheet, self).write(vals)

    # Cancels the current record.
    def button_cancel(self):
        self.write({'state': 'cancel'})

    # Resumes the current record, changing its state to 'startworking'.
    def button_resume(self):
        self.write({'state': 'startworking'})

    # Pauses the current record.
    def button_pause(self):
        self.write({'state': 'pause'})

    # Sets the current record to the 'draft' state.
    def button_draft(self):
        self.write({'state': 'draft'})

    # Sets state to 'startworking' and writes the starting date.
    def action_start_working(self):
        """ Sets state to start working and writes starting date.
        @return: True
        """
        self.write({'state':'startworking', 'date_start': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')})
        if self.job_card_id:
            self.job_card_id.state = 'in_process'
        return True

    # Sets state to 'done', writes finish date, and calculates delay.
    def action_done(self):
        """ Sets state to done, writes finish date and calculates delay.
        @return: True
        """
        delay = 0.0
        date_now = datetime.now()
        date_start = self.date_start
        date_finished = date_now   
        delay += (date_finished-date_start).days * 24
        delay += (date_finished-date_start).seconds / float(60*60)
        self.write({'state':'done', 'date_finished': date_now, 'delay':delay})
        if self.job_card_id:
            self.job_card_id.state = 'worksheet_done'
        return True
