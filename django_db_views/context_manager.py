from contextlib import ContextDecorator

VIEW_MIGRATION_CONTEXT = {"is_view_migration": False}


class view_migration_context(ContextDecorator):
    def __enter__(self):
        global VIEW_MIGRATION_CONTEXT
        VIEW_MIGRATION_CONTEXT["is_view_migration"] = True
        return self

    def __exit__(self, *exc):
        global VIEW_MIGRATION_CONTEXT
        VIEW_MIGRATION_CONTEXT["is_view_migration"] = False
