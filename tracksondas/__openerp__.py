# -*- coding: utf-8 -*-
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
    'name': 'TrackSondas',
    'version': '1.0',
    'sequence': 1,
    'description': """Modulo para monitorización sondas en el dominio del tiempo
      instalar
      pip install xmltodict """,
    'author': 'Infinityloop Sistemas S.L',
    'images' :['images/tracksondas.png'],
    'depends': ['textmagicsms','mro','jasper_server'],
    'external_dependencies': { 'python': ['plotly'], },
    'summary': '',
    'data': ['security/tracksonda_security.xml',
             'security/ir.model.access.csv',
             'data/jasper_config.xml',
             'views/tracksonda_view.xml',
             'views/delivery_view.xml',
             'wizard/tracksonda_wizard.xml',
             'views/tracksonda_report_grafica.xml',
             'views/tracksonda_report_delivery.xml',
             'views/tracksonda_report.xml',
             'data/tracksondas_data.xml',
             ],
    'demo': [],
    'installable': True,
    'application': True,
}

