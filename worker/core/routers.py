APPS = ['submitgit']


class SubmitgitRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label in APPS:
            return "submitgit"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label in APPS or \
           obj2._meta.app_label in APPS:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "submitgit":
            return app_label in APPS
        elif app_label in APPS:
            return False
        return None
