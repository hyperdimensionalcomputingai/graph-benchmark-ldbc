from __future__ import annotations

from typing import Any, Iterable

import pytest
from falkordb import FalkorDB, Graph

import query


@pytest.fixture(scope="session")
def graph() -> Graph:
    db = FalkorDB(host=query.FALKORDB_HOST, port=query.FALKORDB_PORT)
    yield db.select_graph(query.FALKORDB_GRAPH)
    db.close()


def _rows(result: Any) -> list[dict[str, Any]]:
    if hasattr(result, "to_dicts"):
        return result.to_dicts()
    return result


def _row_sort_key(row: dict[str, Any]) -> tuple:
    return tuple(sorted(row.items()))


def _assert_rows(
    result: Any,
    expected_rows: Iterable[dict[str, Any]],
    *,
    order_sensitive: bool = False,
) -> None:
    rows = _rows(result)
    expected = list(expected_rows)
    if order_sensitive:
        assert rows == expected
        return
    assert sorted(rows, key=_row_sort_key) == sorted(expected, key=_row_sort_key)


def _assert_single_value(result: Any, key: str, expected_value: Any) -> None:
    rows = _rows(result)
    assert rows == [{key: expected_value}]


def test_benchmark_query1(benchmark, graph):
    result = benchmark(query.run_query1, graph)
    _assert_rows(
        result,
        [{"p.firstName": "Thomas", "p.lastName": "Brown"}],
        order_sensitive=True,
    )


def test_benchmark_query2(benchmark, graph):
    result = benchmark(query.run_query2, graph)
    _assert_rows(
        result,
        [
            {"post.ID": 2061586474857},
            {"post.ID": 2061586474860},
        ],
    )


def test_benchmark_query3(benchmark, graph):
    result = benchmark(query.run_query3, graph)
    _assert_rows(
        result,
        [
            {
                "person.firstName": "Mads",
                "person.lastName": "Haugland",
                "org.name": "Norwegian_School_of_Sport_Sciences",
            }
        ],
        order_sensitive=True,
    )


def test_benchmark_query4(benchmark, graph):
    result = benchmark(query.run_query4, graph)
    _assert_rows(result, [{"c.ID": 1924145496676}], order_sensitive=True)


def test_benchmark_query5(benchmark, graph):
    result = benchmark(query.run_query5, graph)
    _assert_rows(
        result,
        [{"p.firstName": "Akihiko", "p.lastName": "Choi"}],
        order_sensitive=True,
    )


def test_benchmark_query6(benchmark, graph):
    result = benchmark(query.run_query6, graph)
    _assert_rows(
        result,
        [
            {"p.ID": 28587302332692},
            {"p.ID": 17592186046501},
            {"p.ID": 19791209310595},
            {"p.ID": 15393162799645},
            {"p.ID": 15393162791641},
        ],
    )


def test_benchmark_query7(benchmark, graph):
    result = benchmark(query.run_query7, graph)
    _assert_rows(result, [])


def test_benchmark_query8(benchmark, graph):
    result = benchmark(query.run_query8, graph)
    _assert_rows(result, [{"p.ID": 13194139534410}], order_sensitive=True)


def test_benchmark_query9(benchmark, graph):
    result = benchmark(query.run_query9, graph)
    _assert_rows(
        result,
        [{"p.ID": 1242, "p.firstName": "Hans", "p.lastName": "Johansson"}],
        order_sensitive=True,
    )


def test_benchmark_query10(benchmark, graph):
    result = benchmark(query.run_query10, graph)
    _assert_rows(
        result,
        [
            {"p.ID": 6597069775789},
            {"p.ID": 8796093029267},
            {"p.ID": 24189255819727},
        ],
    )


def test_benchmark_query11(benchmark, graph):
    result = benchmark(query.run_query11, graph)
    _assert_rows(result, [{"num_e": 190, "o.name": "MDLR_Airlines"}])


def test_benchmark_query12(benchmark, graph):
    result = benchmark(query.run_query12, graph)
    _assert_single_value(result, "num_comments", 3229)


def test_benchmark_query13(benchmark, graph):
    result = benchmark(query.run_query13, graph)
    _assert_single_value(result, "num_persons", 2293)


def test_benchmark_query14(benchmark, graph):
    result = benchmark(query.run_query14, graph)
    _assert_single_value(result, "num_forums", 37)


def test_benchmark_query15(benchmark, graph):
    result = benchmark(query.run_query15, graph)
    _assert_single_value(result, "num_forums", 278)


def test_benchmark_query16(benchmark, graph):
    result = benchmark(query.run_query16, graph)
    _assert_single_value(result, "num_posts", 3)


def test_benchmark_query17(benchmark, graph):
    result = benchmark(query.run_query17, graph)
    _assert_rows(result, [{"t.name": "Hamid_Karzai", "tag_count": 32}])


def test_benchmark_query18(benchmark, graph):
    result = benchmark(query.run_query18, graph)
    _assert_single_value(result, "num_p", 20)


def test_benchmark_query19(benchmark, graph):
    result = benchmark(query.run_query19, graph)
    _assert_rows(result, [{"l.name": "India", "comment_count": 242}])


def test_benchmark_query20(benchmark, graph):
    result = benchmark(query.run_query20, graph)
    _assert_single_value(result, "long_comment_count", 3)


def test_benchmark_query21(benchmark, graph):
    result = benchmark(query.run_query21, graph)
    _assert_single_value(result, "liked", True)


def test_benchmark_query22(benchmark, graph):
    result = benchmark(query.run_query22, graph)
    _assert_single_value(result, "has_reply_comment", True)


def test_benchmark_query23(benchmark, graph):
    result = benchmark(query.run_query23, graph)
    _assert_single_value(result, "has_moderator", True)


def test_benchmark_query24(benchmark, graph):
    result = benchmark(query.run_query24, graph)
    _assert_single_value(result, "has_person", False)


def test_benchmark_query25(benchmark, graph):
    result = benchmark(query.run_query25, graph)
    _assert_single_value(result, "knows_someone", False)


def test_benchmark_query26(benchmark, graph):
    result = benchmark(query.run_query26, graph)
    _assert_single_value(result, "has_forum", False)


def test_benchmark_query27(benchmark, graph):
    result = benchmark(query.run_query27, graph)
    _assert_single_value(result, "has_comment", True)


def test_benchmark_query28(benchmark, graph):
    result = benchmark(query.run_query28, graph)
    _assert_single_value(result, "has_people", True)


def test_benchmark_query29(benchmark, graph):
    result = benchmark(query.run_query29, graph)
    _assert_single_value(result, "has_written_post_with_safari", False)


def test_benchmark_query30(benchmark, graph):
    result = benchmark(query.run_query30, graph)
    _assert_single_value(result, "has_self_reply", True)
