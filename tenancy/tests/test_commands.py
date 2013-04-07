from __future__ import unicode_literals
from StringIO import StringIO

import django
from django.db import connections
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test.testcases import TransactionTestCase

from ..models import Tenant, TenantModelBase

from .utils import skipIfCustomTenant

# TODO: Remove when support for django 1.4 is dropped
class raise_cmd_error_stderr(object):
    def write(self, msg):
        raise CommandError(msg)


@skipIfCustomTenant
class CreateTenantCommandTest(TransactionTestCase):
    stderr = raise_cmd_error_stderr()

    def create_tenant(self, *args, **kwargs):
        if django.VERSION[:2] == (1, 4):
            kwargs['stderr'] = self.stderr
        call_command('create_tenant', *args, **kwargs)

    def test_too_many_fields(self):
        args = ('name', 'useless')
        expected_message = (
            "Number of args exceeds the number of fields for model tenancy.Tenant.\n"
            "Got %s when defined fields are ('name',)." % repr(args)
        )
        with self.assertRaisesMessage(CommandError, expected_message):
            self.create_tenant(*args)

    def test_full_clean_failure(self):
        expected_message = (
            'Invalid value for field "name": This field cannot be blank.'
        )
        with self.assertRaisesMessage(CommandError, expected_message):
            self.create_tenant()

    def test_success(self):
        self.create_tenant('tenant', verbosity=0)
        Tenant.objects.get(name='tenant').delete()

    def test_verbosity(self):
        stdout = StringIO()
        self.create_tenant('tenant', stdout=stdout, verbosity=3)
        tenant = Tenant.objects.get(name='tenant')
        stdout.seek(0)
        connection = connections[tenant._state.db]
        if connection.vendor == 'postgresql':  #pragma: no cover
            self.assertIn(tenant.db_schema, stdout.readline())
        for model, line in zip(TenantModelBase.references, stdout.readlines()):
            self.assertIn(model._meta.db_table, line)
        tenant.delete()
