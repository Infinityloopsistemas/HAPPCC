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
from openerp.exceptions import ValidationError
import datetime


class AppccWizardPlanFormacion(models.TransientModel):
    """
    Genera las etapas recursivamente haste un nivel y profundidad
    """
    _name = "appcc.wizard.planformacion"
    _description = "Genera planes de formacion desde Empleados"


    frecuencia_id    = fields.Many2one('appcc.maestros.tpfrecuencias', string=_("Frecuencia"), required=True)
    personal_ids      = fields.Many2many('hr.employee','appcc_wiz_plforma_rel','plforma_id','personal_id', string=_("Personal"), required=True, domain=lambda self: [
        ('department_id.company_id.id', '=', self.env['res.company']._company_default_get('appcc.planformacion').id)])
    tercero_id       = fields.Many2one('res.partner', string=_("Imparte el Curso"), required=False,
                                 domain=([('category_id.name', '=', 'FORMACION')]))
    fechavalida      = fields.Date(string =_("Fecha Certificacion"),required=True )
    tiposcursos_ids  = fields.Many2many('appcc.maestros.tpcursos','appcc_wz_plforma_tpcurso_rel','plforma_id','tpcurso_id',string="Cursos Recibidos")

    @api.multi
    def action_button_generar(self):

        if len(self.personal_ids) == 0:
            raise ValidationError('Seleccione personas para crear los planes')

        model_planformacion = self.env['appcc.planformacion']

        print "Tipos de Cursos"
        ids_cursos=[]
        for cursos in self.tiposcursos_ids:
           ids_cursos.append(cursos.id)



        # ids_cursos = "'name': ".join(map(lambda x: x, (str(tipocur.name) for tipocur in
        #                                         self.tiposcursos_ids)))



        for personas in self.personal_ids:
            model_planformacion.create({ 'frecuencia_id': self.frecuencia_id.id, 'personal_id' : personas.id, 'tercero_id':self.tercero_id.id, 'fechavalida' :self.fechavalida,
                                         'tiposcursos_ids': [( 6,0, ids_cursos )] } )

        ctx = dict()
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            compose_form_id = ir_model_data.get_object_reference('appcc', 'appcc_pformacion_tree_view')[1]
        except ValueError:
            compose_form_id = False

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'appcc.planformacion',
            'views': [(compose_form_id, 'tree')],
            'view_id': compose_form_id
        }


