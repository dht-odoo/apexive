odoo.define('attendance_extended.inherit_my_attendance', function (require) {
    "use strict";

    var MyAttendances = require('hr_attendance.my_attendances');
    var session = require('web.session');

    MyAttendances.include({
        events: Object.assign({}, MyAttendances.prototype.events, {
            'change select[id="projectSelect"]': '_onChangeProjectSelect',
        }),
        // When change the js project, It will set project task with this project
        _onChangeProjectSelect: function (ev) {
            if (this.$("#projectSelect")[0]) {
                const projectID = this.$("select[name='project_id']").val();
                var selectHtml = '<select class="col-7" name="project_task_id" id="projectTaskSelect">';
                selectHtml += '<option selected="selected" value=""></option>';
                for (const tId of this.projects.project_task_ids) {
                    if (tId.project_id == projectID) {
                        selectHtml += "<option value='" + tId.id + "'" + ">" + tId.name + "</option>";
                    }
                }
                selectHtml += "</select>";
                this.$("#projectTaskSelect").replaceWith(selectHtml);
            }
        },
        
        // When it start Attendance, collection current attendances data with project, project task and description from backend
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._rpc({
                    model: 'hr.employee',
                    method: 'get_attendance_projects',
                    args: [[['user_id', '=', self.getSession().uid]]],
                    context: session.user_context,
                }).then(function (p) {
                    self.projects = p;
                });
            });
        },

        /**
         * @override
         */ 
        update_attendance: function () {
            var self = this;
            var context = session.user_context;
            var project_id = this.$("select[name='project_id']").val();
            var project_task_id = this.$("select[name='project_task_id']").val();
            var attend_description = this.$("textarea[id='attend_description']").val();
            if (!project_id || !project_task_id || !attend_description) {
                self.displayNotification({ title: "Warning", message: "Please fill in all mandatory fields.", type: 'warning' });
                return;
            }
            context['project_id'] = project_id;
            context['project_task_id'] = project_task_id;
            debugger
            if (this.employee.attendance_state === 'checked_in') {
                context['attendance_description_out'] = attend_description;
            }else {
                context['attend_description'] = attend_description;
            }
            this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
                context: context,
            })
                .then(function (result) {
                    if (result.action) {
                        self.do_action(result.action);
                    } else if (result.warning) {
                        self.displayNotification({ title: result.warning, type: 'danger' });
                    }
                });
        },
    });
    return MyAttendances;
});
