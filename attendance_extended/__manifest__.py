# -*- coding: utf-8 -*-
{
    'name' : 'Attendance with Project and Task',
    'version' : '16.0.1.0.0',
    'summary': 'Allow user to select project and task while chech-in and check-out in attendance',
    'sequence': 100,
    'description': """Modification of attendance module to
        enhance the existing attendance module to allow users to:
        Select a project: Users should be able to choose a specific project while checking in.
        Select a project task: Along with selecting a project, users should also be able to select a specific task related to the chosen project.
        Write descriptions: Enable users to add a description for their activities during both check-in and check-out.""",
    'author': 'Dhvanil Trivedi',
    'maintainer': 'Dhvanil Trivedi',
    'category': 'Productivity',
    'images' : [],
    'depends': ['hr_attendance','project'],
    'data': [
        'views/hr_attendance_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'attendance_extended/static/src/js/hr_attendance.js',
            'attendance_extended/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'license': 'LGPL-3',
}