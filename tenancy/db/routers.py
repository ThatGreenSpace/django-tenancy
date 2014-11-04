from ..models import TenantModel


class TenancyRouter(object):
    """
    A router to control migrations on Tenancy models
    """

    def allow_migrate(self, db, model):
        if issubclass(model, TenantModel) and model == model._for_tenant_model:
            return False
        return True
