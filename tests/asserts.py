from django.db import connections


def is_table_exists(table_name: str, using: str = 'default') -> bool:
    with connections[using].cursor() as cursor:
        return table_name in connections[using].introspection.table_names(cursor)


def is_view_exists(view_name: str, using: str = 'default') -> bool:
    with connections[using].cursor() as cursor:
        views = [
            table.name for table in connections[using].introspection.get_table_list(cursor) if table.type == 'v'
        ]
        return view_name in views
