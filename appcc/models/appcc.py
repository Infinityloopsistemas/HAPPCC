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
import threading

import numpy as np

__author__ = 'julian'
from openerp.osv import osv
from openerp import api, fields, models, fields
from openerp import _, tools
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
import datetime
import os
import base64
import tempfile


OPCIONES_DIAS_1 = (('S',_('Lunes a Sabado')),('L',_('Lunes a Viernes')),('F',_('Fin de Semana')),('5',_('Sabado')),('6',_('Domingo')),('0',_('Lunes')),('1',_('Martes')),('2',_('Miercoles')),('3',_('Jueves')),('4',_('Viernes')))
OPCIONES_TPCAL  = ([('FESTIVO NACIONAL',('FESTIVO NACIONAL')),('FESTIVO AUTONOMICO',('FESTIVO AUTONOMICO')),('FESTIVO LOCAL',('FESTIVO LOCAL'))])
HORAS  =    map( lambda x: 2*[ (str(x))] , range(0,24) )
TIPOLECTURA =(('QR','QR'),('M',_('MANUAL')),('QRA',_('QR Y MANUAL')),)


def fechaEjecucion( fecha, diapro):
    """ Comprueba si s un  dia a agendizar
    :param fecha: dia a comprobar date
    :param diapro: parametrizacion del dia Integer
    :return: Boolean """
    #print "---------------------------------------diapro %s " % diapro
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


class appcc_config_settings(osv.osv_memory):
    _name = 'appcc.config.settings'
    _description = "Settings de Configuración APPCC"


    appc_ok     = fields.Boolean('APPCC Listo', help=_("""Configurar datos iniciales APPCC"""))
    planauto_ok = fields.Boolean('Plan auto control Listo', help=_("""Configurar plan de auto control"""))
    manual_ok   = fields.Boolean('Manual auto control Listo', help=_(""" Configurar manual de auto control"""))


    # configuracion =  models.ForeignKey(Configuracion,on_delete=models.PROTECT)
    # personas      =  models.ManyToManyField(Personal, verbose_name=_("Personas"),help_text=_("a efectos de avisos"))
    # registros     =  models.ManyToManyField(CabRegistros, verbose_name="Registros a Supervisar")
    # accion        =  models.CharField(max_length=1, choices=(('I',_('Incidencias')),('A',_('EMAIL')),('T',_('EMAIL/Incidencias')),('S',_('SMS')),( 'Z',_('SMS/EMAIL')) ), verbose_name=_("Acción a realizar" ) )
    # habilitar     =  models.CharField( verbose_name=_("Habilitar"),max_length=1, choices=(('S',_('Si')),('N',_('No'))))
    # dias          =  models.CharField(max_length=1,choices=OPCIONES_DIAS_1, null=True,blank=True, verbose_name="Dias Activa")
    # turnos        =  models.ForeignKey(TiposTurnos, blank=True, null=True, verbose_name="Horario Desactiva")


class ApccConfigAvisos(models.Model):
    _name        ='appcc.config.avisos'
    _description ='Configuracion de Avisos'

    @api.one
    @api.depends('detreg_ids')
    def _compute_marcoslegales(self):
        txtmarco=""
        actual=0
        ids=[]
        if self.tipoaviso == "P":
            if self.tipodeplan_id.habilitaformacion:
                txtmarco   = self.env['appcc.planformacion'].search([('tiposcursos_ids',"!=",False)],limit=1).manautctrl_id.marcolegal
            else:
                txtmarco = self.env['appcc.manualautocontrol'].search([('tpplancontrol_id', "=", self.tipodeplan_id.id),('tpplancontrol_id.habilitaformacion', '=', False)],limit=1).marcolegal
        else:
            for ele in self.detreg_ids:
                if ele.cabreg_id.manautctrl_id.id not in ids:
                    txtmarco = ele.cabreg_id.manautctrl_id.marcolegal +txtmarco
                    ids.append(ele.cabreg_id.manautctrl_id.id)

        self.marcolegal=txtmarco


    name          = fields.Char(string=_("Denominación"), required=True)
    partner_ids   = fields.Many2many('res.partner',string=_('Destinatarios'), required=False)
    tipoaviso     = fields.Selection([('R','Revision Registros'),('P','Planes de Autocontrol')], required=True, default='R')
    tipodeplan_id = fields.Many2one('appcc.maestros.tpplancontrol', string="Tipo de Plan", domain=[('habilitaavisos','=',True)])
    detreg_ids    = fields.Many2many( 'appcc.detallesregistros',string='Registros a Supervisar', required=False, domain=([('actividades_id.agenda','=',True),('tracksonda_id','=',False)]) )
    tipoenvio     = fields.Selection([('E','EMail'),('S','SMS'),('ES',('Email/SMS'))], required=True)
    active        = fields.Boolean(string=_("Activo"), default=True)
    tpturnos_id   = fields.Many2one('appcc.maestros.tpturnos', string=_("Turno"),required=False)
    diasdesfase   = fields.Integer(string=_("Límite días aviso"))
    revisareg_ids = fields.One2many('appcc.revisareg','confavisos_id')
    company_id    = fields.Many2one('res.company',string=_("Empresa / Local"), default=lambda self: self.env['res.company']._company_default_get('appcc.config.avisos'))
    marcolegal    = fields.Html(compute=_compute_marcoslegales)

    #Validar seleccion a la hora de configurar los avisos
    @api.model
    def cron_planformacion(self):
        """ Revisamos el personal proximo a  caducar"""
        cr = self.env.cr
        diaspend = 0
        fmt = '%Y-%m-%d'
        fecha = datetime.datetime.now()
        # Registros con sondas
        objconfavisos  = self.env['appcc.config.avisos']
        objconfrefav   = self.env['appcc.revisareg']
        regsavisos     = objconfavisos.search([('active', '=', True), ('tipoaviso', '=', 'P'),('tipodeplan_id.habilitaformacion','!=',False)])

        for regavi in regsavisos:
            regcreados = []
            if regavi.tipodeplan_id.habilitaformacion:
                objs_planforma = self.env['appcc.planformacion'].search([('company_id', '=', regavi.company_id.id)])
                for planforma in objs_planforma:
                    _fecal_str = planforma.fechavalida
                    _fecal = datetime.datetime.strptime(_fecal_str,fmt)
                    ndias = ( (planforma.frecuencia_id.nounidades)/24) - regavi.diasdesfase
                    d_fecal1= _fecal + datetime.timedelta(days=  ndias)
                    d_fecal2=  d_fecal1 + datetime.timedelta(days= 2*regavi.diasdesfase)
                    if d_fecal1<= fecha and fecha <= d_fecal2:
                        newobj = objconfrefav.create(
                            {'fechaultima': _fecal_str , 'fechaaudit': fecha,
                             'planforma_id': planforma.id, 'desfase': ndias, 'tipo': 'V', 'name': planforma.manautctrl_id.name,
                             'confavisos_id': regavi.id})
                        regcreados.append(newobj)

            if len(regcreados) != 0:
                idok = self._send_mail_desfase("email_avisos_formacion",regavi.partner_ids,regavi.id)
                for obj in objconfrefav.search([]):
                    obj.write({'active': False})

    @api.model
    def cron_planautocontrol(self):
        """ Revisamos el personal proximo a  caducar"""
        cr = self.env.cr
        diaspend = 0
        fmt = '%Y-%m-%d'
        fecha = datetime.datetime.now()
        # Registros con sondas
        objconfavisos = self.env['appcc.config.avisos']
        objconfrefav  = self.env['appcc.revisareg']
        regsavisos    = objconfavisos.search([('active', '=', True), ('tipoaviso', '=', 'P'), ('tipodeplan_id.habilitaformacion', '=', False), ('tipodeplan_id.habilitaavisos', '!=', False)])
        print "AVISOS PLAN CONTROL DE PLAGAS"
        print regsavisos
        for regavi in regsavisos:
            regcreados = []

            objs_planauto = self.env['appcc.planautocontrol'].search([('company_id', '=', regavi.company_id.id), ('manautctrl_id.tpplancontrol_id', "in", [regavi.tipodeplan_id.id])
                                                                         ,('manautctrl_id.tpplancontrol_id.habilitaavisos', '!=', False)],limit=1)

            for planforma in objs_planauto:
                _fecal_str = planforma.fecha
                _fecal   = datetime.datetime.strptime(_fecal_str, fmt)
                ndias    = ((planforma.frecuencia_id.nounidades) / 24) - regavi.diasdesfase
                d_fecal1 = _fecal + datetime.timedelta(days=ndias)
                d_fecal2 = d_fecal1 + datetime.timedelta(days=2 * regavi.diasdesfase)
                if d_fecal1 <= fecha and fecha <= d_fecal2:
                    newobj = objconfrefav.create(
                        {'fechaultima': _fecal_str, 'fechaaudit': fecha,
                         'procedimento_id': planforma.id, 'desfase': ndias, 'tipo': 'V',
                         'name': planforma.manautctrl_id.name,
                         'confavisos_id': regavi.id})
                    print newobj
                    regcreados.append(newobj)

            if len(regcreados) != 0:
                print regavi.partner_ids
                idok = self._send_mail_desfase("email_control_plagas", regavi.partner_ids, regavi.id)
                for obj in objconfrefav.search([]):
                    obj.write({'active': False})


    @api.multi
    def _send_mail_desfase(self,template_xmlid,partner_ids,pid ):
        res = False
        data_pool     = self.env['ir.model.data']
        mail_pool     = self.env['mail.mail']
        template_pool = self.env['mail.template']

        # Ubicamos solo destinatario de AVISOS EMAIL
        email_dir = ', '.join(map(lambda x: x, (str(partner.email) for partner in
                                                partner_ids)))

        dummy, template_id = data_pool.get_object_reference('appcc', template_xmlid)
        email = template_pool.browse(template_id)
        email.email_to = email_dir
        mail_id = email.send_mail(pid, force_send=True)
        if mail_id:
            res = mail_pool.send([mail_id])
        return res


    @api.model
    def action_genera_revision(self):
        cr  = self.env.cr
        hoy = datetime.datetime.now().strftime('%Y-%m-%d')
        objconfavisos  = self.env['appcc.config.avisos']
        objconfrefav   = self.env['appcc.revisareg']
        regsavisos     = objconfavisos.search([('tipoaviso','=','R')])
        fecha          = datetime.datetime.now()
        if objconfrefav.search([('fechaaudit','=',fecha.strftime("%Y-%m-%d")),('confavisos_id','=',self.id)],limit=1):
            objconfrefav.search([('fechaaudit','=',fecha.strftime("%Y-%m-%d")),('confavisos_id','=',self.id)]).unlink()
        for reg in regsavisos:
            regcreados = []
            for detreg in reg.detreg_ids:
                #Unicamente para registros que tengan inicio anteriores a la fecha actual
                if detreg.fecha<=hoy:
                    sql  = """select min(start_date) ufecha from appcc_registros where (state is null or state='draft') and detreg_id= %s  """ % detreg.id
                    cr.execute(sql)
                    registros = cr.dictfetchall()
                    row=registros[0]
                    if row['ufecha']:
                        ultimafecha  = datetime.datetime.strptime( row['ufecha'] if row['ufecha'] else detreg.fecha, "%Y-%m-%d" )
                        ndias        = detreg.frecuencia_id.nounidades/24
                        fechaini     = ultimafecha
                        diaspend     = abs(fecha-fechaini).days
                        if diaspend > reg.diasdesfase+ndias  :
                            newobj=objconfrefav.create({ 'fechaultima': ultimafecha.strftime("%Y-%m-%d"),'fechaaudit':fecha.strftime("%Y-%m-%d"), 'detreg_id': detreg.id, 'desfase': diaspend,'tipo': 'D', 'name': detreg.name,
                                                         'confavisos_id': reg.id})
                            regcreados.append(newobj)
                #print "Numero de registros creados ....%s " % len(newobj)
                #print newobj
            if len(regcreados)!=0:
                idok =self._send_mail_desfase("email_avisos_desfase",reg.partner_ids,reg.id)
                self.env["appcc.revisareg"].write({'active': False})


#Crear en revision registros accesso al plan de formacion para que genere el email


class ApccRevisaRegistro(models.TransientModel):
    _name        =  'appcc.revisareg'
    _description =  """Genera supervision de registros para generar informe"""

    name               = fields.Char()
    confavisos_id      = fields.Many2one('appcc.config.avisos')
    fechaaudit         = fields.Date()
    fechaultima        = fields.Date()
    detreg_id          = fields.Many2one('appcc.detallesregistros')
    desfase            = fields.Integer(string=_("Número de días"))
    tipo               = fields.Selection([('D','DESFASE'),('A','ALARMA'),('V','VENCIMIENTOS')])
    active             = fields.Boolean(default=True)
    planforma_id       = fields.Many2one('appcc.planformacion')
    procedimento_id    = fields.Many2one('appcc.planautocontrol')



class AppccHistorialRevisiones(models.Model):
    _name        = 'appcc.historialrevisiones'
    _description = 'Actividades del appcc'
    _order       = 'fecharevision'

    #Guardar historial completo del APPC , registros y utilizar campos relacionador
    name            = fields.Char(compute="_compute_version",string=_("Versión"))
    fecharevision   = fields.Date(string=_("Fecha"))
    major           = fields.Integer(string=_("Versión principal"))
    minor           = fields.Integer(string=_("Cambio significativo"))
    revision        = fields.Integer(string=_("Modificación de errores"))
    tecnico_id      = fields.Many2one('res.partner',string=_("Corregido por"), domain=([('company_type','=','person'),('category_id.name','=','VETERINARIO')]))
    coordinador_id  = fields.Many2one('hr.employee',string=_("Revisado por"))

    @api.one
    @api.constrains('major', 'minor','revision','fecharevision')
    def _check_version(self):
        HistorialRev  = self.env['appcc.historialrevisiones']
        ultimarev = HistorialRev.search([])
        if len(ultimarev)!=0:
            ids       = ultimarev.ids
            ultimo    = ids[-1]
            ultimarev = ultimarev.browse(ultimo)
            #En la creacion
            if ultimarev.mapped('major')[0] > self.major:
                raise ValidationError( 'Major incompatible con la anterior')
            if ultimarev.mapped('major')[0] < self.major and ultimarev.mapped('minor')[0]> self.minor:
                raise ValidationError( 'Minor incompatible con la anterior')
            if ultimarev.mapped('major')[0] <=self.major and ultimarev.mapped('minor')[0]<= self.minor and ultimarev.mapped('revision')[0]>self.revision:
                raise ValidationError( 'Revision incompatible con la anterior')
            if ultimarev.mapped('fecharevision')[0] > self.fecharevision:
                raise ValidationError( 'Fecha no valida, existe una posterior')

    #Gestionar la secuencia del control de versiones
    @api.one
    def _compute_version(self):
        self.name = "V.%s.%s.%s" % (self.major,self.minor,self.revision)



class Appcc(models.Model):
    _name        = 'appcc'
    _description = 'Analisis de peligros y puntos de control criticos'
    _unique      = ('company_id','revision_id')

    def attachment_tree_view(self, cr, uid, ids, context):
        domain = ['&', ('res_model', '=', 'appcc'), ('res_id', 'in', ids)]
        res_id = ids and ids[0] or False
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
        }

    @api.one
    def _get_attached_docs(self):
        res = {}
        attachment = self.env['ir.attachment']
        appcc_attachments = attachment.search_count( [('res_model', '=', 'appcc'), ('res_id', '=', self.id)] )
        res  = appcc_attachments or 0
        self.doc_count = res

    def planes_tree_view(self, cr, uid, ids, context):
            domain = [('appcc_id', 'in', ids)]
            res_id = ids and ids[0] or False
            return {
                'name': _('Planes'),
                'domain': domain,
                'res_model': 'appcc.manualautocontrol',
                'type': 'ir.actions.act_window',
                'view_id': False,
                'view_mode': 'tree,form',
                'view_type': 'form',
                'limit': 80,
                'context': "{'default_res_id': %d}" % res_id
            }

    @api.one
    def _get_num_planes(self):
        i=0
        for planes in self.planautoctrl_ids:
            i=i+1
        self.num_planes = i

    fecimplanta       = fields.Date(string=_("Fecha implatación"), required=True)
    name              = fields.Char(string=_("Denominación"))
    contenido         = fields.Text(string=_("Desc.Actividad"))
    revision_id       = fields.Many2one('appcc.historialrevisiones', string=_("Revisión"), copy=False)
    propietario_id    = fields.Many2one('hr.employee',string=_("Nombre del propietario"))
    coordinadores_ids = fields.Many2many('hr.employee','appcc_coordinador_rel','employee_id','appcc_id',string=_("Coordinadores")) #Campos a relacionar
    tecnicos_ids      = fields.Many2many('res.partner','appcc_veterinarios_rel','employee_id','appcc_id',string=_("Técnicos"), domain=([('company_type','=','person'),('category_id.name','=','VETERINARIO')]))
    company_id        = fields.Many2one('res.company',string=_("Local"), default=lambda self: self.env['res.company']._company_default_get('appcc'), copy=False)
    color             = fields.Integer()
    planautoctrl_ids  = fields.One2many('appcc.manualautocontrol','appcc_id')
    qrimage           = fields.Binary(groups='appcc.group_appcc_tecnicos', copy=False)
    configpass        = fields.Char(string=_("Clave Config") , groups='appcc.group_appcc_tecnicos', copy=False)
    doc_count         = fields.Integer(compute='_get_attached_docs', string="Adjuntar documentos")
    num_planes        = fields.Integer(compute='_get_num_planes', string="Numero de Planes")

    _sql_constraints = [
        ('appcc_uniq', 'unique(revision_id, company_id )', 'La Version del APPCC es unica, genera nueva version!'),

        ]

    def _compute_configpass(self):
        import random, string
        length = 4
        chars = string.ascii_letters + string.digits
        rnd = random.SystemRandom()
        return ''.join(rnd.choice(chars) for i in range(length))


    def get_image(self, value):
        from qrcode import QRCode, ERROR_CORRECT_L
        qr = QRCode(version=1, error_correction=ERROR_CORRECT_L)
        qr.add_data(value)
        qr.make()  ## Generar el codigo QR
        im = qr.make_image()
        fname = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        im.save(fname.name)
        f = open(fname.name, "r")
        data = base64.encodestring(f.read())
        f.close()
        return data

    def generate_image(self, obj, valor):
        """Generamos qr de registro """
        image = self.get_image(valor)
        obj.write({'qrimage': image})
        return True

    @api.one
    def write(self, vals):
        nombre   = self.name
        company  = self.company_id.name
        new_id   = str(self.id)
        version  = self.revision_id.name
        confpass = self._compute_configpass()
        ct     = threading.current_thread()
        ct_db  = getattr(ct, 'dbname', None)
        dbname = tools.config['log_db'] or ct_db
        base_url = self.env['ir.config_parameter'].get_param('web.base.url').replace("http","https")
        codigo = "%s;" \
                 "%s;" \
                 "%s;" \
                 "%s;" \
                 "%s;" \
                 "%s;" \
                 "%s" % (dbname, nombre, new_id, version, base_url, company, confpass)

        image = self.get_image(codigo)
        vals['configpass'] = confpass
        vals['qrimage']    = image
        new_id = super(Appcc, self).write(vals)
        return new_id

    @api.model
    def create(self, vals):
        vals['configpass']=self._compute_configpass()
        new_obj   = super(Appcc, self).create(vals)
        nombre   = new_obj.name
        company  = new_obj.company_id.name
        version  = new_obj.revision_id.name
        confpass = new_obj.configpass
        new_id   = str(new_obj.id)

        ct = threading.current_thread()
        ct_db = getattr(ct, 'dbname', None)
        dbname = tools.config['log_db'] or ct_db
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        codigo = "%s;" \
                 "%s;" \
                 "%s;" \
                 "%s;" \
                 "%s;" \
                 "%s;" \
                 "%s" % (dbname, nombre, new_id, version, base_url, company,confpass)
        image    = self.get_image(codigo)
        vals['qrimage'] = image
        self.generate_image(new_obj, codigo)
        return new_obj

    @api.one
    @api.constrains('name')
    def action_update_appcc(self):
        objappcc = self.env['appcc'].browse([self.id])
        print "Ids de appcc %s  " % objappcc.planautoctrl_ids
        for reg in objappcc.planautoctrl_ids:
            reg.write({'name' : "Plan: %s - %s" % (self.name, reg.tpplancontrol_id.name) })



class AppccManualAutoControl(models.Model):
    """Plan de Autocontrol"""
    _name        = 'appcc.manualautocontrol'
    _description = 'Plan de auto control'
    #_rec_name    =  'tpplancontrol_id'
    _unique       = ('appcc_id','tpplancontrol_id','revision_id')

    name             = fields.Char(string=_("Denominación"))
    appcc_id         = fields.Many2one('appcc',deafult= lambda self: [('company_id.id','=', self.env['res.company']._company_default_get('appcc.manualautocontrol').id)] , string=_("APPCC"),required=True)
    categoria_id     = fields.Many2one('appcc.maestros.categorias',string=_("Categorias"))
    objeto           = fields.Text(string=_("Objeto"))
    alcance          = fields.Text(string=_("Alcance"))
    contenido        = fields.Text(string=_("Contenido"))
    marcolegal       = fields.Text(string=_("Marco Legal"))
    procedimiento    = fields.Text(string=_("Procedimiento documental"))
    tpplancontrol_id = fields.Many2one('appcc.maestros.tpplancontrol', string=_("Tipo plan de control"), required=True )
    #Se autocompletan cuando se selecciona  appcc_id
    company_id       = fields.Many2one('res.company',related='appcc_id.company_id', store=True, readonly=True)
    revision_id      = fields.Many2one('appcc.historialrevisiones', string=_("Revisión"), required=True)
    manautctrl_ids   = fields.One2many('appcc.planautocontrol','manautctrl_id')


    @api.constrains('appcc_id','tpplancontrol_id')
    @api.one
    def _get_company(self):
        regs=0
        self.name = "Plan: %s - %s" % (self.appcc_id.name, self.tpplancontrol_id.name)
        regs =self.env['appcc.planautocontrol'].search_count([('manautctrl_id','=',self.id)])
        if regs>0:
            message="No se puede modificar MANUAL APPCC, existen Planes de autocontrol "
            raise ValidationError(message)

        regs=self.env['appcc.cabregistros'].search_count([('manautctrl_id','=',self.id)])
        if regs>0:
            message="No se puede modificar MANUAL APPCC, existen Registros de control "
            raise ValidationError(message)

        self.name = "Plan: %s - %s" % (self.appcc_id.name, self.tpplancontrol_id.name)



class AppccPlanFormacion(models.Model):
    _name = 'appcc.planformacion'
    _description = 'Plan de formacion'
    _rec_name    =  'personal_id'

    manautctrl_id    = fields.Many2one('appcc.manualautocontrol', string=_("Plan"))
    frecuencia_id    = fields.Many2one('appcc.maestros.tpfrecuencias', string=_("Frecuencia"), required=True)
    personal_id      = fields.Many2one('hr.employee', string=_("Personal"), required=False, domain=lambda self: [
        ('department_id.company_id.id', '=', self.env['res.company']._company_default_get('appcc.planformacion').id)])
    tercero_id       = fields.Many2one('res.partner', string=_("Imparte el Curso"), required=False,
                                       domain=([('category_id.name', '=', 'FORMACION')]))
    fechavalida      = fields.Date(string =_("Fecha Certificacion"),required=True )
    tiposcursos_ids  = fields.Many2many('appcc.maestros.tpcursos','appcc_planforma_tpcursos_rel','plforma_id','tpcurso_id',string="Cursos Recibidos")
    company_id       = fields.Many2one('res.company', related='manautctrl_id.company_id', store=True, readonly=True)
    active           = fields.Boolean(default=True)

    #Generar cron para aviso de vencimiento o renovacion de cursos comunicar por email

    @api.model
    def create(self, vals):

        obj_tpplan = self.env['appcc.maestros.tpplancontrol'].search([('habilitaformacion','=', True)])

        if len(obj_tpplan)==1:

            obj_manualctrl_id = self.env['appcc.manualautocontrol'].search([ ('tpplancontrol_id.id','=',obj_tpplan.id), ('company_id.id', '=', self.env['res.company']._company_default_get('appcc.planformacion').id)])
            print obj_manualctrl_id
            if len(obj_manualctrl_id)==1:
                vals['manautctrl_id'] = obj_manualctrl_id.id
                new_id = super(AppccPlanFormacion, self).create(vals)
                return new_id
            else:
                raise UserError("No se crea, no esta definido el Plan de Formación o inexistente")
        else:
            raise UserError("No se crea, Tipo de plan de formacion no se encuentra indicado")



class AppccPlanAutoControl(models.Model):
    """Procedimiento de trabajo"""
    _name        = 'appcc.planautocontrol'
    _description = 'Procedimientos de trabajo'
    #_rec_name    =  'manautctrl_id'

    manautctrl_id   = fields.Many2one('appcc.manualautocontrol', string=_("Plan"), required=True)
    frecuencia_id   = fields.Many2one('appcc.maestros.tpfrecuencias', string=_("Frecuencia"), required=True )
    zonas_ids       = fields.Many2many('stock.location', string=_("Zona"),required=True, domain = lambda self: [('company_id.id','=', self.env['res.company']._company_default_get('appcc.planautocontrol').id)])
    zonalimpieza    = fields.Text(string=_("Descripción de la zona"), required=False)
    #proclimpieza no esta en uso en appcc_view
    proclimpieza    = fields.Text(string=_("Instrucciones"),required=False)
    tercero_id      = fields.Many2one('res.partner', string=_("Mantenedor"),required=False, domain=([('category_id.name','=','MANTENEDOR')]))
    operaciones     = fields.Text(string=_("Operaciones"), required=True)
    equipos_ids     = fields.Many2many('asset.asset', string=_("Equipos") , required=False)
    productos_ids   = fields.Many2many('product.product',string=_("Productos"),required=False)
    personal_ids    = fields.Many2many('hr.employee', string=_("Personal"),required=False ,domain = lambda self: [('department_id.company_id.id','=', self.env['res.company']._company_default_get('appcc.planautocontrol').id)])
    fecha           = fields.Date( string=_("Fecha"),required=True)
    tpmedvig_id     = fields.Many2one('appcc.maestros.tpmedvigilancia',string=_("Medidas de vigilancia"),required=True,)
    tpmedactp_id    = fields.Many2one('appcc.maestros.tpmedactuacion',string=_("Medidas de actuacion preventivas"),required=True, domain=([('tipo','=','P')]))
    tpmedactc_id    = fields.Many2one('appcc.maestros.tpmedactuacion',string=_("Medidas correctivas"),required=True,domain=([('tipo','=','C')]))
    observaciones   = fields.Text(required=False,string="")
    revision_id     = fields.Many2one('appcc.historialrevisiones',string=_("Revisión"),required=True)
    consumibles_ids = fields.One2many('appcc.consumibles',inverse_name="planautctrl_id",string=_("Consumibles"))
    valanali_ids    = fields.One2many('appcc.valoresanaliticas',inverse_name="planautctrl_id",string="")
    company_id      = fields.Many2one('res.company',related='manautctrl_id.company_id', store=True, readonly=True)
    name            = fields.Char(string=_("Denominación"))

    # @api.constrains('manautctrl_id')
    # def _get_company(self):
    #     self.name = "Procedimiento: %s" % self.manautctrl_id.name


    @api.one
    @api.constrains('zonas_ids','equipos_ids')
    def _check_zonas(self):
        if self.zonas_ids ==False:
            raise ValidationError("Seleccione una zona primero")


class AppccConsumiblesDosis(models.Model):
    _name        = 'appcc.consumibles'
    _description = 'Dosis Consumibles'

    planautctrl_id  =  fields.Many2one('appcc.planautocontrol', string=_("Procedimiento"))
    consumible_id   =  fields.Many2one('product.product', string=_("Productos Limpieza"))
    name            =  fields.Char(string=_("Dosis"),help=_("Cantidad de producto"))
    dosis           =  fields.Char(string=_("Dosificación"),help=_("Forma de dosificar el producto"))
    company_id      =  fields.Many2one('res.company',related='planautctrl_id.company_id', store=True, readonly=True)



class AppccValoresAnaliticas(models.Model):
    _name        = 'appcc.valoresanaliticas'
    _description = 'Valores Analiticas'
    _rec_name    =  'paramanali_id'

    planautctrl_id  =  fields.Many2one('appcc.planautocontrol', string=_("Plan"))
    paramanali_id  = fields.Many2one('appcc.maestros.paraanalisis',string=_("Parámetro"))
    valores        = fields.Float(digits=(12,4) , string=_("Valor"), help=_("Introduzca valor de referencia"))
    tolerancia     = fields.Integer( string=_("Margen de tolerancia"))



class ApccCabRegistros(models.Model):
    _name       = 'appcc.cabregistros'
    _description = 'Cabecera de Registros'

    name            = fields.Char(string =_("Denominación"), required=True)
    tpmedvig_id     = fields.Many2one('appcc.maestros.tpmedvigilancia', string=_("Medidas de vigilancia"))
    tpmedactc_id    = fields.Many2one('appcc.maestros.tpmedactuacion',  string=_("Medidas correctivas"), required=True, domain=([('tipo','=','C')]))
    company_id      = fields.Many2one('res.company',related='manautctrl_id.company_id', store=True, readonly=True)
    manautctrl_id   = fields.Many2one('appcc.manualautocontrol', string=_("Plan de autocontrol"), required=True)
    revision_id     = fields.Many2one('appcc.historialrevisiones', string=_("Revisión"))
    cabreg_ids      = fields.One2many('appcc.detallesregistros','cabreg_id' , string=_("Registros"),copy=False)
    evalua_ids      = fields.One2many('appcc.evaluacion','regeval_id' , string=_("Evaluación"))



class AppccCalendarCalc(models.TransientModel):
    _name = 'appcc.calendarcalc'
    _description = 'Temporal calculo calendario registros'

    def init(self, cr):
        cr.execute(""" DROP INDEX IF EXISTS  appcc_calendarcal_detreg_sd_index """)

        cr.execute("""CREATE INDEX appcc_calendarcal_detreg_sd_index
                        ON public.appcc_calendarcalc USING btree
                    (detreg_id, start_date)
                        TABLESPACE pg_default""")

    start_date = fields.Date(index=True)
    detreg_id  = fields.Integer(index=True)
    activo     = fields.Boolean(default=True)
    activo_eje = fields.Boolean(default=True)


    @api.multi
    def _validarExcepcion(self,diapro,company_id):
        """
        Valida Excepcion de calendario forzando para frecuencias mayor que uno una nueva fecha, casos
        de frecuencia semanal, quincenal etc..
        :param fecha:  date
        :param frec: integer
        :return: integer
        """
        fmt          = '%Y-%m-%d'
        for row in self.search([]):

            fecha        = row.start_date
            objfestivos  = self.env['appcc.maestros.festivos']
            objexcepcio  = self.env['appcc.excepcalendar']
            #company_id   = self.env['res.company']._company_default_get('appcc.detallesregistros').id
            search_exec  = [('company_id','=',company_id),('fechaini','<=',fecha),('fechafin','>=',fecha),('activo','=',True)]
            search_fest  = [('fechaini','<=',fecha),('fechafin','>=',fecha),('name','in',['FESTIVO NACIONAL','FESTIVO AUTONOMICO']),('activo','=',True)]
            numexcepcio  = objexcepcio.search_count(search_exec)
            numfestloca  = objfestivos.search_count(search_exec)
            numfestivos  = objfestivos.search_count(search_fest)

            #print "Fecha: %s Excepcion %s Festivo Local %s Festivos %s " % (fecha,numexcepcio,numfestloca,numfestivos)
            if not ( numexcepcio==0 and numfestloca == 0 and numfestivos==0 ):
                row.activo=False

            dfecha = datetime.datetime.strptime(fecha,fmt)
            #Valida si es dia en el que se puede ejecutar
            if not fechaEjecucion(dfecha,diapro):
                row.activo_eje=False

    @api.multi
    def deleteAll(self):
        for row in self.search([]):
            row.unlink()



class AppccDetallesRegistros(models.Model):
    _name       = 'appcc.detallesregistros'
    _description = 'Detalles de Registros'

    name               = fields.Char(string =_("Denominación"))
    fecha              = fields.Date(string =_("Fecha inicio"),required=True )
    cabreg_id          = fields.Many2one('appcc.cabregistros',string=_("Registro"), required=True)
    actividades_id     = fields.Many2one('appcc.maestros.actividades', string=_("Actividades"), required=True, domain=[('agenda','=',True)])
    tplimitcrit_id     = fields.Many2one('appcc.maestros.tpmlimitescriticos', string=_("Límites críticos"),required=True)
    zonas_id           = fields.Many2one('stock.location',string=_("Zonas") ,required=True, domain = lambda self: [('company_id.id','=', self.env['res.company']._company_default_get('appcc.detallesregistros').id)])
    equipos_id         = fields.Many2one('asset.asset',string=_("Equipos"),required=True)
    indicador_id       = fields.Many2one('appcc.maestros.tiposindicador', string=_("Indicador a controlar"),required=True)
    ordagenda          = fields.Selection(HORAS,string=_("Hora agenda"), required=True )
    frecuencia_id      = fields.Many2one('appcc.maestros.tpfrecuencias', string=_("Frecuencia"), required=True)
    diaejecuta         = fields.Selection(OPCIONES_DIAS_1, string=_("Día ejecución") ,help="Para dias de semana especificos hacer coincidir la ultima fecha del registro con el día de la semana a parametrizar")
    tpturnos_id        = fields.Many2one('appcc.maestros.tpturnos', string=_("Turno"),required=True)
    company_id         = fields.Many2one('res.company',string="Empresa",related='cabreg_id.company_id', store=True, readonly=True)
    revision_id        = fields.Many2one('appcc.historialrevisiones', string=_("Revisión"),required=True)
    detreg_ids         = fields.One2many('appcc.registros','detreg_id',copy=False)
    tracksonda_id      = fields.Many2one('tracksonda',"Sonda asociada")
    active             = fields.Boolean(string="Activo",default=True)
    departamento_ids   = fields.Many2many('hr.department','appcc_detreg_depart_rel','detreg_id','departamento_id', string="Departamento Asignado")
    tpadquisicion      = fields.Selection(TIPOLECTURA,string="Tipo Adquisicion", default="M")
    qrimage            = fields.Binary(groups='appcc.group_appcc_tecnicos', copy=False)


    @api.one
    def write(self, vals):
        adqui  = vals.get('tpadquisicion',self.tpadquisicion)

        if adqui != "M":
            nombre = self.name
            max = self.tplimitcrit_id.indicador_id.vmax
            min = self.tplimitcrit_id.indicador_id.vmin
            company = self.company_id.name
            equipos = self.equipos_id.name
            serial  = self.equipos_id.serial or " "
            new_id = str(self.id)
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            ct = threading.current_thread()
            ct_db = getattr(ct, 'dbname', None)
            dbname = tools.config['log_db'] or ct_db
            codigo = "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s" % (nombre, new_id, str(max), str(min), equipos, serial, dbname, company)
            image = self.get_image(codigo)
            vals['qrimage'] = image
        new_id = super(AppccDetallesRegistros, self).write(vals)
        return new_id

    @api.model
    def create(self,vals):
        adqui  =vals['tpadquisicion']
        nombre =vals['name']
        new_obj = super(AppccDetallesRegistros, self).create(vals)
        if adqui !='M':
            max = new_obj.tplimitcrit_id.indicador_id.vmax
            min = new_obj.tplimitcrit_id.indicador_id.vmin
            company = new_obj.company_id.name
            equipos = new_obj.equipos_id.name
            serial  = new_obj.equipos_id.serial or " "
            new_id = str(new_obj.id)
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            ct = threading.current_thread()
            ct_db = getattr(ct, 'dbname', None)
            dbname = tools.config['log_db'] or ct_db
            codigo = "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s;" \
                     "%s" % (nombre, new_id, str(max), str(min), equipos, serial, dbname, company)
            self.generate_image(new_obj,codigo)
        return new_obj

    def get_image(self, value):
        from qrcode import QRCode,ERROR_CORRECT_L
        ##qr = QRCode(version=7, error_correction=ERROR_CORRECT_L)
        qr=QRCode()
        qr.add_data(value)
        qr.make()  ## Generar el codigo QR
        im = qr.make_image()
        fname = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        im.save(fname.name)
        f = open(fname.name, "r")
        data =  base64.encodestring(f.read())
        f.close()
        return data


    def generate_image(self,obj,valor):
        """Generamos qr de registro """
        image = self.get_image(valor)
        obj.write( {'qrimage':image} )
        return True


    @api.onchange('equipos_id')
    def onchange_equipos(self):
        if self.equipos_id:
            self.zonas_id = self.equipos_id.property_stock_asset.id



    @api.onchange('actividades_id','equipos_id')
    def putName(self):
        if self.actividades_id.name and self.equipos_id.name:
            self.name = "%s - %s " % (self.actividades_id.name,self.equipos_id.name)



    @api.onchange('cabreg_id')
    def onchange_cabreg_id(self):
        res={}
        if not res.get('domain', {}):
            res['domain'] = {}
        aids=[]
        zids=[]
        zonas_ids = self.cabreg_id.manautctrl_id.manautctrl_ids.zonas_ids
        asset_ids = self.cabreg_id.manautctrl_id.manautctrl_ids.equipos_ids


        #zonas_ids = self.env['stock.location'].search_read([('id','in',self.cabreg_id.manautctrl_id.zonas_id.id)],['id'])
        #asset_ids = self.env['asset.asset'].search_read([('id','in',self.cabreg_id.manautctrl_id.equipos_id.id)],['id'] )
        # print zonas_ids
        # print "-----------------"
        # print asset_ids
        # if asset_ids:
        #     for sto in asset_ids:
        #          aids.append(sto['id'])
        #     for zto in asset_ids:
        #          zids.append(zto['id'])
        #     if asset_ids:
        #         res['domain']['equipos_id'] = [('id','in', aids)]
        #     if zonas_ids:
        #         res['domain']['zonas_id'] = [('id','in', zids)]
        return res


    @api.constrains('cabreg_id')
    def _get_companyc(self):
        self.company_id = self.cabreg_id.company_id.id


    @api.constrains('diaejecuta','fecha')
    def valida_diaejecuta(self):
        diapro   = self.diaejecuta
        dfecha   = datetime.datetime.strptime(self.fecha,"%Y-%m-%d")
        if not fechaEjecucion(dfecha,diapro):
            raise ValidationError("¡La Fecha inicio no coincide con el Dia de ejecucion!")


    def _esHoy(self,dias,difedia,diapro,fecha):
        #Ver si cae fin de semana, configuración de la frecuencia
        if dias > difedia:
             return False
        else:
            if fechaEjecucion( fecha, diapro):
                #print "Verifica fecha de ejecucion"
                return True
            else:
                return False


    @api.model
    def action_button_generaragenda(self):
        """ Proceso automatico de creación de agenda
            Este proceso es independiente del usuario, se generan todas las agendas en todas las empresas del grupo
        """
        cr = self.env.cr
        diaspend     = 0
        fmt          = '%Y-%m-%d'
        fechafin     = datetime.datetime.today()
        objdetregis  = self.env['appcc.detallesregistros']
        objregistro  = self.env['appcc.registros']
        objcompa     = self.env['res.company'].search([])
        objcalendar  = self.env['appcc.calendarcalc']
        ultimafecha  =""
        """ Revisamos la agenda por empresa"""
        for regs in objcompa:
            # Limpiamos temporal de calculo
            objcalendar.deleteAll()
            #print "---------------------------- Entramos en local --> %s " % regs.name
            objdetreg = objdetregis.search([('company_id','=',regs.id), ('actividades_id.agenda','=',True)])
            for objdet in objdetreg:
                diaejecuta  = objdet.diaejecuta
                dias        = objdet.frecuencia_id.nounidades/24
                #Ultimo registro completado
                sql = """select max(start_date) ufecha from appcc_registros where  detreg_id= %s  """ % objdet.id
                cr.execute(sql)
                registros = cr.dictfetchall()
                row=registros[0]
                #Discriminamos el primer registro
                if row['ufecha']:
                    inifec = row['ufecha']
                    inireg = False
                else:
                    inifec=objdet.fecha
                    inireg= True
                    objregistro.create({'start_date': inifec, 'detreg_id': objdet.id,
                                        'horarioturno_id': objdet.tpturnos_id.id})


                ultimafecha  = datetime.datetime.strptime( inifec,fmt)
                fechaini     = ultimafecha
                diaspend     = (fechafin-fechaini).days
                #print "Dias Pendientes %s " % diaspend
                if diaspend > 0:
                    #Generamos todas las fechas pendientes en temporal calendario
                    for i in range(diaspend+1):
                        #print "Crea Calendario"
                        record_fecha = ultimafecha + datetime.timedelta(days=i) #coloca la fecha en el ultimo dia de la excepcion
                        char_fecha   = datetime.datetime.strftime(record_fecha,fmt)
                        objcalendar.create({'start_date': char_fecha, 'detreg_id': objdet.id  })

                    #Revisamos todas las fechas pendientes y marcamos las NO DISPONIBLES
                    objcalendar._validarExcepcion(diaejecuta,regs.id)

                    ant_siguiente=False
                    for row in objcalendar.search([('detreg_id','=',objdet.id)], order='start_date'):
                        #Reglas
                        dfecha       = datetime.datetime.strptime(row.start_date,fmt)
                        diffdias     = (dfecha-fechaini).days
                        #print "Diferencia de dias %s --> dias %s " % (diffdias,dias)
                        #print "Fecha %s" % dfecha
                        #print "Fecha ini %s " % fechaini

                        if row.activo_eje and diffdias >= dias:
                            fechaini = datetime.datetime.strptime(row.start_date, fmt)
                            ant_siguiente = True
                        else:
                            if not ant_siguiente:
                                ant_siguiente =False
                        #print "Fecha %s Festivos %s Ejecucion %s Siguiente %s Dias %s diffdias %s " % (row.start_date,row.activo,row.activo_eje,ant_siguiente,dias,diffdias)
                        #print "Fecha registro Inicio %s" % inireg
                        if ant_siguiente and row.activo:
                            #fechaini = datetime.datetime.strptime(row.start_date, fmt)
                            #print "Entra en ant_siguiente"
                            if self._esHoy(dias,diffdias,diaejecuta,fechaini): #Si existe excepcion se salta la validacion
                                #print "Inserta Fecha %s  registro --> %s"  % (row.start_date,objdet.name)
                                objregistro.create({'start_date':row.start_date, 'detreg_id': objdet.id, 'horarioturno_id' : objdet.tpturnos_id.id})
                            ant_siguiente = False

    @api.model
    def cron_calculate_temp_cinetica(self):
        cr = self.env.cr
        DH     =  83.14472 #KJ/MOLE ENERGIA DE ACTIVACION
        GCR    =  8.314472 # KJ/MOLE/C CONSTANTE DE LOS GASES
        KELVIN =  273.15   #CERO ABSOULUTO
        diaspend = 0
        fmt = '%Y-%m-%d'
        fechafin = datetime.datetime.today()
        objdetregis = self.env['appcc.detallesregistros'].search([('tracksonda_id', '!=', False),('indicador_id.tipocalculo','=','TC')])
        objregistro = self.env['appcc.registros']
        fechaini = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        for objdet in objdetregis:
            hini = objdet.tracksonda_id.hub_id.ihora
            hfin = objdet.tracksonda_id.hub_id.fhora
            tracksonda_id = objdet.tracksonda_id.id
            if hfin == False or hini == False:
                hini = 0
                hfin = 23
            sql_1 = """select max(start_date) ufecha from appcc_registros where state='done' and detreg_id= %s  """ % objdet.id
            sql_2 = """select valor medtemp from tracksonda_loaddatson where  tiempo >=%s and tiempo <=%s and tracksonda_id = %s order by tiempo """
            cr.execute(sql_1)
            registros = cr.dictfetchall()
            row = registros[0]
            fechaini = datetime.datetime.strptime(row['ufecha'] if row['ufecha'] else objdet.fecha, fmt)
            # Fecha desde que inciamos el calculo de registro
            diaspend = (fechafin - fechaini).days
            for dia in range(0, diaspend):
                # Calculamos dia a buscar.
                fecha = fechaini + datetime.timedelta(days=dia)
                # Tramo Madrugada
                fecha1ini = datetime.datetime(fecha.year, fecha.month, fecha.day, 0, 1)
                fecha2fin = datetime.datetime(fecha.year, fecha.month, fecha.day, 23, 59)
                cr.execute(sql_2, (fecha1ini, fecha2fin, tracksonda_id))
                valores1 = cr.dictfetchall()
                numero_datos =0
                denominador  =0
                print valores1
                for regval in valores1:
                    numero_datos = numero_datos +1
                    temp= regval["medtemp"]
                    const = np.math.exp(-1*DH/(GCR*(temp+KELVIN)))
                    denominador= const + denominador

                if numero_datos!=0:
                    tc_med = ((DH/GCR) / (-1* np.math.log(denominador/numero_datos)))-KELVIN
                    objreg = objregistro.search(
                        [('start_date', '=', fecha.strftime('%Y-%m-%d')), ('detreg_id', '=', objdet.id)], limit=1)
                    if objreg:
                        objreg.write(
                            {'valor': tc_med, 'observaciones': "Registros automatizado sonda SIVA", 'state': 'done'})
                    else:
                        objregistro.create({'valor': tc_med, 'start_date': fecha.strftime('%Y-%m-%d'), 'state': 'done',
                                            'detreg_id': objdet.id,
                                            'observaciones': "Registros automatizado sonda SIVA"})


    @api.model
    def cron_calculate_valor(self):
        """ Revisamos todos los registros con sondas y procedemos a su calculo, se genera desde el utltimo """
        cr = self.env.cr
        diaspend     = 0
        fmt          = '%Y-%m-%d'
        fechafin     = datetime.datetime.today()
        #Registros con sondas
        objdetregis  = self.env['appcc.detallesregistros'].search([('tracksonda_id','!=',False),('indicador_id.tipocalculo','in',['N',False])])
        objregistro  = self.env['appcc.registros']
        """ Revisamos todos los registros con sondas y """
        for objdet in objdetregis:
            #Calculo horacion operaciones
            hini          = objdet.tracksonda_id.hub_id.ihora
            hfin          = objdet.tracksonda_id.hub_id.fhora
            tracksonda_id = objdet.tracksonda_id.id
            if hfin == False  or hini== False:
                hini=7
                hfin=19

            fechaini  = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
            #Ultimo registro completado
            sql_1 = """select max(start_date) ufecha from appcc_registros where state='done' and detreg_id= %s  """ % objdet.id
            sql_2 = """select avg(valor) medtemp from tracksonda_loaddatson where  tiempo >=%s and tiempo <=%s and tracksonda_id = %s """
            cr.execute(sql_1)
            registros = cr.dictfetchall()
            row=registros[0]
            fechaini  = datetime.datetime.strptime( row['ufecha'] if row['ufecha'] else objdet.fecha,fmt)
            #Fecha desde que inciamos el calculo de registro
            diaspend = (fechafin-fechaini).days
            for dia in range(0,diaspend):
                #Calculamos dia a buscar.
                fecha =  fechaini +datetime.timedelta(days=dia)
                #Tramo Madrugada
                fecha1ini = datetime.datetime(fecha.year,fecha.month,fecha.day,0,1)
                fecha2ini = datetime.datetime(fecha.year,fecha.month,fecha.day,hini,0)
                #Tramo Noche
                fecha1fin = datetime.datetime(fecha.year,fecha.month,fecha.day,hfin,0)
                fecha2fin = datetime.datetime(fecha.year,fecha.month,fecha.day,23,59)

                #print "Fechas %s %s %s %s" % (fecha1ini,fecha2ini,fecha2ini,fecha2fin)

                cr.execute(sql_2,(fecha1ini,fecha2ini,tracksonda_id))
                valores1 = cr.dictfetchall()
                val1=valores1[0]["medtemp"]

                cr.execute(sql_2,(fecha1fin,fecha2fin,tracksonda_id))
                valores2 = cr.dictfetchall()
                val2=valores2[0]["medtemp"]

                #print "Valores %s %s" % (val1,val2)

                if val2 or val1:
                    if val1 is None:
                        val1=val2
                    if  val2 is None:
                        val2=val1
                    #Calculamos valor de temperatura proemedio con un ponderado de la media
                    mediatemp = round( (val1*(hini-0) + val2*(24-hfin)  )/ (hini+(24-hfin)) ,2)

                    objreg=objregistro.search([('start_date','=',fecha.strftime('%Y-%m-%d')),('detreg_id','=',objdet.id)],limit=1)
                    if objreg:
                        objreg.write({ 'valor': mediatemp, 'observaciones': "Registros automatizado sonda SIVA" , 'state': 'done' })
                    else:
                        objregistro.create({ 'valor': mediatemp, 'start_date': fecha.strftime('%Y-%m-%d'), 'state': 'done', 'detreg_id' : objdet.id,
                                             'observaciones': "Registros automatizado sonda SIVA"})



class AppccRegistrosFirmas(models.Model):
    _name = 'appcc.registros.firmas'
    _description = 'Control de firmas de registros'

    image      = fields.Binary("Image", attachment=True )
    date_firma = fields.Datetime(default=datetime.datetime.now())
    fecha_rel  = fields.Date() #Fecha de relacion con registros a firmar
    firma_id   = fields.Many2one('hr.employee', string=_("Firmar registro"))



class AppccRegistrosTask(models.Model):
    _name       = 'appcc.registros'
    _description = 'Registros'
    _unique=('detreg_id','start_date','horarioturno_id')
    _order= 'detreg_id,start_date'

    @api.one
    def _getFirma(self):
        imagen = None
        obj_firmas = self.env["appcc.registros.firmas"]
        print "Fecha : %s  Firma id %s " % (self.start_date, self.firmas_id.id)
        firmareg = obj_firmas.search([('fecha_rel', '=', self.start_date), ('firma_id', '=', self.firmas_id.id)],
                                     limit=1)

        if firmareg.image:
            imagen = firmareg.image

        self.imgfirma = imagen

    def _getdefault_employee(self):
        idemp = self.env['hr.employee'].search([ ('user_id','=',self.env.user.id),('department_id.company_id.id','=', self.env['res.company']._company_default_get('appcc.registros').id)],limit=1)
        if idemp:
            return idemp[0].id
        else:
            return None

    detreg_id          = fields.Many2one('appcc.detallesregistros', required=True, index=True)
    valor              = fields.Float(digits=(10,2), string=_("Valor"), group_operator="avg")
    estado             = fields.Boolean(index=True, default=False, string=_("Estado check"))
    observaciones      = fields.Char(string=_("Observaciones"),help=_("Incidencias detectadas"))
    firmas_id          = fields.Many2one('hr.employee',string=_("Firmar registro") , domain = lambda self: [ ('user_id','=',self.env.user.id),('department_id.company_id.id','=', self.env['res.company']._company_default_get('appcc.registros').id)]) ##FILTRAR POR CATEGORIA DE ETIQUETAS
    horarioturno_id    = fields.Many2one('appcc.maestros.tpturnos', string=_("Horario turno"))
    company_id         = fields.Many2one('res.company', string="Empresa",related='detreg_id.company_id', store=True, readonly=True)
    color              = fields.Char(related='detreg_id.actividades_id.color', store=True, readonly=True, copy=False)
    tipo               = fields.Char()
    state              = fields.Char()
    start_date         = fields.Date("Fecha Programada",required=True, index=True)
    start              = fields.Datetime()
    stop               = fields.Datetime()
    stop_date          = fields.Date("Fecha Realizada")
    start_datetime     = fields.Datetime()
    stop_datetime      = fields.Datetime()
    name               = fields.Char()
    incidencia         = fields.Boolean(string=_("Incidencia"),default=False)
    textoincidencia    = fields.Char()
    actividad_id       = fields.Many2one("appcc.maestros.actividades",related="detreg_id.actividades_id")
    device             = fields.Char() #Tipo de dispositivo que completa el datos, iOS, android ,etc
    imgfirma           = fields.Binary(compute= "_getFirma", store=False)






    @api.one
    @api.constrains('valor','estado')
    def validarRegistroTarea(self):
        #Iniciamos busquedad registro inmediatamente anterior:
        #Salta la validaciones para las sondas
        if not self.detreg_id.tracksonda_id.id and self.state == 'done':
            self.incidencia = False
            fmt          = '%Y-%m-%d'
            frec         = self.detreg_id.frecuencia_id.nounidades/24
            diaejecuta   = self.detreg_id.diaejecuta
            start_date   = self.start_date
            iddetreg     = self.detreg_id.id
            sql = """select max(start_date) ufecha from appcc_registros where state='done' and detreg_id= %s and start_date!=to_date('%s','YYYY-MM-DD')  """ % (self.detreg_id.id,start_date)
            #print sql
            cr = self.env.cr
            cr.execute(sql)
            regist = cr.dictfetchall()
            row=regist[0]
            numdias=0
            dfecha= row['ufecha']
            #print "Fecha  a verificar %s " % dfecha
            if dfecha:
                for row in self.search([('detreg_id','=',iddetreg)],order='start_date'):
                    #print "Registro en el loop %s registro validado %s " % (row.start_date,start_date)

                    if not row.state == 'done' and row.start_date < start_date:
                        #Registros diferentes de la web
                        if self.device:
                            if row.tipo =="C":
                                row.estado = self.estado
                            else:
                                row.valor  = self.valor
                            row.device         = self.device
                            row.observaciones  = self.observaciones
                            self.state         = None
                            self.valor         = None
                            self.estado        = None
                            self.observaciones = None
                            self.device        = None
                            raise ValidationError("[E:1] Se ha completado el registro de Fecha [%s] con el valor actual" % row.start_date)
                        else:
                            return {'warning': {
                                'title': _('AVISO IMPORTANTE'),
                                'message': _(
                                    'Recuerde completar los registros de fecha "%(registro)s", se encuentran incompletos') % {
                                               'registro': row.start_date},
                            }}
                            #raise ValidationError("Complete el registro de Fecha %s " % row.start_date)
            else:
                sql = """select min(start_date) ufecha, min(tipo) utipo from appcc_registros where state!='done' and detreg_id= %s  """ % (self.detreg_id.id)
                cr = self.env.cr
                cr.execute(sql)
                regist = cr.dictfetchall()
                row=regist[0]
                if row['ufecha']:
                    if row['ufecha'] != start_date:
                        if self.device:
                            objreg= self.search([('detreg_id', '=', self.detreg_id.id),('start_date','=',row['ufecha'])],limit=1)
                            print objreg
                            if row['utipo'] == "C":
                                objreg.estado=self.estado
                            else:
                                objreg.valor=self.valor
                            objreg.device       = self.device
                            objreg.observaciones= self.observaciones
                            self.state          = None
                            self.valor          = None
                            self.estado         = None
                            self.observaciones  = None
                            self.device         = None
                            raise ValidationError("[E:1] Se ha completado el registro de Fecha [%s] con el valor actual" % row['ufecha'])
                        else:
                            raise ValidationError("¡Complete el registro inicial!")

    @api.one
    @api.onchange('valor')
    def validarRegistroRango(self):
        self.state = False
        if self.detreg_id.actividades_id.tipo == "V" and not self.detreg_id.tracksonda_id.id:
            self.stop_date = datetime.datetime.now()
            vmax = self.detreg_id.indicador_id.vmax
            vmin = self.detreg_id.indicador_id.vmin
            valor = float(self.valor)
            warning = {}
            result = {}

            if not (vmin <= valor <= vmax):
                self.state = 'draft'
                texto = 'El valor  %s  introducido se encuentra fuera de los límites de control (%s,%s), si desea continuar genere un Aviso' % (
                valor, vmin, vmax)
                self.textoincidencia = "El valor  %s  introducido se encuentra fuera de los límites de control (%s,%s)" % (
                valor, vmin, vmax)
                self.observaciones = self.textoincidencia
                warning = {
                    'title': _('A V I S O!'),
                    'message': _(texto),
                }
                result['warning'] = warning

                return result

    @api.one
    def action_solincide_tablet(self):
        """Genera Solicitud de mantenimiento y envio de email a peticion del operario que hace el check en la tablet, no es necesario tener marcadas las medidas de actuacion"""
        #Comprobar Solicitud de Mantenimiento.
        solmante = self.detreg_id.cabreg_id.tpmedactc_id.solmante
        objincidencia = self.env['appcc.gestorincidencias']
        objempleado = self.env['hr.employee']
        objmrorequest = self.env['mro.request']
        # Creamos incidencias.
        appcc_id = self.detreg_id.cabreg_id.manautctrl_id.appcc_id.id
        fincidencia = datetime.datetime.now().strftime("%Y-%m-%d")
        estado = "C"
        name = "Aviso Reg: %s  de fecha %s " % (self.name, self.start_date)
        observaciones = " %s - %s" % (self.textoincidencia or '', self.observaciones or '')
        tipogenera = "A"
        equipo_id = self.detreg_id.equipos_id.id
        zonas_id = self.detreg_id.zonas_id.id
        tpmedactc_id = self.detreg_id.cabreg_id.tpmedactc_id.id
        company_id = self.detreg_id.cabreg_id.manautctrl_id.appcc_id.company_id.id
        user_id = self.detreg_id.equipos_id.user_id.id
        empleado_id = objempleado.search([('user_id', '=', user_id), ('work_email', '!=', False)], limit=1)
        if empleado_id:
            emple_id = empleado_id.id
        else:
            empleado_id = objempleado.search([('work_email', '!=', False)], limit=1)
            if empleado_id:
                emple_id = empleado_id.id
            else:
                emple_id = ""

        regincidencia = {"appcc_id": appcc_id, 'fincidencia': fincidencia, 'estado': estado, 'name': name,
                         'observaciones': observaciones,
                         'tipogenera': tipogenera, 'equipo_id': equipo_id, 'zonas_id': zonas_id,
                         'tpmedactc_id': tpmedactc_id, 'company_id': company_id,
                         'personal_id': emple_id, 'detreg_id': self.detreg_id.id}

        id_incidencia = objincidencia.create(regincidencia)
        id_incidencia._send_mail_registros("email_solicitud_mantenimiento")
        regmrorequest = {"asset_id": self.detreg_id.equipos_id.id,
                             "cause": "Registro %s de fecha %s " % (name, self.start_date.strftime('%Y-%m-%d')),
                             'requested_date': fincidencia,
                             "description": self.textoincidencia, 'incidencia_id': id_incidencia.id}
        id_mrorequest = objmrorequest.create(regmrorequest)

        # Actualiza el registro con "done"
        self.write({'state': 'done', 'incidencia': True,
                    'observaciones': "%s  %s **Ver aviso generado en Apartado Aviso** " % (
                    self.observaciones or '', self.textoincidencia or '')})

    @api.one
    def action_button_incidencia(self):
        #print "Valor de la incidencia  en boton %s " % self.incidencia
        #Comprobar Solicitud de Mantenimiento.
        #La solicitudes de mantenimiento solo se generan si estan marcadas en las medidas de actuacion
        solmante      = self.detreg_id.cabreg_id.tpmedactc_id.solmante
        objincidencia = self.env['appcc.gestorincidencias']
        objempleado   = self.env['hr.employee']
        objmrorequest = self.env['mro.request']
        #Creamos incidencias.
        appcc_id      = self.detreg_id.cabreg_id.manautctrl_id.appcc_id.id
        fincidencia   = datetime.datetime.now().strftime("%Y-%m-%d")
        estado        = "C"
        name          = "Aviso Reg: %s  de fecha %s " % (self.name,self.start_date)
        observaciones = " %s - %s" % (self.textoincidencia or '',self.observaciones or '')
        tipogenera    =  "A"
        equipo_id     = self.detreg_id.equipos_id.id
        zonas_id      = self.detreg_id.zonas_id.id
        tpmedactc_id  = self.detreg_id.cabreg_id.tpmedactc_id.id
        company_id    = self.detreg_id.cabreg_id.manautctrl_id.appcc_id.company_id.id
        user_id       = self.detreg_id.equipos_id.user_id.id
        empleado_id   = objempleado.search([('user_id','=',user_id),('work_email','!=',False)], limit=1)
        if empleado_id:
            emple_id = empleado_id.id
        else:
            empleado_id   = objempleado.search([('work_email','!=',False)], limit=1)
            if empleado_id:
                emple_id= empleado_id.id
            else:
                emple_id=""

        regincidencia = { "appcc_id" : appcc_id, 'fincidencia': fincidencia, 'estado':estado, 'name':name, 'observaciones' :observaciones,
                           'tipogenera' : tipogenera , 'equipo_id' : equipo_id, 'zonas_id': zonas_id, 'tpmedactc_id': tpmedactc_id, 'company_id': company_id,
                           'personal_id': emple_id , 'detreg_id': self.detreg_id.id}

        id_incidencia = objincidencia.create(regincidencia)
        if id_incidencia and solmante:
            print "Entra en solicitud de mantenimiento y envia emial de incidendia"
            id_incidencia._send_mail_registros("email_solicitud_mantenimiento")
            #Genera solicitud de mantenimiento siempre y cuando este marcada la opcion en tipos de medidas de actuacion
            regmrorequest = {"asset_id": self.detreg_id.equipos_id.id, "cause": "Registro %s de fecha %s " % (name ,self.start_date.strftime('%Y-%m-%d') ) , 'requested_date': fincidencia,
                             "description" : self.textoincidencia, 'incidencia_id' : id_incidencia.id}
            id_mrorequest = objmrorequest.create(regmrorequest)
            #id_mrorequest.action_send()
        else:
            id_incidencia. _send_mail_registros("email_avisos_incidencias")

        #Actualiza el registro con "done"
        self.write({'state': 'done', 'incidencia': True, 'observaciones': "%s  %s **Ver aviso generado en Apartado Aviso** " % (self.observaciones or '',self.textoincidencia or '') })



    @api.one
    @api.constrains('detreg_id')
    def _compute_color(self):
        self.color           = self.detreg_id.actividades_id.colorback
        self.tipo            = self.detreg_id.actividades_id.tipo
        self.name            = self.detreg_id.name



    @api.onchange("start_date")
    def onchange_start_date(self):
        if self.start_date:
            fecha_task           =  datetime.datetime.combine(datetime.datetime.strptime(self.start_date,'%Y-%m-%d'),datetime.datetime.min.time())
            self.start           = fecha_task + datetime.timedelta( hours = int(self.detreg_id.ordagenda))
            self.start_datetime  = fecha_task + datetime.timedelta( hours = int(self.detreg_id.ordagenda))
            self.stop            = fecha_task + datetime.timedelta( hours = int(self.detreg_id.ordagenda)+1 )


    @api.model
    def create(self,vals):

        detreg_id  = vals.get('detreg_id')
        start_date = vals.get('start_date')
        if start_date:
            fecha_task           =  datetime.datetime.combine(datetime.datetime.strptime(start_date,'%Y-%m-%d'),datetime.datetime.min.time())
        if detreg_id:
            obj = self.env['appcc.detallesregistros'].search([('id','=',detreg_id)])
            if obj:
                if obj.ordagenda < 23 and obj.ordagenda > 0:
                    incre = 60
                else:
                    incre = 30
                vals['start']           = fecha_task + datetime.timedelta( hours = int(obj.ordagenda))
                vals['start_datetime']  = fecha_task + datetime.timedelta( hours = int(obj.ordagenda))
                vals['stop_datetime']   = fecha_task + datetime.timedelta( hours = int(obj.ordagenda), minutes=incre)
                vals['stop']            = fecha_task + datetime.timedelta( hours = int(obj.ordagenda), minutes=incre)
                vals['company_id'] = obj.company_id.id

        new_id = super(AppccRegistrosTask, self).create(vals)
        return new_id


    @api.one
    def write(self, vals):
        update = vals.get('valor',False) or  vals.get('estado',None)
        start_date = vals.get('start_date',False)
        if start_date:
            fecha_task = datetime.datetime.combine(datetime.datetime.strptime(start_date, '%Y-%m-%d'),
                                                   datetime.datetime.min.time())
            obj = self.env['appcc.detallesregistros'].search([('id', '=', self.detreg_id.id)])
            if obj:
                if obj.ordagenda <23 and obj.ordagenda>=0:
                    incre=60
                else:
                    incre=45
                vals['start']          =  fecha_task + datetime.timedelta(hours=int(obj.ordagenda))
                vals['start_datetime'] =  fecha_task + datetime.timedelta(hours=int(obj.ordagenda))
                vals['stop_datetime']  =  fecha_task + datetime.timedelta(hours=int(obj.ordagenda),minutes=incre)
                vals['stop']           =  fecha_task + datetime.timedelta(hours=int(obj.ordagenda),minutes=incre)

        updatefirmas = vals.get('firmas_id',False)
        if update:
            if not updatefirmas:
                vals['firmas_id'] = self._getdefault_employee()

            if vals.get('state',self.state) != 'draft':
                vals['state']     = 'done'
                vals['stop_date'] = fields.Date.from_string(fields.Date.today()) #Importante testear

        new_id = super(AppccRegistrosTask, self).write(vals)
        return new_id



class AppccMroRequest(models.Model):
    """
    Solicitudes de Mantenimiento para incidencias de equipos registrados por APPCC
    """
    _name = 'mro.request'
    _inherit = 'mro.request'

    incidencia_id = fields.Many2one('appcc.gestorincidencias',"Origen Solicituda")



class AppccCuadrosGestion(models.Model):
    _name        = 'appcc.cuadrosgestion'
    _description = 'Cuadros de Gestion'
    _order =('name')

    @api.one
    def _num_children(self,ids):
        res = {}
        for i in ids:
            nb_children = self.search( [('id', 'child_of', i.id)], count=True)
            res[i] = nb_children
        return res

    @api.multi
    def action_name(self):
        view = self.env.ref('appcc.action_appcc_cuadgest_kanban').id
        return {
            'type': 'ir.actions.act_windows',
            'view' : view,
            'res_id': self.id
        }

    name            = fields.Char(string="Denominacion" ,required=True)
    appcc_id        = fields.Many2one('appcc', string=_("APPCC"), required=True, deafult= lambda self: [('company_id.id','=', self.env['res.company']._company_default_get('appcc.cuadrosgestion').id)] )
    inicuad_id      = fields.Many2one('appcc.cuadrosgestion','Etapa Inicial',ondelete='cascade',domain=[('parent_id', '=', False)],readonly=True)
    parent_id       = fields.Many2one('appcc.cuadrosgestion', string=_('Etapa padre'),domain="[('id','child_of',inicuad_id)]")
    child_ids       = fields.One2many('appcc.cuadrosgestion', 'parent_id', string=_('Subordinado'))
    etapa_id        = fields.Many2one('appcc.maestros.etapas', string=_("Etapa"))
    peligro_id      = fields.Many2one('appcc.maestros.peligros', string=_("Peligro"))
    tpmedactp_ids   = fields.Many2many('appcc.maestros.tpmedactuacion', 'appcc_cuadgest_tpmedacttp_rel','preventiva_id','cuadgestion_id',   string=_("Medidas de actuación preventivas") , domain=([('tipo','=','P')]))
    ptocritico      = fields.Boolean(string=_("Punto de control"))
    ptoctrlcrit     = fields.Boolean(string=_("P.C. crítico"))
    tplimitcrit_id  = fields.Many2one('appcc.maestros.tpmlimitescriticos', string=_("Límites críticos"))
    tpmedvig_ids    = fields.Many2many('appcc.maestros.tpmedvigilancia', 'appcc_cuadgest_tpmedvig_rel','vigilancia_id','cuadgestion_id',string=_("Medidas de vigilancia"))
    momento         = fields.Char(string=_("Momento"),help=_("Cuándo se realiza la acción"))
    ente_id         = fields.Many2one('hr.employee', string=_("Personal"), required=False)
    tpmedactc_ids   = fields.Many2many('appcc.maestros.tpmedactuacion', 'appcc_cuadgest_tpmedactc_rel','correctiva_id','cuadgestion_id',string=_("Medidas correctivas"), domain=([('tipo','=','C')]))
    registros_id    = fields.Many2one('appcc.cabregistros', string=_("Registros"), help="Cabecera de registro depende toma de datos")
    tpfrecreg_id    = fields.Many2one('appcc.maestros.tpfrecuencias', string=_("Frecuencia"), required=False)
    revision_id     = fields.Many2one('appcc.historialrevisiones', string=_("Revisión"))
    company_id      = fields.Many2one('res.company',related='appcc_id.company_id', store=True, readonly=True)
    color           = fields.Integer()
    num_children    = fields.Integer(function=_num_children,method=True,string=_("Num. Sub Estapas"), strore=False)
    probabilidad    = fields.Selection([('1','Baja'),('2','Media'),('3','Alta')], string="Probabilidad" )
    severidad       = fields.Selection([('1','Baja'),('2','Media'),('3','Alta')], string="Severidad")
    tipopeligro     = fields.Char(compute="_calcula_peligro", string="Tipo de Peligro", strore=True)


    @api.one
    @api.depends('severidad', 'probabilidad')
    def _calcula_peligro(self):
        if self.probabilidad and self.severidad:
            resultado= int(self.probabilidad)+int(self.severidad)
            if resultado >=4:
                self.tipopeligro= "Significativo"
            else:
                self.tipopeligro= "No Significativo"

    @api.constrains('ptocritico','ptoctrlcrit')
    def _valida_puntos(self):
        if self.ptocritico and self.ptoctrlcrit:
            raise ValidationError("Un punto de control no puede ser Critico y de Control ")

    @api.constrains('appcc_id')
    def _get_companyc(self):
        self.company_id = self.appcc_id.company_id.id

        #Hacer validacion, solo mostrar appcc en etapa inicial despues heredar APPCC de etapa padre, no se puede
        #actualizar etapa inicial si tiene etapar hijas



ESTADOS=[('C',_('Comunicada')),('P',_('Pendiente')),('S',_('Solucionada'))]



class AppccGestorIncidencias(models.Model):
    _name        = 'appcc.gestorincidencias'
    _description = 'Gestor de Incidencias'

    appcc_id          = fields.Many2one('appcc', default= lambda self: [('company_id.id','=', self.env['res.company']._company_default_get('appcc.gestorincidencias').id)], string=_("APPCC"))
    fincidencia       = fields.Date(string=_("F. Aviso"))
    festado           = fields.Date(string=_("F. Resolución"),null=True,blank=True)
    estado            = fields.Selection(ESTADOS)
    name              = fields.Char(string=_("Aviso"))
    observaciones     = fields.Text(string=_("Descripción del aviso"),help=_("Descripción amplia del aviso."))
    personal_id       = fields.Many2one('hr.employee', string=_("Personal"), help=_("Persona asignada para el seguimiento del aviso"),required=False,domain = lambda self: [('department_id.company_id.id','=', self.env['res.company']._company_default_get('appcc.gestorincidencias').id)])
    etapa_id          = fields.Many2one('appcc.maestros.etapas', string=_("Etapa"), help=_("Etapa del cuadro de gestión"))
    equipo_id         = fields.Many2one('asset.asset', string=_("Equipos"))
    zonas_id          = fields.Many2one('stock.location', string=_("Zona") )
    tpmedactc_id      = fields.Many2one('appcc.maestros.tpmedactuacion',  string=_("Medidas correctivas"), required=True, domain=([('tipo','=','C')]))
    tipogenera        = fields.Selection([('A','AUTOMATICO'),('P','MANUAL')],string=_("Tipo de generación"),help=_("Elegir si el aviso se genera automáticamente o manualmente."))
    company_id        = fields.Many2one('res.company', string="Empresa", related='appcc_id.company_id', store=True, readonly=True)
    detreg_id         = fields.Many2one('appcc.detallesregistros', required=True,string="Registro",help="Registro de control sobre el que se genera el aviso")
    manautctrl_id     = fields.Many2one('appcc.manualautocontrol', string="Plan Autocontrol")


    @api.constrains('appcc_id')
    def _get_companyc(self):
        self.company_id = self.appcc_id.company_id.id

    @api.multi
    def action_button_solmante(self):
        objmrorequest = self.env['mro.request']
        # Genera solicitud de mantenimiento siempre y cuando este marcada la opcion en tipos de medidas de actuacion
        # Validar que solo se haya generado una vez la solicitud de mantenimiento
        regmrorequest = {"asset_id": self.equipo_id.id, "cause": "Desde APPCC %s  " % self.name,
                         'requested_date': self.fincidencia,
                         "description": self.observaciones, 'incidencia_id': self.id}


        id_mrorequest = objmrorequest.create(regmrorequest)
        self._send_mail_registros("email_solicitud_mantenimiento")
        # id_mrorequest.action_send()



    @api.multi
    def _send_mail_registros(self,template_xmlid):
        res = False
        data_pool = self.env['ir.model.data']
        mail_pool = self.env['mail.mail']
        template_pool = self.env['mail.template']
        # Ubicamos solo destinatario de AVISOS EMAIL
        userids = self.env['res.partner.category'].search([('name', '=', 'AVISOS EMAIL')])
        print userids
        email_dir = ', '.join(map(lambda x: x, (str(partner.email) for partner in
                                                self.env['res.partner'].search([('category_id', 'in', userids.ids)]))))

        dummy, template_id = data_pool.get_object_reference('appcc', template_xmlid)
        email = template_pool.browse(template_id)
        email.email_to = email_dir
        mail_id = email.send_mail(self.id, force_send=True)
        if mail_id:
            res = mail_pool.send([mail_id])

        return res



class AppccCabAnaliticas(models.Model):
    _name       = 'appcc.cabanaliticas'
    _description = 'Cabecera Analiticas'

    cabreg_id          = fields.Many2one('appcc.cabregistros')
    detreg_id          = fields.Many2one('appcc.detallesregistros',string=_("Registro Analisis"), domain=([('cabreg_id.tpmedvig_id.analitica','=',True)]),required=True)
    name               = fields.Char( string=_('Denominación') )
    fecha              = fields.Date( string=_('Fecha'),help=_("Fecha analítica"), required=True)
    laboratorio_id     = fields.Many2one('res.partner', string=_("Laboratorio"),domain = ([('category_id.name','=','LABORATORIO')]), required=True )
    observaciones      = fields.Text(string=_("Observaciones") )
    company_id         = fields.Many2one('res.company', string="Empresa",related='detreg_id.company_id', store=True, readonly=True)
    cabana_ids         = fields.One2many('appcc.detanaliticas', 'cabanalitica_id')



class AppccDetAnaliticas(models.Model):
    _name        = 'appcc.detanaliticas'
    _description = 'Detalle Analiticas'

    cabanalitica_id  = fields.Many2one('appcc.cabanaliticas')
    fecha            = fields.Datetime(string=_('F .Muestra'),help=_("Fecha de toma de la muestra"))
    parametros       = fields.Many2one('appcc.maestros.paraanalisis', string=_("Parámetro análisis"))
    valores          = fields.Float(digits=(10,4), string=_('Valores'), group_operator="avg")
    company_id        = fields.Many2one('res.company', string='Company',related='cabanalitica_id.company_id', store=True, readonly=True)



class AppccCabInformesTecnicos(models.Model):
    _name        = 'appcc.cabinfotecnicos'
    _description = 'Cabecera de Informes Tecnicos'

    appcc_id          = fields.Many2one('appcc',default= lambda self: [('company_id.id','=', self.env['res.company']._company_default_get('appcc.cabinfotecnicos').id)], string=_("APPCC"))
    establecimiento   = fields.Char(string=_('Establecimiento'))
    expediente        = fields.Char(string=_('Expediente'))
    responsables_ids  = fields.Many2many('hr.employee','appcc_cab_info_coordinador_rel_1','employee_id','appcc_id',string=_("Coordinadores/Responsables"),domain = lambda self: [('department_id.company_id.id','=', self.env['res.company']._company_default_get('appcc.cabinfotecnicos').id)]) #Campos a relacionar
    auditor_ids       = fields.Many2many('res.partner','appcc_cab_info_veterinarios_rel_1','employee_id','appcc_id',string=_("Auditores"), domain=([('company_type','=','person'),('category_id.name','=','VETERINARIO')]))
    fecha             = fields.Date(string=_("Fecha Realizado"))
    legislacion_ids   = fields.Many2many('appcc.maestros.tplegislacion','appcc_cabinfo_legisla_rel','legisla_id','cabinfo_id', string=_("Legislación"))
    company_id        = fields.Many2one('res.company', string="Empresa", related='appcc_id.company_id', store=True, readonly=True)
    cabinfortec_ids    = fields.One2many('appcc.detinfotecnicos', 'cabinfortec_id')



#CAB INFO TEC IDS



class AppccDetInformesTecnicos(models.Model):
    _name        = 'appcc.detinfotecnicos'
    _description = 'Detalles de Informes Tecnicos'


    def attachment_tree_view(self, cr, uid, ids, context):
        domain = ['&', ('res_model', '=', 'appcc.detinfotecnicos'), ('res_id', 'in', ids)]
        res_id = ids and ids[0] or False
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
        }

    @api.one
    def _get_attached_docs(self):
        res = {}
        attachment = self.env['ir.attachment']
        appcc_attachments = attachment.search_count( [('res_model', '=', 'appcc.detinfotecnicos'), ('res_id', '=', self.id)] )
        res  = appcc_attachments or 0
        self.doc_count = res


    cabinfortec_id = fields.Many2one('appcc.cabinfotecnicos')
    titulo         = fields.Char(string=_('Título'))
    texto          = fields.Text(string=_('Texto'))
    orden          = fields.Integer()
    doc_count      = fields.Integer(compute='_get_attached_docs', string="Adjuntar documentos", type='integer')
    company_id     = fields.Many2one('res.company', string='Company',related='cabinfortec_id.company_id', store=True, readonly=True)



class AppccMExcepCalendar(models.Model):
    _name        = 'appcc.excepcalendar'
    _description = "Alta de dias festivos y excepciones de calendario"


    name       = fields.Char(string=_("Tipo de excepción"),  required=True)
    observa    = fields.Text()
    company_id = fields.Many2one('res.company', string=_("Local"),default=lambda self: self.env['res.company']._company_default_get('appcc.excepcalendar'))
    fechaini   = fields.Date(string=_("Fecha inicio"),required=True)
    fechafin   = fields.Date(string=_("Fecha fin"), required=True)
    activo     = fields.Boolean(string=_("Activar"), default=True)


    @api.one
    @api.constrains('fechaini', 'fechafin')
    def _check_fecha(self):
        if self.fechafin < self.fechaini:
            raise ValidationError('Las fechas no corresponden a inicio y fin')

