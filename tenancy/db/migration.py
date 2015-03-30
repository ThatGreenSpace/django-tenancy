from __future__ import unicode_literals
from django.db.migrations import Migration
from .. import get_tenant_model


class TenantMigration(Migration):
    def pre_tenant_step_sql(self, tenant, default_schema_name):
        return ["SET search_path TO '%s', %s" % (
            tenant.db_schema, default_schema_name
        )]

    def post_tenant_step_sql(self, tenant, default_schema_name):
        return ["SET search_path TO %s" % default_schema_name]

    def get_queryset(self):
        return get_tenant_model()._default_manager.all()

    def tenant_step(self, operation, project_state, schema_editor, collect_sql):
        default_schema_name = 'public'
        deferred_sql = schema_editor.deferred_sql
        for tenant in self.get_queryset():
            pre_sql = self.pre_tenant_step_sql(tenant, default_schema_name)
            for statement in pre_sql:
                schema_editor.execute(statement)
            pre_deferred_len = len(deferred_sql)

            operation(project_state, schema_editor, collect_sql)

            post_deferred_len = len(deferred_sql)
            post_sql = self.post_tenant_step_sql(tenant, default_schema_name)
            for statement in post_sql:
                schema_editor.execute(statement)
            # If some deferred statements were added we wrap them with the
            # required pre/post sql statements.
            if post_deferred_len > pre_deferred_len:
                deferred_sql[pre_deferred_len:pre_deferred_len] = pre_sql
                deferred_sql.extend(post_sql)

    def apply(self, project_state, schema_editor, collect_sql=False):
        self.tenant_step(super(TenantMigration, self).apply, project_state, schema_editor, collect_sql)

    def unapply(self, project_state, schema_editor, collect_sql=False):
        self.tenant_step(super(TenantMigration, self).unapply, project_state, schema_editor, collect_sql)
