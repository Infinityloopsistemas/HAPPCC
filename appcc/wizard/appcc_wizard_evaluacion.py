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

MESES = map( lambda x: 2*[ (str(x))] , range(1,13) )


class AppccWizardEvaluacion(models.TransientModel):
    """
    Genera las etapas recursivamente haste un nivel y profundidad
    """
    _name = "appcc.wizard.evaluacion"
    _description = "Genera una evaluacion desde plantillas"


    fecha             = fields.Date(string=_("Fecha"), required=True)
    name              = fields.Char(string=_("Denominación de la evaluación"),  required=True)
    tecnicos_id       = fields.Many2one('res.partner',required=True,string=_("Tecnicos"), domain=([('company_type','=','person'),('category_id.name','=','VETERINARIO')]))
    evaldet_ids       = fields.One2many('appcc.wizard.evaluacionlin','evaldet_id')
    regeval_id        = fields.Many2one('appcc.cabregistros', string=_("Registro Control"))
    mes_ini           = fields.Selection(MESES, string=_("Mes Inicial"),required=True)
    mes_fin           = fields.Selection(MESES, string=_("Mes Final"), required=True)

    @api.multi
    def action_button_generar(self):

        if len(self.evaldet_ids)==0:
            raise ValidationError( 'Seleccione plantillas para proceder a la configuracion')

        obj_evaluacion = self.env['appcc.evaluacion']
        obj_evalualin  = self.env['appcc.evaluacion.lineas']
        obj_evaluadet  = self.env['appcc.evaluacion.detalle']
        ano = datetime.datetime.strptime(self.fecha,'%Y-%m-%d').year

        userid = self.env['res.users'].search([('partner_id', '=', self.tecnicos_id.id)], limit=1).id
        print "Vemos usuario %s " % userid
        if userid == False:
            userid = None
        for mes in range(int(self.mes_ini),int(self.mes_fin)+1):
            pri_fecha = datetime.date(ano, mes, 1).strftime("%Y-%m-%d")
            calevalua = self.env['calendar.event']
            eval_vals = {
                'name': "%s - %s " % (self.name,str(mes).zfill(2)),
                # 'categ_ids': record.holiday_status_id.categ_id and [
                #     (6, 0, [record.holiday_status_id.categ_id.id])] or [],
                'duration': 1,
                'description':'Correspondiente al mes de %s ' % str(mes).zfill(2) ,
                'partner_ids': [([4,self.tecnicos_id.id])],
                'user_id': userid,
                'start': pri_fecha,
                'stop':  pri_fecha,
                'allday': False,
                'state': 'open',  # to block that meeting date in the calendar
                'class': 'public',
                'alarm_ids' : [(6,0,[4,5])]
            }
            idcaleeval = calevalua.create(eval_vals).id
            #Creamos Evaluacion

            ideval = obj_evaluacion.create({'calevalua_id': idcaleeval, 'regeval_id': self.regeval_id.id, 'fecha': pri_fecha,'name': "%s - %s " % (self.name,str(mes).zfill(2)) ,'tecnicos_id': self.tecnicos_id.id})
            for reg in self.evaldet_ids:
                # print {'evaldet_id': ideval.id,'templatevalua_id': reg.tipotemplate.id,
                #                                    'property_departament': reg.property_departament.id, 'property_employee': reg.property_employee.id,
                #                                 'property_centro': reg.property_centro.id,'property_equipos': reg.property_equipos.id,
                #                             'name': reg.name}
                idevallin = obj_evalualin.create({'evaldet_id': ideval.id,'templatevalua_id': reg.tipotemplate.id,
                                                  'property_departament': reg.property_departament.id, 'property_employee': reg.property_employee.id,
                                               'property_centro': reg.property_centro.id,'property_equipos': reg.property_equipos.id,
                                           'name': reg.name, 'fecha': pri_fecha })
                print "Genera lineas ID %s" % idevallin.id
                for det in reg.tipotemplate.tevaluacion_ids:
                    idevaldet = obj_evaluadet.create({'evallin_id': idevallin.id, 'indicador_id': det.id,'textoevaluar': det.name  })


        ctx = dict()
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            compose_form_id = ir_model_data.get_object_reference('appcc', 'appcc_evaluacion_lineas_tree_view')[1]
        except ValueError:
            compose_form_id = False


        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'appcc.evaluacion.lineas',
            'views': [(compose_form_id, 'tree')],
            'view_id' : compose_form_id
        }



class AppccWizardEvaluacionLin(models.TransientModel):
    _name = "appcc.wizard.evaluacionlin"
    _description = "Genera lineas  evaluacion desde plantillas"


    evaldet_id           = fields.Many2one('appcc.wizard.evaluacion')
    tipotemplate         = fields.Many2one('appcc.template.evaluacion', string=_("Seleccionar plantilla"))
    property_departament = fields.Many2one('hr.department',  string=_("Departamento"),company_dependent=True)
    property_employee    = fields.Many2one('hr.employee',    string=_("Personal"),company_dependent=True)
    property_centro      = fields.Many2one('res.partner',    string=_("Centro"),company_dependent=True)
    property_equipos     = fields.Many2one('asset.asset',    string=_("Equipos"),company_dependent=True)
    name                 = fields.Char(string=_("Otros"))


    @api.onchange('tipotemplate')
    def onchange_tipo(self):
        tipo = self.tipotemplate.tipo

        print "--------------Seleccionamos el tipo %s" % tipo
        res={}
        if tipo == 'D':
            res['domain']={
                    'property_centro'      : [('id','=', 0)],
                    'property_employee'    : [('id','=', 0)],
                    'property_equipos'     : [('id','=', 0)],
                    'property_departament' : [('id','!=', 0),('company_id','=', self.env['res.company']._company_default_get('appcc').id)]
                }

        else:

            if tipo == 'P':
                res['domain']={
                        'property_employee' : [('id','!=', 0),('company_id','=',self.env['res.company']._company_default_get('appcc').id)],
                        'property_centro' : [('id','=', 0)],
                        'property_departament' : [('id','=', 0)],
                        'property_equipos' : [('id','=', 0)]
                    }
            else:

                if tipo == 'C':
                    res['domain']={
                             'property_centro' : [('id','!=', 0),('company_id','=',self.env['res.company']._company_default_get('appcc').id)],
                            'property_departament' : [('id','=', 0)],
                            'property_employee' : [('id','=', 0)],
                            'property_equipos' : [('id','=', 0)]
                        }
                else:
                    if tipo == 'E':
                        #Dominio de los equipos asociadods al registro
                        equipos_ids =[]

                        for idequip in self.evaldet_id.regeval_id.cabreg_ids:
                            print "----- Id. compnany %s " % idequip.equipos_id.property_stock_asset.company_id.id
                            if idequip.equipos_id.property_stock_asset.company_id.id == self.env['res.company']._company_default_get('appcc').id:
                                equipos_ids.append(idequip.equipos_id.id)

                        if equipos_ids ==[]:
                            res['domain'] = {
                                'property_equipos': [ ('id', '!=', 0) ],
                                'property_centro': [('id', '=', 0)],
                                'property_employee': [('id', '=', 0)],
                                'property_departament': [('id', '=', 0)]
                            }
                        else:
                            res['domain']={
                                    'property_equipos' : [('id','in', equipos_ids),],
                                    'property_centro' : [('id','=', 0)],
                                    'property_employee' : [('id','=', 0)],
                                    'property_departament' : [('id','=', 0)]
                                }
        return res


    @api.constrains('name')
    def  constraint_name(self):
        if self.name:
            if self.property_departament or self.property_centro or self.property_equipos or self.property_employee:
                raise ValidationError( 'Imposible añadir OTROS mientras exista otra OPCION')
