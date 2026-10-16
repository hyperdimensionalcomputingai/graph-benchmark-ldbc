"""
Run the 30-query LDBC SNB SF1 suite against DuckDB via DuckPGQ (SQL/PGQ).

The queries are translations of the Cypher queries used for the other engines
(see ladybugdb/query.py). The pattern inside `GRAPH_TABLE` returns a table via
the `COLUMNS (...)` clause; DISTINCT, aggregation, ORDER BY and LIMIT are
expressed in the surrounding SQL. DuckPGQ requires every node and edge pattern
to bind a variable and a label, so there are no anonymous patterns.

Usage:
    uv run query.py            # run all 30 queries
    uv run query.py "1,2,6"    # run a subset
"""

from __future__ import annotations

import sys
import time
from typing import Callable

import duckdb
import polars as pl

from common import DB_PATH, PROPERTY_GRAPH_NAME as G, connect, duckdb_version, duckpgq_version


def _execute(conn: duckdb.DuckDBPyConnection, idx: int, query: str) -> pl.DataFrame:
    print(f"\nQuery {idx}:\n{query}")
    # conn.sql() returns a relation that converts straight to a Polars DataFrame.
    result = conn.sql(query).pl()
    print(result)
    return result


def run_query1(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Who are the names of people who live in Glasgow and are interested in Napoleon?"
    query = f"""
        SELECT firstName, lastName
        FROM GRAPH_TABLE ({G}
            MATCH (p:Person)-[loc:personIsLocatedIn]->(pl:Place),
                  (p:Person)-[int:hasInterest]->(t:Tag)
            WHERE pl.name = 'Glasgow' AND t.name = 'Napoleon'
            COLUMNS (p.firstName AS firstName, p.lastName AS lastName)
        );
    """
    return _execute(conn, 1, query)


def run_query2(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "IDs of posts by Lei Zhang whose content contains Zulu."
    query = f"""
        SELECT postId
        FROM GRAPH_TABLE ({G}
            MATCH (post:Post)-[hc:postHasCreator]->(p:Person)
            WHERE p.firstName = 'Lei' AND p.lastName = 'Zhang'
              AND contains(post.content, 'Zulu')
            COLUMNS (post.id AS postId)
        );
    """
    return _execute(conn, 2, query)


def run_query3(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Creator of post ID 962077547172 and where they studied."
    query = f"""
        SELECT firstName, lastName, orgName
        FROM GRAPH_TABLE ({G}
            MATCH (post:Post)-[hc:postHasCreator]->(person:Person),
                  (person:Person)-[s:studyAt]->(org:Organisation)
            WHERE post.id = 962077547172
            COLUMNS (person.firstName AS firstName, person.lastName AS lastName, org.name AS orgName)
        );
    """
    return _execute(conn, 3, query)


def run_query4(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Comment IDs by Alfredo Gomez with length > 100."
    query = f"""
        SELECT commentId
        FROM GRAPH_TABLE ({G}
            MATCH (c:Comment)-[hc:commentHasCreator]->(p:Person)
            WHERE p.firstName = 'Alfredo' AND p.lastName = 'Gomez'
              AND c.length > 100
            COLUMNS (c.id AS commentId)
        );
    """
    return _execute(conn, 4, query)


def run_query5(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Full names of persons with last name Choi who are members of forums containing John Brown."
    query = f"""
        SELECT DISTINCT firstName, lastName
        FROM GRAPH_TABLE ({G}
            MATCH (f:Forum)-[m:hasMember]->(p:Person)
            WHERE contains(f.title, 'John Brown') AND contains(p.lastName, 'Choi')
            COLUMNS (p.firstName AS firstName, p.lastName AS lastName)
        )
        LIMIT 10;
    """
    return _execute(conn, 5, query)


def run_query6(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "IDs of employees who work at Nova_Air and whose last name contains Bravo."
    query = f"""
        SELECT personId
        FROM GRAPH_TABLE ({G}
            MATCH (p:Person)-[w:workAt]->(o:Organisation)
            WHERE o.name = 'Nova_Air' AND contains(p.lastName, 'Bravo')
            COLUMNS (p.id AS personId)
        );
    """
    return _execute(conn, 6, query)


def run_query7(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Places where person 1786706544494 commented on posts tagged Jamaica."
    query = f"""
        SELECT DISTINCT placeName
        FROM GRAPH_TABLE ({G}
            MATCH (c:Comment)-[hc:commentHasCreator]->(p:Person),
                  (c:Comment)-[r:replyOfPost]->(post:Post)-[ht:postHasTag]->(t:Tag),
                  (c:Comment)-[loc:commentIsLocatedIn]->(place:Place)
            WHERE p.id = 1786706544494 AND t.name = 'Jamaica'
            COLUMNS (place.name AS placeName)
        );
    """
    return _execute(conn, 7, query)


def run_query8(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Distinct IDs of persons born after 1990 who moderate forums containing Emilio Fernandez."
    query = f"""
        SELECT DISTINCT personId
        FROM GRAPH_TABLE ({G}
            MATCH (f:Forum)-[m:hasModerator]->(p:Person)
            WHERE p.birthday > DATE '1990-01-01'
              AND contains(f.title, 'Emilio Fernandez')
            COLUMNS (p.id AS personId)
        );
    """
    return _execute(conn, 8, query)


def run_query9(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Persons with last name Johansson who know someone who studied in Tallinn."
    query = f"""
        SELECT personId, firstName, lastName
        FROM GRAPH_TABLE ({G}
            MATCH (p:Person)-[k:knows]->(p2:Person)-[s:studyAt]->(o:Organisation)
                  -[loc:organisationIsLocatedIn]->(l:Place)
            WHERE l.name = 'Tallinn' AND p.lastName = 'Johansson'
            COLUMNS (p.id AS personId, p.firstName AS firstName, p.lastName AS lastName)
        );
    """
    return _execute(conn, 9, query)


def run_query10(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Unique IDs of persons who commented on posts tagged Cate_Blanchett."
    query = f"""
        SELECT DISTINCT personId
        FROM GRAPH_TABLE ({G}
            MATCH (c:Comment)-[r:replyOfPost]->(post:Post)-[ht:postHasTag]->(t:Tag),
                  (c:Comment)-[hc:commentHasCreator]->(p:Person)
            WHERE t.name = 'Cate_Blanchett'
            COLUMNS (p.id AS personId)
        );
    """
    return _execute(conn, 10, query)


def run_query11(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Non-university organization with most employees."
    query = f"""
        SELECT count(DISTINCT personId) AS num_e, orgName
        FROM GRAPH_TABLE ({G}
            MATCH (p:Person)-[w:workAt]->(o:Organisation)
            WHERE o.type <> 'university'
            COLUMNS (p.id AS personId, o.name AS orgName)
        )
        GROUP BY orgName
        ORDER BY num_e DESC
        LIMIT 1;
    """
    return _execute(conn, 11, query)


def run_query12(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Total number of comments with non-null content created by people in Berlin."
    query = f"""
        SELECT count(DISTINCT commentId) AS num_comments
        FROM GRAPH_TABLE ({G}
            MATCH (c:Comment)-[hc:commentHasCreator]->(p:Person)-[loc:personIsLocatedIn]->(l:Place)
            WHERE c.content IS NOT NULL AND l.name = 'Berlin'
            COLUMNS (c.id AS commentId)
        );
    """
    return _execute(conn, 12, query)


def run_query13(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Total number of persons who liked comments created by Rafael Alonso."
    query = f"""
        SELECT count(DISTINCT likerId) AS num_persons
        FROM GRAPH_TABLE ({G}
            MATCH (p2:Person)-[lk:likeComment]->(c:Comment)-[hc:commentHasCreator]->(p:Person)
            WHERE p.firstName = 'Rafael' AND p.lastName = 'Alonso'
            COLUMNS (p2.id AS likerId)
        );
    """
    return _execute(conn, 13, query)


def run_query14(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Number of forums with tags belonging to the Athlete tagclass."
    query = f"""
        SELECT count(DISTINCT forumId) AS num_forums
        FROM GRAPH_TABLE ({G}
            MATCH (f:Forum)-[ht:forumHasTag]->(t:Tag)-[typ:hasType]->(tc:Tagclass)
            WHERE tc.name = 'Athlete'
            COLUMNS (f.id AS forumId)
        );
    """
    return _execute(conn, 14, query)


def run_query15(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Total number of forums moderated by employees of Air_Tanzania."
    query = f"""
        SELECT count(DISTINCT forumId) AS num_forums
        FROM GRAPH_TABLE ({G}
            MATCH (f:Forum)-[m:hasModerator]->(p:Person)-[w:workAt]->(o:Organisation)
            WHERE o.name = 'Air_Tanzania'
            COLUMNS (f.id AS forumId)
        );
    """
    return _execute(conn, 15, query)


def run_query16(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Number of posts containing Copernicus created by persons located in Mumbai."
    query = f"""
        SELECT count(postId) AS num_posts
        FROM GRAPH_TABLE ({G}
            MATCH (p:Person)-[loc:personIsLocatedIn]->(l:Place),
                  (post:Post)-[hc:postHasCreator]->(p:Person)
            WHERE l.name = 'Mumbai' AND contains(post.content, 'Copernicus')
            COLUMNS (post.id AS postId)
        );
    """
    return _execute(conn, 16, query)


def run_query17(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Most common interest tag among people who studied at Indian_Institute_of_Science."
    query = f"""
        SELECT tagName, count(*) AS tag_count
        FROM GRAPH_TABLE ({G}
            MATCH (p:Person)-[s:studyAt]->(o:Organisation),
                  (p:Person)-[int:hasInterest]->(t:Tag)
            WHERE o.name = 'Indian_Institute_of_Science'
            COLUMNS (t.name AS tagName)
        )
        GROUP BY tagName
        ORDER BY tag_count DESC
        LIMIT 1;
    """
    return _execute(conn, 17, query)


def run_query18(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "People studying at The_Oxford_Educational_Institutions with interest in William_Shakespeare."
    query = f"""
        SELECT count(DISTINCT personId) AS num_p
        FROM GRAPH_TABLE ({G}
            MATCH (p:Person)-[s:studyAt]->(o:Organisation),
                  (p:Person)-[int:hasInterest]->(t:Tag)
            WHERE o.name = 'The_Oxford_Educational_Institutions'
              AND t.name = 'William_Shakespeare'
            COLUMNS (p.id AS personId)
        );
    """
    return _execute(conn, 18, query)


def run_query19(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Place with most comments whose tag contains Copernicus."
    query = f"""
        SELECT placeName, count(commentId) AS comment_count
        FROM GRAPH_TABLE ({G}
            MATCH (c:Comment)-[ht:commentHasTag]->(t:Tag),
                  (c:Comment)-[loc:commentIsLocatedIn]->(l:Place)
            WHERE contains(t.name, 'Copernicus')
            COLUMNS (c.id AS commentId, l.name AS placeName)
        )
        GROUP BY placeName
        ORDER BY comment_count DESC
        LIMIT 1;
    """
    return _execute(conn, 19, query)


def run_query20(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Number of comments containing World War II with length > 1000."
    query = f"""
        SELECT count(commentId) AS long_comment_count
        FROM GRAPH_TABLE ({G}
            MATCH (c:Comment)
            WHERE contains(c.content, 'World War II') AND c.length > 1000
            COLUMNS (c.id AS commentId)
        );
    """
    return _execute(conn, 20, query)


def run_query21(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Has Bill Moore liked the post with ID 1649268446863?"
    query = f"""
        SELECT count(postId) > 0 AS liked
        FROM GRAPH_TABLE ({G}
            MATCH (p2:Person)-[lk:likePost]->(p:Post)
            WHERE p2.firstName = 'Bill' AND p2.lastName = 'Moore'
              AND p.id = 1649268446863
            COLUMNS (p.id AS postId)
        );
    """
    return _execute(conn, 21, query)


def run_query22(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Did anyone who works at Linxair create a comment that replied to a post?"
    query = f"""
        SELECT count(DISTINCT commentId) > 0 AS has_reply_comment
        FROM GRAPH_TABLE ({G}
            MATCH (p:Person)-[w:workAt]->(o:Organisation),
                  (c:Comment)-[r:replyOfPost]->(post:Post),
                  (c:Comment)-[hc:commentHasCreator]->(p:Person)
            WHERE o.name = 'Linxair'
            COLUMNS (c.id AS commentId)
        );
    """
    return _execute(conn, 22, query)


def run_query23(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Is there a person with last name Gurung who is a moderator of a forum tagged Norah_Jones?"
    query = f"""
        SELECT count(DISTINCT personId) > 0 AS has_moderator
        FROM GRAPH_TABLE ({G}
            MATCH (f:Forum)-[m:hasModerator]->(p:Person),
                  (f:Forum)-[ht:forumHasTag]->(t:Tag)
            WHERE t.name = 'Norah_Jones' AND p.lastName = 'Gurung'
            COLUMNS (p.id AS personId)
        );
    """
    return _execute(conn, 23, query)


def run_query24(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Is there a person who lives in Paris and is interested in Cate_Blanchett?"
    query = f"""
        SELECT count(DISTINCT personId) > 0 AS has_person
        FROM GRAPH_TABLE ({G}
            MATCH (p:Person)-[loc:personIsLocatedIn]->(l:Place),
                  (p:Person)-[int:hasInterest]->(t:Tag)
            WHERE l.name = 'Paris' AND t.name = 'Cate_Blanchett'
            COLUMNS (p.id AS personId)
        );
    """
    return _execute(conn, 24, query)


def run_query25(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Does Amit Singh know anyone who studied at MIT_School_of_Engineering?"
    query = f"""
        SELECT count(DISTINCT personId) > 0 AS knows_someone
        FROM GRAPH_TABLE ({G}
            MATCH (amit:Person)-[k:knows]->(p2:Person)-[s:studyAt]->(o:Organisation)
            WHERE amit.firstName = 'Amit' AND amit.lastName = 'Singh'
              AND o.name = 'MIT_School_of_Engineering'
            COLUMNS (p2.id AS personId)
        );
    """
    return _execute(conn, 25, query)


def run_query26(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Are there any forums with tag Benjamin_Franklin that person 10995116287854 is a member of?"
    query = f"""
        SELECT count(DISTINCT forumId) > 0 AS has_forum
        FROM GRAPH_TABLE ({G}
            MATCH (f:Forum)-[m:hasMember]->(p:Person),
                  (f:Forum)-[ht:forumHasTag]->(t:Tag)
            WHERE p.id = 10995116287854 AND t.name = 'Benjamin_Franklin'
            COLUMNS (f.id AS forumId)
        );
    """
    return _execute(conn, 26, query)


def run_query27(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Did any person from Toronto create a comment with tag Winston_Churchill?"
    query = f"""
        SELECT count(DISTINCT commentId) > 0 AS has_comment
        FROM GRAPH_TABLE ({G}
            MATCH (c:Comment)-[hc:commentHasCreator]->(p:Person),
                  (p:Person)-[loc:personIsLocatedIn]->(l:Place),
                  (c:Comment)-[ht:commentHasTag]->(t:Tag)
            WHERE l.name = 'Toronto' AND t.name = 'Winston_Churchill'
            COLUMNS (c.id AS commentId)
        );
    """
    return _execute(conn, 27, query)


def run_query28(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Are there people in Manila interested in tags of type BritishRoyalty?"
    query = f"""
        SELECT count(DISTINCT personId) > 0 AS has_people
        FROM GRAPH_TABLE ({G}
            MATCH (t:Tag)-[typ:hasType]->(tc:Tagclass),
                  (p:Person)-[int:hasInterest]->(t:Tag),
                  (p:Person)-[loc:personIsLocatedIn]->(l:Place)
            WHERE tc.name = 'BritishRoyalty' AND l.name = 'Manila'
            COLUMNS (p.id AS personId)
        );
    """
    return _execute(conn, 28, query)


def run_query29(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Has Justine Fenter written a post using Safari?"
    query = f"""
        SELECT count(postId) > 0 AS has_written_post_with_safari
        FROM GRAPH_TABLE ({G}
            MATCH (post:Post)-[hc:postHasCreator]->(p:Person)
            WHERE p.firstName = 'Justine' AND p.lastName = 'Fenter'
              AND contains(post.browserUsed, 'Safari')
            COLUMNS (post.id AS postId)
        );
    """
    return _execute(conn, 29, query)


def run_query30(conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    "Are there comments replying to posts created by the same person?"
    query = f"""
        SELECT count(DISTINCT commentId) > 0 AS has_self_reply
        FROM GRAPH_TABLE ({G}
            MATCH (c:Comment)-[hc:commentHasCreator]->(creator:Person),
                  (c:Comment)-[r:replyOfPost]->(post:Post)-[phc:postHasCreator]->(creator:Person)
            COLUMNS (c.id AS commentId)
        );
    """
    return _execute(conn, 30, query)


QUERY_FUNCTIONS: dict[int, Callable[[duckdb.DuckDBPyConnection], pl.DataFrame]] = {
    i: globals()[f"run_query{i}"] for i in range(1, 31)
}


def _parse_selection(argv: list[str]) -> list[int] | None:
    if not argv:
        return None
    selection = argv[0].strip()
    if selection in {"run_all", "all"}:
        return None
    indices: list[int] = []
    for part in (p.strip() for p in selection.split(",") if p.strip()):
        try:
            indices.append(int(part))
        except ValueError:
            raise ValueError(f"Invalid query index: {part}")
    return indices


def main(conn: duckdb.DuckDBPyConnection, selected: list[int] | None = None) -> None:
    print(f"DuckDB {duckdb_version(conn)}, DuckPGQ {duckpgq_version(conn)}")
    start = time.perf_counter()
    if selected is None:
        selected = list(QUERY_FUNCTIONS.keys())
    for idx in selected:
        func = QUERY_FUNCTIONS.get(idx)
        if func is None:
            print(f"Skipping unknown query index: {idx}")
            continue
        func(conn)
    elapsed = time.perf_counter() - start
    print(f"\nCompleted {len(selected)} query(ies) in {elapsed:.2f}s")


if __name__ == "__main__":
    if not DB_PATH.is_file():
        raise SystemExit(f"Missing {DB_PATH}. Run build_graph.py first.")
    with connect(DB_PATH) as CONNECTION:
        main(CONNECTION, _parse_selection(sys.argv[1:]))
