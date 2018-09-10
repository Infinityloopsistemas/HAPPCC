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

from datetime import datetime, timedelta
import random
from urlparse import urljoin
import werkzeug

from openerp.addons.base.ir.ir_mail_server import MailDeliveryException
from openerp.osv import osv, fields
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, ustr
from ast import literal_eval
from openerp.tools.translate import _
from openerp.exceptions import UserError


def now(**kwargs):
    dt = datetime.now() + timedelta(**kwargs)
    return dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

class res_users(osv.Model):
    _inherit = 'res.users'


    def action_reset_password(self, cr, uid, ids, context=None):
        """ create signup token for each user, and send their signup url by email """
        # prepare reset password signup
        if not context:
            context = {}
        create_mode = bool(context.get('create_user'))
        res_partner = self.pool.get('res.partner')
        partner_ids = [user.partner_id.id for user in self.browse(cr, uid, ids, context)]

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        res_partner.signup_prepare(cr, uid, partner_ids, signup_type="reset", expiration=expiration, context=context)

        context = dict(context or {})

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                # get_object() raises ValueError if record does not exist
                template = self.pool.get('ir.model.data').get_object(cr, uid, 'appcc', 'set_password_email_siva')
            except ValueError:
                pass
        if not bool(template):
            template = self.pool.get('ir.model.data').get_object(cr, uid, 'appcc', 'reset_password_email_siva')
        assert template._name == 'mail.template'

        for user in self.browse(cr, uid, ids, context):
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.") % user.name)
            context['lang'] = user.lang
            self.pool.get('mail.template').send_mail(cr, uid, template.id, user.id, force_send=True,
                                                     raise_exception=True, context=context)
