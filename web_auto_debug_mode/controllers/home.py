from footil.xtyping import bytes_to_str

from odoo.http import request

from odoo.addons.web.controllers.main import Home as HomeOrig

from ..models.res_users import DEBUG_PREFIX

PARAM_SEP = '#'


class Home(HomeOrig):
    """Extended to modify redirect on login."""

    def get_no_debug_redirects(self):
        """Return list of exclusions that can't use debug mode.

        It can be full redirect or its fragment.
        """
        return ['/web/become', '/web/login', DEBUG_PREFIX]

    def _check_redirect(self, redirect):
        for excluded in self.get_no_debug_redirects():
            if excluded in redirect:
                return False
        return True

    def combine_redirect_with_debug(self, redirect, debug_mode):
        """Form new redirect with original plus debug_mode."""
        # Debug mode already has question mark.
        redirect = redirect.replace('?', '')
        idx = redirect.find(PARAM_SEP)
        if idx == -1:
            return redirect + debug_mode
        # Put debug mode between redirect and its parameters.
        return f'{redirect[:idx]}{debug_mode}{redirect[idx:]}'

    def _login_redirect(self, uid, redirect=None):
        """Extend to enable debug mode if user uses it."""
        redirect = super()._login_redirect(uid, redirect=redirect)
        redirect = bytes_to_str(redirect)
        if self._check_redirect(redirect):
            debug_mode = (
                request.env['res.users'].sudo().browse(uid).get_debug_parameter()
            )
            redirect = self.combine_redirect_with_debug(redirect, debug_mode)
        return redirect
