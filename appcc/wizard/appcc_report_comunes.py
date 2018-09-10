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

from openerp import api, fields, models, _


class AppccCommonReport(models.TransientModel):
    _name        = "appcc.common.report"
    _description = "Report Comunes Appcc"


    date_from = fields.Date(string=_('Fecha Inicio'))
    date_to   = fields.Date(string=_('Fecha Fin'))


    @api.one
    @api.constrains('date_from','date_to')
    def _check_date(self):
        if self.date_from > self.date_to:
            raise Warning("La fecha inicio no puede ser mayor que la fecha fin")

    def _build_contexts(self, data):
        result = {}

        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False

        return result

    def _print_report(self, data):
        raise (_('Error!'), _('Not implemented.'))

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids']   = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form']  = self.read(['date_from', 'date_to'])[0]
        used_context  = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_ES'))
        return self._print_report(data)
