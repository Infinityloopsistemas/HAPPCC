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

from operator import itemgetter
import time

from openerp import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import ValidationError



class ResCompany(models.Model):
    _inherit = "res.company"

    auditora_id    = fields.Many2one('res.partner', domain = ([('category_id.name','=','AUDITORA')]), string=_("Auditora"))
    auditor_id     = fields.Many2one('res.partner', string=_("Auditor"))
    nrgseaa        = fields.Char( string="NO.RGSEAA")


    @api.one
    @api.constrains('auditora_id')
    def _validate_auditoria(self):
        warning = {}
        result  = {}
        print "Entra en constraints"
        if not self.auditora_id:
            warning = {
                    'title':   _('Error!'),
                    'message': _('Seleccione empresa auditora'),
                }
            result['warning'] = warning
            return result

    @api.multi
    @api.onchange('auditora_id')
    def _onchange_auditoria(self):
        aids=[]
        res={}
        partner_ids = self.env['res.partner'].search_read([('parent_id','=',self.auditora_id.id),('company_type','=','person')],['id'] )

        for idpar in partner_ids:
            print "Personas %s " % idpar
            aids.append(idpar['id'])

        if partner_ids:
            res['domain']={
                    'auditor_id' : [('id','in', aids)]
                }
        return res


    def _action_busca_rgseaa(self):
        #http: // rgsa - web - aesan.msssi.es / rgsa / formulario_principal_js.jsp
        pass




