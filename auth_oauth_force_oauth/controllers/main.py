# Copyright 2024 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import _, http
from odoo.http import request

from odoo.addons.auth_signup.controllers import main
from odoo.addons.web.controllers import home


class Home(home.Home):
    @http.route("/web/login", type="http", auth="none")
    def web_login(self, redirect=None, **kw):
        # Only proceed if it's a POST request and 'login' is provided
        if request.httprequest.method != "POST" or "login" not in kw:
            return super().web_login(redirect=redirect, **kw)
        login = kw["login"]
        user = request.env["res.users"].sudo().search([("login", "=", login)], limit=1)
        # Only proceed if 'force_oauth_domains' is set for the company
        if user._is_allowed_password_login():
            return super().web_login(redirect=redirect, **kw)
        # User is not allowed to login with a password, prompt for OAuth login
        providers = self.list_providers()
        values = request.params
        values["error"] = _(
            "You are not allowed to login with password. Please use OAuth login."
        )
        values["providers"] = providers
        return request.render("web.login", values)


class CustomAuthSignup(main.AuthSignupHome):
    @http.route(
        "/web/reset_password", type="http", auth="public", website=True, sitemap=False
    )
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        login = qcontext.get("login", request.params.get("login"))
        password = qcontext.get("password")
        confirm_password = qcontext.get("confirm_password")
        if not login or not password or not confirm_password:
            return super().web_auth_reset_password(*args, **kw)
        user = request.env["res.users"].sudo().search([("login", "=", login)], limit=1)
        if user._is_allowed_password_login():
            return super().web_auth_reset_password(*args, **kw)
        qcontext["error"] = _(
            "You are not allowed to login with password. Please use OAuth login."
        )
        return request.render("auth_signup.reset_password", qcontext)
