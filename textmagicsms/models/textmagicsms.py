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


from openerp.osv import osv
from openerp import api, fields, models, fields
from openerp import _, tools
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
from textmagic.rest import TextmagicRestClient



class TextMagicConfig(models.Model):
    _name="textmagicsms.configuration"
    _description ="Text Magic Configuration"

    name   = fields.Char("Nombre Usuario", required=True)
    token  = fields.Char("Token", required=True)
    numsms = fields.Integer("Numero maximo de SMS a enviar", default=3)


class TextMagicMessages(models.Model):
    _name="textmagicsms.messages"
    _description="Text Magic SMS messages"

    name      = fields.Char("Telephone Number")
    datetime  = fields.Datetime("Date SMS send")
    text      = fields.Char("Text messages")
    model     = fields.Char("Model origin send")
    sendstate = fields.Char("State Send")


    def create(self,vals):
        telephone = vals.get('name')
        smstext   = vals.get('text')
        objconfig = self.env["textmagicsms.configuration"].browse([1])
        print  objconfig
        if objconfig:
            username  = objconfig.name
            token     = objconfig.token
            nummax    = objconfig.numsms
            hoy       = fields.Date.today()
            finicio   = hoy+" 00:00:00"
            ffin      = hoy+" 23:59:59"
            numero    = self.env['textmagicsms.messages'].search_count([('datetime','<=',ffin),('datetime','>=',finicio)])
            print "Numero de envios %s" % numero
            if numero<= nummax:
                if token and username:
                    print "Username and token and phone %s , %s , %s" % (username,token,telephone)
                    client = TextmagicRestClient(username, token)
                    vals['sendstate'] = client.messages.create(phones=telephone, text=smstext)
                    vals['datetime']  = fields.Datetime.now()
                    print vals
                    new_id = super(TextMagicMessages, self).create(vals)
                    return new_id


