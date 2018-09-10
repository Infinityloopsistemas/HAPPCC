# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 InfinityLoop Sistemas S.L (<http://www.infinityloop.es>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Appcc',
    'version': '1.0',
    'sequence': 1,
    'description': """
       Analisis de Peligros y puntos de control criticos
       ( Hazard Analysis and Critical Control Point)
       según el R.D. 2207/95 que transpone la Directiva 93/43/CE""",
    'author': 'Infinityloop Sistemas S.L',
    'images' :['images/hummingbird.png'],
    'depends': ['tracksondas','textmagicsms','hr','calendar','product','document','report_webkit','asset',],
    'external_dependencies': { 'python': ['textmagic'], },
    'summary': '',
    'data': ['security/appcc_security.xml',
             'security/ir.model.access.csv',
             'data/appcc_maestros.xml',
             'views/appcc_menuitem.xml',
             'views/appcc_calendar.xml',
             'views/appcc_reports.xml',
             'views/appcc_report_qr.xml',
             'views/appcc_report_registros.xml',
             'views/appcc_report_analitica.xml',
             'views/appcc_report_cuadrog.xml',
             'views/appcc_report_plan.xml',
             'views/appcc_report_inicio.xml',
             'views/appcc_report_procedimiento.xml',
             'views/appcc_report_informeaud.xml',
             'views/appcc_report_evaluaciones.xml',
             'views/appcc_maestros_view.xml',
             'views/appcc_view.xml',
             'views/partner_view.xml',
             'views/hr.xml',
             'views/appcc_evaluacion_view.xml',
             'wizard/appcc_report_comunes_view.xml',
             'wizard/appcc_report_reg_view.xml',
             'views/report_toteval.xml',
             'views/report_totevalm.xml',
             'wizard/appcc_wizard_maestros.xml',
             'wizard/appcc_wizard_evaluacion.xml',
             'wizard/appcc_wizard_view_clonado.xml',
             'wizard/appcc_wizard_planforma.xml',
             'views/report_regfecha.xml',
             'views/report_evalregistros.xml',
             'views/report_certforma.xml',
             'views/layouts.xml',
             'views/layouts_simple.xml',
             'views/company_view.xml',
             'views/appcc_report_avisos.xml',
             'views/res_users_view.xml',
             'data/appcc_tpmedvigilancia.xml',
             'data/appcc_tpmedactuacion.xml',
             'data/appcc_inicio.xml',
             'data/appcc_eventos.xml',
             'data/appcc_colores.xml',
             'data/appcc_festivos.xml'

    ],
    'demo': [],
    'installable': True,
    'application': True,
}

