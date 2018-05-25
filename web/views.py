# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views.generic import TemplateView
from .utils import create_user_company

class HomeView(TemplateView):
    """HomeView the first page in the app

    This will make sure that company will be created if the user is not a part
    of any company before
    """
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        sup = super(HomeView, self).get_context_data(**kwargs)
        return sup

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated():
            companies = user.company_set.count()
            if companies == 0:
                create_user_company(user)
        return super(HomeView, self).dispatch(request, *args, **kwargs)
