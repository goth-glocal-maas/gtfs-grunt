# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import AbstractUser
from django.db.models import Model, CharField, SlugField, ManyToManyField


@python_2_unicode_compatible
class User(AbstractUser):
    """User

    I don't know why I make it people.User though, but I do it anyway,
    easier access maybe?
    """
    def __str__(self):
        return self.username

    @property
    def company(self):
        try:
            return self.company_set.all()[0]
        except:
            return None


@python_2_unicode_compatible
class Company(Model):
    """Company to hold all models together
    """
    name = CharField('Company Name', max_length=200)
    slug = SlugField('Company Slug', unique=True, max_length=100)
    url = CharField('Company URL', max_length=250)
    users = ManyToManyField('User')

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name
