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
from openerp import models, fields, api, _
from openerp.tools.float_utils import float_round



class GeneraEtapas(models.TransientModel):
    """
    Genera las etapas recursivamente haste un nivel y profundidad
    """
    _name = "appcc.maestros.generaetapas"
    _description = "Genera Estapa con nivel, apartado y profundidad"

    prefijo     = fields.Char(string=_("Nombre Etapa"))
    niveles     = fields.Integer(string=_("Niveles"), required=True)
    apartados   = fields.Integer(string=_("Apartados"), default=0)
    profundidad = fields.Integer(string=_("Profundidad"), default=0)

    @api.multi
    def action_button_genera(self):

        objetap = self.env['appcc.maestros.etapas']
        context = dict(self._context or {})
        for ni in range(1,self.niveles):
            nivel = "%s %s" % (self.prefijo,ni)
            nivel_id = objetap.create({'name': nivel, 'parent_id':'' })
            if self.apartados!=0:
                for apa in range(1,self.apartados):
                    apartado = "%s %s.%s" % (self.prefijo,ni,apa)
                    apartado_id = objetap.create({'name': apartado, 'parent_id': nivel_id.id})
                    if self.profundidad!=0:
                        for prof in range(1,self.profundidad):
                            profundidad =  "%s %s.%s.%s" % (self.prefijo,ni,apa,prof)
                            objetap.create({'name': profundidad, 'parent_id': apartado_id.id })


        # active_ids = context.get('active_ids', []) or []
        #
        # for record in self.env['account.invoice'].browse(active_ids):
        #     if record.state not in ('draft', 'proforma', 'proforma2'):
        #         raise UserError(_("Selected invoice(s) cannot be confirmed as they are not in 'Draft' or 'Pro-Forma' state."))
        #     record.signal_workflow('invoice_open')
        return {'type': 'ir.actions.act_window_close'}
