"""
Benchmark the 30-query suite on DuckDB + DuckPGQ with pytest-benchmark.

Run from the `duckpgq/` directory:

    uv run --frozen pytest benchmark_query.py \
      --benchmark-min-rounds=5 \
      --benchmark-min-time=0.000005 \
      --benchmark-max-time=1.0 \
      --benchmark-timer=time.perf_counter \
      --benchmark-calibration-precision=10 \
      --benchmark-warmup=off \
      --benchmark-warmup-iterations=5 \
      --benchmark-disable-gc \
      --benchmark-sort=fullname

Query result conversion (to a Polars DataFrame) happens inside the timed
function, matching the other engines in this repository. The expected values
are the same as in ladybugdb/benchmark_query.py; only the column aliases differ.
"""

from __future__ import annotations

from typing import Any, Iterable

import pytest

import query
from common import DB_PATH, connect, duckdb_version, duckpgq_version


@pytest.fixture(scope="session")
def connection():
    if not DB_PATH.is_file():
        raise RuntimeError(f"Missing {DB_PATH}. Run build_graph.py first.")
    with connect(DB_PATH) as conn:
        print(f"\nDuckDB {duckdb_version(conn)}, DuckPGQ {duckpgq_version(conn)}, database {DB_PATH}")
        yield conn


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


def test_benchmark_query1(benchmark, connection):
    result = benchmark(query.run_query1, connection)
    _assert_rows(
        result,
        [{"firstName": "Thomas", "lastName": "Brown"}],
        order_sensitive=True,
    )


def test_benchmark_query2(benchmark, connection):
    result = benchmark(query.run_query2, connection)
    _assert_rows(
        result,
        [
            {"postId": 2061586474857},
            {"postId": 2061586474860},
        ],
    )


def test_benchmark_query3(benchmark, connection):
    result = benchmark(query.run_query3, connection)
    _assert_rows(
        result,
        [
            {
                "firstName": "Mads",
                "lastName": "Haugland",
                "orgName": "Norwegian_School_of_Sport_Sciences",
            }
        ],
        order_sensitive=True,
    )


def test_benchmark_query4(benchmark, connection):
    result = benchmark(query.run_query4, connection)
    _assert_rows(result, [{"commentId": 1924145496676}], order_sensitive=True)


def test_benchmark_query5(benchmark, connection):
    result = benchmark(query.run_query5, connection)
    _assert_rows(
        result,
        [{"firstName": "Akihiko", "lastName": "Choi"}],
        order_sensitive=True,
    )


def test_benchmark_query6(benchmark, connection):
    result = benchmark(query.run_query6, connection)
    _assert_rows(
        result,
        [
            {"personId": 28587302332692},
            {"personId": 17592186046501},
            {"personId": 19791209310595},
            {"personId": 15393162799645},
            {"personId": 15393162791641},
        ],
    )


def test_benchmark_query7(benchmark, connection):
    result = benchmark(query.run_query7, connection)
    _assert_rows(result, [])


def test_benchmark_query8(benchmark, connection):
    result = benchmark(query.run_query8, connection)
    _assert_rows(result, [{"personId": 13194139534410}], order_sensitive=True)


def test_benchmark_query9(benchmark, connection):
    result = benchmark(query.run_query9, connection)
    _assert_rows(
        result,
        [{"personId": 1242, "firstName": "Hans", "lastName": "Johansson"}],
        order_sensitive=True,
    )


def test_benchmark_query10(benchmark, connection):
    result = benchmark(query.run_query10, connection)
    _assert_rows(
        result,
        [
            {"personId": 6597069775789},
            {"personId": 8796093029267},
            {"personId": 24189255819727},
        ],
    )


def test_benchmark_query11(benchmark, connection):
    result = benchmark(query.run_query11, connection)
    _assert_rows(result, [{"num_e": 190, "orgName": "MDLR_Airlines"}])


def test_benchmark_query12(benchmark, connection):
    result = benchmark(query.run_query12, connection)
    _assert_single_value(result, "num_comments", 3229)


def test_benchmark_query13(benchmark, connection):
    result = benchmark(query.run_query13, connection)
    _assert_single_value(result, "num_persons", 2293)


def test_benchmark_query14(benchmark, connection):
    result = benchmark(query.run_query14, connection)
    _assert_single_value(result, "num_forums", 37)


def test_benchmark_query15(benchmark, connection):
    result = benchmark(query.run_query15, connection)
    _assert_single_value(result, "num_forums", 278)


def test_benchmark_query16(benchmark, connection):
    result = benchmark(query.run_query16, connection)
    _assert_single_value(result, "num_posts", 3)


def test_benchmark_query17(benchmark, connection):
    result = benchmark(query.run_query17, connection)
    _assert_rows(result, [{"tagName": "Hamid_Karzai", "tag_count": 32}])


def test_benchmark_query18(benchmark, connection):
    result = benchmark(query.run_query18, connection)
    _assert_single_value(result, "num_p", 20)


def test_benchmark_query19(benchmark, connection):
    result = benchmark(query.run_query19, connection)
    _assert_rows(result, [{"placeName": "India", "comment_count": 242}])


def test_benchmark_query20(benchmark, connection):
    result = benchmark(query.run_query20, connection)
    _assert_single_value(result, "long_comment_count", 3)


def test_benchmark_query21(benchmark, connection):
    result = benchmark(query.run_query21, connection)
    _assert_single_value(result, "liked", True)


def test_benchmark_query22(benchmark, connection):
    result = benchmark(query.run_query22, connection)
    _assert_single_value(result, "has_reply_comment", True)


def test_benchmark_query23(benchmark, connection):
    result = benchmark(query.run_query23, connection)
    _assert_single_value(result, "has_moderator", True)


def test_benchmark_query24(benchmark, connection):
    result = benchmark(query.run_query24, connection)
    _assert_single_value(result, "has_person", False)


def test_benchmark_query25(benchmark, connection):
    result = benchmark(query.run_query25, connection)
    _assert_single_value(result, "knows_someone", False)


def test_benchmark_query26(benchmark, connection):
    result = benchmark(query.run_query26, connection)
    _assert_single_value(result, "has_forum", False)


def test_benchmark_query27(benchmark, connection):
    result = benchmark(query.run_query27, connection)
    _assert_single_value(result, "has_comment", True)


def test_benchmark_query28(benchmark, connection):
    result = benchmark(query.run_query28, connection)
    _assert_single_value(result, "has_people", True)


def test_benchmark_query29(benchmark, connection):
    result = benchmark(query.run_query29, connection)
    _assert_single_value(result, "has_written_post_with_safari", False)


def test_benchmark_query30(benchmark, connection):
    result = benchmark(query.run_query30, connection)
    _assert_single_value(result, "has_self_reply", True)
