from django_db_views.autodetector import ViewMigrationAutoDetector


def test_is_same_views():
    is_same = ViewMigrationAutoDetector.is_same_views

    assert is_same("A B C", "A B   C")
    assert is_same("select * from xyz", "SELECT *   FROM xyz")
    assert not is_same("select 1 from test", "select 2 from test")
    assert is_same("select *\nfrom test\n", "select * from test")
    assert is_same(
        "SELECT\n\t   * \n FROM something where a = ' ' and B = \"  \"",
        "select * from something where a = ' ' and b = \"  \"",
    )
    assert not is_same('SELECT " "', 'SELECT ""')
    assert not is_same('SELECT "TEST "', 'SELECT "TEST    "')

    assert is_same(
        """
        -- some comment
        select count(*) from
                    table\t
        where is_countable    group by kind
        """,
        "SELECT COUNT(*) FROM table WHERE is_countable GROUP BY kind",
    )
