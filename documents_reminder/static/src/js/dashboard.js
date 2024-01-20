 // Odoo Dashboard JavaScript Code for the Document Dashboard

odoo.define('documents_reminder.Dashboard', function (require) {

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const QWeb = core.qweb;
    const session = require('web.session');


    const DocumentDashboard = AbstractAction.extend({
        template: 'DocumentDashboard',

        /*
         * @override
         */
        init: function(parent, context) {
            debugger
            this._super(parent, context);
            this.company_name = session.user_companies.allowed_companies[session.company_id].name

        },

        /*
         * @override
         */
        willStart: async function() {
            const res = await this._super();
            const datas = await this._rpc({
                model: 'reminder.document',
                method: 'get_document_data'
            });
            this.document_data = datas.document_data;
            this.sections_data = datas.sections_data;
            this.company_data = datas.company_data;
            return res;
        },

        /*
         * @override
         */
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboard_list();
                self.$el.parent().addClass('oe_background_grey');
            });
        },

        /*
         * Renders all data on Dashboard view for Documents.
         */
        render_dashboard_list: function() {
            this.$('.o_document_list_container').append(QWeb.render('DashboardList', {widget: this}));
            this.$('.o_document_calendar_container').append(QWeb.render('DasboardCompanyStats', {widget: this}));

            const config = {
                animate: 1000,
                scaleColor: false,
                lineWidth: 4,
                lineCap: 'square',
                size: 90,
                trackColor: 'rgba(0, 0, 0, .09)',
                onStep: function(_from, _to, currentValue) {
                var value = currentValue;

                $(this.el)
                    .find('> span')
                    .text(Math.round(value) + $(this.el).attr('data-suffix'));
                    },
                }

            this.$('#easy-pie-chart-1')
                .attr('data-percent', this.company_data.percentage_documents)
                .attr('data-max-value', this.company_data.total_allowed_documents)
                .easyPieChart($.extend({}, config, { barColor: '#43a047' }));

            this.$('#easy-pie-chart-2')
                .attr('data-percent', this.company_data.percentage_partners)
                .attr('data-max-value', this.company_data.total_allowed_partners)
                .easyPieChart($.extend({}, config, { barColor: '#039be5' }));

        },

    });

    core.action_registry.add('document_dashboard', DocumentDashboard);

    return DocumentDashboard;

});
