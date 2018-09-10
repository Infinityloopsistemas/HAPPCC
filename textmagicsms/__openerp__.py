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
    'name': 'Text Magic',
    'version': '1.0',
    'category': 'Utilities',
    'sequence': 75,
    'author': 'Infinityloop Sistemas S.L',
    'summary': 'SMS SENDS',
    'description': """
     SMS SENDS
     Install pip install textmagic
    """,
    'website': 'https://www.textmagic.com',
    'images': [
    ],
    'depends': [

    ],
    'data': ["views/textmagicsms_view.xml","data/textmagic_data.xml"

    ],
    'demo': [],
    'test': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
