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

import datetime
__author__ = 'julian'
from openerp.osv import osv
from openerp import api, fields, models, fields
from openerp import _, tools
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError


def fechaEjecucion( fecha, diapro):
    """ Comprueba si s un  dia a agendizar
    :param fecha: dia a comprobar date
    :param diapro: parametrizacion del dia Integer
    :return: Boolean """
    print "---------------------------------------diapro %s " % diapro
    # OPCIONES_DIAS = ([('T',_('Ningun día')),('A',_('Todos los dias')),('L',_('Lunes a Viernes')),('F',_('Fin de Semana')),('5',_('Sabado')),('6',_('Domingo')),('0',_('Lunes')),('1',_('Martes')),('2',_('Miercoles')),('3',_('Jueves')),('4',_('Viernes'))])
    ndia = fecha.weekday()
    # print "Dia ejecucion %s Dia programados %s " % (ndia,diapro)
    if diapro == 'T':
        # print "Entra en ningun dia"
        return False
    else:
        if ndia in (6, 5) and diapro == 'F':
            # print "Entra en Fines de semana"
            return True
        else:
            if diapro == 'A' or not diapro:
                # print "Entra en todos los dias"
                return True
            else:
                if ndia in (0, 1, 2, 3, 4) and diapro == 'L':
                    # print "Entra de lunes a viernes"
                    return True
                else:
                    if ndia in (0, 1, 2, 3, 4, 5) and diapro == 'S':
                        # print "Entra de lunes a sabado"
                        return True
                    else:
                        if str(ndia) == diapro:
                            # print "Entra en dia concreto %s" % ndia
                            return True
                        else:
                            # print "Ninguna opcion de las anteriores"
                            return False



class GeneraClonado(models.TransientModel):
    """
    Generar nuevos appcc
    """
    _name = "appcc.wizard.clonado"
    _description = "Genera nuevos appcc de uno existentes"

    name        = fields.Char(string="Nombre de local en APPCC")
    appcc_id    = fields.Many2one('appcc',deafult= lambda self: [('company_id.id','=', self.env['res.company']._company_default_get('appcc.wizard.clonado').id)] , string=_("APPCC"),required=True)
    company_id  = fields.Many2one('res.company', string=_("Empresa / Local Destino") , required=True,context={'user_preference': True})
    fechainicio = fields.Date(string="Fecha Inicio APPCC", required=True)
    fechareg    = fields.Date(string="Fecha Inicio Registros", required=True)
    revision_id = fields.Many2one('appcc.historialrevisiones', string=_("Revisión"), required=True)


    @api.constrains('company_id')
    def _valida_revision(self):
        idcompany = self.env['res.company']._company_default_get('appcc.wizard.clonado').id
        if self.appcc_id.revision_id.id == self.revision_id.id and self.company_id.id == idcompany :
            raise ValidationError(_("Imposible Clonar igual APPCC en la misma empresa con igual revision"))


    #VALIDAR FECHAS DE CLONADO

    # @api.onchange('company_id')
    # def _change_revision(self):
    #     res = {}
    #     if self.company_id:
    #         print "Entra en self.comapny_id %s " % self.company_id.id
    #         res['domain'] = {'revision_id': [('company_id.id', '=', self.company_id.id)]}
    #         print res
    #     else:
    #         print "Entra en nulo"
    #         res['domain'] = {'revision_id': []}
    #     return res


    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     context = self._context or {}
    #     res = super(GeneraClonado, self).fields_view_get(view_id=view_id, view_type=view_type,
    #                                                                  toolbar=toolbar, submenu=False)
    #     cmp_select = []
    #     CompanyObj = self.env['res.company']
    #
    #     companies = CompanyObj.sudo().search([])
    #     companies_ids =', '.join(map(lambda x: x,( str(emp.id) for emp in companies )))
    #
    #     # Muestra solo las company que no tienes APPCC asociado
    #     print "SELECT company_id FROM appcc WHERE company_id in (%s)" % companies_ids
    #     self._cr.execute("SELECT company_id FROM appcc WHERE company_id  in (%s) group by company_id" % companies_ids)
    #     configured_cmp = [r[0] for r in self._cr.fetchall()]
    #
    #     print "Configura ids %s " % configured_cmp
    #     for field in res['fields']:
    #         if field == 'company_id':
    #             print "Entra ... en campo"
    #             cmp_select = [(line.id, line.name) for line in CompanyObj.sudo().browse(configured_cmp)]
    #             print cmp_select
    #             res['fields'][field]['domain'] = []
    #             res['fields'][field]['selection'] = cmp_select
    #
    #     return res


    @api.multi
    def action_button_generar(self):
        #Duplicamos appcc y sobre escribimos el nombre
        model_appcc = self.env['appcc']
        model_manua = self.env['appcc.manualautocontrol']
        model_plana = self.env['appcc.planautocontrol']
        model_consd = self.env['appcc.consumibles']
        model_cabre = self.env['appcc.cabregistros']
        model_detre = self.env['appcc.detallesregistros']
        model_cuadg = self.env['appcc.cuadrosgestion']
        model_locat = self.env['stock.location']



        #Duplicamos appcc
        for regappcc in model_appcc.browse([self.appcc_id.id]):
            print "Copia APPCC"
            new_obj_appcc  = regappcc.copy()
            new_obj_appcc.sudo().write({'company_id' : self.company_id.id , 'name' : self.name , 'fecimplanta' : self.fechainicio, 'revision_id' : self.revision_id.id})
            #Duplicamos Planes de AutoControl
            for regmanu in model_manua.search([('appcc_id','=',regappcc.id )]):
                print "Copia Plan Autocontrol --id appcc  origen %s   final %s " % (regappcc.id, new_obj_appcc.id)
                new_obj_manu    = regmanu.copy()
                print "Finaliza Copia Plan Autocontrol"
                new_obj_manu.sudo().write({'appcc_id': new_obj_appcc.id, 'company_id': self.company_id.id, 'revision_id' : self.revision_id.id})
                print "Finaliza Actualiza Plan Autocontrol"
                #Duplicamos los procedimientos
                for regplan in model_plana.search([('manautctrl_id','=',regmanu.id)]):
                    print "Copia Procedimientos"
                    new_obj_plana = regplan.copy()
                    new_obj_plana.sudo().write({'manautctrl_id':new_obj_manu.id, 'fecha': self.fechainicio ,'company_id': self.company_id.id ,'revision_id' : self.revision_id.id })
                    #Duplicamos Consumibles
                    for regconsd in model_consd.search([('planautctrl_id','=',regplan.id)]):
                        print "Copia Consumibles"
                        new_obj_consd = regconsd.copy()
                        new_obj_consd.sudo().write({'planautctrl_id': new_obj_consd.id, 'company_id': self.company_id.id })
                for regcabreg in model_cabre.search([('manautctrl_id','=',regmanu.id)]):
                    print "Copia CabReg"
                    new_obj_cabre = regcabreg.copy()
                    new_obj_cabre.sudo().write({'manautctrl_id': new_obj_manu.id, 'company_id': self.company_id.id, 'revision_id': self.revision_id.id })
                    for regdetreg in model_detre.search([('cabreg_id','=',regcabreg.id)]):
                        print "Copia Detreg"
                        new_obj_detre =  regdetreg.copy()
                        #Procedemos a revisar los dias de ejecución de los registros
                        diapro = new_obj_detre.diaejecuta
                        dfecha = datetime.datetime.strptime(new_obj_detre.fecha, "%Y-%m-%d")
                        if  not fechaEjecucion(dfecha, diapro):
                            diasema = dfecha.weekday()
                            dif     = diasema-diapro
                            dfecha  = dfecha+datetime.timedelta(days=dif)
                        new_obj_detre.sudo().write({'cabreg_id': new_obj_cabre.id, 'company_id': self.company_id.id, 'revision_id': self.revision_id.id,'departamento_ids': None , 'fecha': dfecha.strftime('%Y-%m-%d'), 'tracksonda_id': None })

            list_parent ={}
            mod_cuad=[]
            for regcuadro in model_cuadg.search([('appcc_id','=',regappcc.id)]):
                new_obj_regcuadro = regcuadro.copy()
                list_parent[regcuadro.id] =new_obj_regcuadro.id
                new_obj_regcuadro.sudo().write({ 'appcc_id':  new_obj_appcc.id, 'company_id': self.company_id.id, 'revision_id': self.revision_id.id, 'registros_id': None, 'ente_id': None })
                if not new_obj_regcuadro.parent_id:
                    new_obj_regcuadro.sudo().write({'name': 'Emp/Local %s ' % self.name})
                mod_cuad.append(new_obj_regcuadro.sudo())
            print "Lista de registos "
            print list_parent
            if len(list_parent)>0:
                print "--- Entra en Actualizar Cuadro de Gestion ---"
                print mod_cuad
                for reg_par_cuad in mod_cuad:
                    print "Objeto Cuad Gestion %s " % reg_par_cuad.parent_id.id
                    parent_id = list_parent.get(reg_par_cuad.parent_id.id)
                    print "Registro padre %s " % parent_id
                    if parent_id:
                        print "Actualizamos padre %s " % parent_id
                        reg_par_cuad.sudo().write({'parent_id' : parent_id})

            #Generamos las zonas

            company_origen = self.env['res.company']._company_default_get('appcc.wizard.clonado').id
            if company_origen != self.company_id.id:
                objs_locats = model_locat.search([('company_id','=',company_origen),('usage','=','asset')])
                for locat in objs_locats:
                     new_loca = locat.copy()
                     new_loca.sudo().write({'company_id': self.company_id.id})



        # active_ids = context.get('active_ids', []) or []
        #
        # for record in self.env['account.invoice'].browse(active_ids):
        #     if record.state not in ('draft', 'proforma', 'proforma2'):
        #         raise UserError(_("Selected invoice(s) cannot be confirmed as they are not in 'Draft' or 'Pro-Forma' state."))
        #     record.signal_workflow('invoice_open')
        return {'type': 'ir.actions.act_window_close'}