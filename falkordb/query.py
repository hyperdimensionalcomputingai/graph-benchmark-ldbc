import os
import sys
import time
from typing import Any, Callable

from dotenv import load_dotenv
from falkordb import FalkorDB, Graph

load_dotenv()

FALKORDB_HOST = os.environ.get("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.environ.get("FALKORDB_PORT", "6379"))
FALKORDB_GRAPH = os.environ.get("FALKORDB_GRAPH", "ldbc_snb_sf1")


def _execute(graph: Graph, idx: int, query: str) -> list[dict[str, Any]]:
    print(f"\nQuery {idx}:\n{query}")
    result = graph.ro_query(query)
    names = [name for _, name in result.header]
    records = [dict(zip(names, row)) for row in result.result_set]
    print(records)
    return records


def run_query1(graph: Graph):
    "Who are the names of people who live in Glasgow and are interested in Napoleon?"
    query = """
        MATCH (p:Person)-[:personIsLocatedIn]->(pl:Place),
              (p)-[:hasInterest]->(t:Tag)
        WHERE pl.name = "Glasgow" AND t.name = "Napoleon"
        RETURN p.firstName, p.lastName;
    """
    return _execute(graph, 1, query)


def run_query2(graph: Graph):
    "IDs of posts by Lei Zhang whose content contains Zulu."
    query = """
        MATCH (p:Person)<-[:postHasCreator]-(post:Post)
        WHERE p.firstName = "Lei" AND p.lastName = "Zhang"
          AND post.content CONTAINS "Zulu"
        RETURN post.ID;
    """
    return _execute(graph, 2, query)


def run_query3(graph: Graph):
    "Creator of post ID 962077547172 and where they studied."
    query = """
        MATCH (post:Post {ID: 962077547172})-[:postHasCreator]->(person:Person),
              (person)-[:studyAt]->(org:Organisation)
        RETURN person.firstName, person.lastName, org.name;
    """
    return _execute(graph, 3, query)


def run_query4(graph: Graph):
    "Comment IDs by Alfredo Gomez with length > 100."
    query = """
        MATCH (p:Person)<-[:commentHasCreator]-(c:Comment)
        WHERE p.firstName = "Alfredo"
          AND p.lastName = "Gomez"
          AND c.length > 100
        RETURN c.ID;
    """
    return _execute(graph, 4, query)


def run_query5(graph: Graph):
    "Full names of persons with last name Choi who are members of forums containing John Brown."
    query = """
        MATCH (f:Forum)-[:hasMember]->(p:Person)
        WHERE f.title CONTAINS "John Brown"
          AND p.lastName CONTAINS "Choi"
        RETURN DISTINCT p.firstName, p.lastName
        LIMIT 10;
    """
    return _execute(graph, 5, query)


def run_query6(graph: Graph):
    "IDs of employees who work at Nova_Air and whose last name contains Bravo."
    query = """
        MATCH (p:Person)-[:workAt]->(o:Organisation)
        WHERE o.name = "Nova_Air" AND p.lastName CONTAINS "Bravo"
        RETURN p.ID;
    """
    return _execute(graph, 6, query)


def run_query7(graph: Graph):
    "Places where person 1786706544494 commented on posts tagged Jamaica."
    query = """
        MATCH (p:Person {ID: 1786706544494})<-[:commentHasCreator]-(c:Comment)
              -[:replyOfPost]->(post:Post)-[:postHasTag]->(t:Tag),
              (c)-[:commentIsLocatedIn]->(place:Place)
        WHERE t.name = "Jamaica"
        RETURN DISTINCT place.name;
    """
    return _execute(graph, 7, query)


def run_query8(graph: Graph):
    "Distinct IDs of persons born after 1990 who moderate forums containing Emilio Fernandez."
    query = """
        MATCH (p:Person)<-[:hasModerator]-(f:Forum)
        WHERE date(p.birthday) > date("1990-01-01")
          AND f.title CONTAINS "Emilio Fernandez"
        RETURN DISTINCT p.ID;
    """
    return _execute(graph, 8, query)


def run_query9(graph: Graph):
    "Persons with last name Johansson who know someone who studied in Tallinn."
    query = """
        MATCH (p:Person)-[:knows]->(p2:Person)-[:studyAt]->(o:Organisation)
              -[:organisationIsLocatedIn]->(l:Place)
        WHERE l.name = "Tallinn" AND p.lastName = "Johansson"
        RETURN p.ID, p.firstName, p.lastName;
    """
    return _execute(graph, 9, query)


def run_query10(graph: Graph):
    "Unique IDs of persons who commented on posts tagged Cate_Blanchett."
    query = """
        MATCH (c:Comment)-[:replyOfPost]->(post:Post)-[:postHasTag]->(t:Tag),
              (c)-[:commentHasCreator]->(p:Person)
        WHERE t.name = "Cate_Blanchett"
        RETURN DISTINCT p.ID;
    """
    return _execute(graph, 10, query)


def run_query11(graph: Graph):
    "Non-university organization with most employees."
    query = """
        MATCH (p:Person)-[:workAt]->(o:Organisation)
        WHERE o.type <> "university"
        RETURN COUNT(DISTINCT p.ID) AS num_e, o.name
        ORDER BY num_e DESC
        LIMIT 1;
    """
    return _execute(graph, 11, query)


def run_query12(graph: Graph):
    "Total number of comments with non-null content created by people in Berlin."
    query = """
        MATCH (c:Comment)-[:commentHasCreator]->(p:Person)-[:personIsLocatedIn]->(l:Place)
        WHERE c.content IS NOT NULL AND l.name = "Berlin"
        RETURN COUNT(DISTINCT c.ID) AS num_comments;
    """
    return _execute(graph, 12, query)


def run_query13(graph: Graph):
    "Total number of persons who liked comments created by Rafael Alonso."
    query = """
        MATCH (p:Person)<-[:commentHasCreator]-(c:Comment)<-[:likeComment]-(p2:Person)
        WHERE p.firstName = "Rafael" AND p.lastName = "Alonso"
        RETURN COUNT(DISTINCT p2.ID) AS num_persons;
    """
    return _execute(graph, 13, query)


def run_query14(graph: Graph):
    "Number of forums with tags belonging to the Athlete tagclass."
    query = """
        MATCH (f:Forum)-[:forumHasTag]->(:Tag)-[:hasType]->(:Tagclass {name: "Athlete"})
        RETURN COUNT(DISTINCT f.ID) AS num_forums;
    """
    return _execute(graph, 14, query)


def run_query15(graph: Graph):
    "Total number of forums moderated by employees of Air_Tanzania."
    query = """
        MATCH (f:Forum)-[:hasModerator]->(p:Person)-[:workAt]->(o:Organisation)
        WHERE o.name = "Air_Tanzania"
        RETURN COUNT(DISTINCT f.ID) AS num_forums;
    """
    return _execute(graph, 15, query)


def run_query16(graph: Graph):
    "Number of posts containing Copernicus created by persons located in Mumbai."
    query = """
        MATCH (p:Person)-[:personIsLocatedIn]->(l:Place),
              (p)<-[:postHasCreator]-(post:Post)
        WHERE l.name = "Mumbai" AND post.content CONTAINS "Copernicus"
        RETURN COUNT(post.ID) AS num_posts;
    """
    return _execute(graph, 16, query)


def run_query17(graph: Graph):
    "Most common interest tag among people who studied at Indian_Institute_of_Science."
    query = """
        MATCH (p:Person)-[:studyAt]->(o:Organisation), (p)-[:hasInterest]->(t:Tag)
        WHERE o.name = "Indian_Institute_of_Science"
        RETURN t.name, COUNT(*) AS tag_count
        ORDER BY tag_count DESC
        LIMIT 1;
    """
    return _execute(graph, 17, query)


def run_query18(graph: Graph):
    "People studying at The_Oxford_Educational_Institutions with interest in William_Shakespeare."
    query = """
        MATCH (p:Person)-[:studyAt]->(o:Organisation), (p)-[:hasInterest]->(t:Tag)
        WHERE o.name = "The_Oxford_Educational_Institutions"
          AND t.name = "William_Shakespeare"
        RETURN COUNT(DISTINCT p.ID) AS num_p;
    """
    return _execute(graph, 18, query)


def run_query19(graph: Graph):
    "Place with most comments whose tag contains Copernicus."
    query = """
        MATCH (c:Comment)-[:commentHasTag]->(t:Tag), (c)-[:commentIsLocatedIn]->(l:Place)
        WHERE t.name CONTAINS "Copernicus"
        RETURN l.name, COUNT(c.ID) AS comment_count
        ORDER BY comment_count DESC
        LIMIT 1;
    """
    return _execute(graph, 19, query)


def run_query20(graph: Graph):
    "Number of comments containing World War II with length > 1000."
    query = """
        MATCH (c:Comment)
        WHERE c.content CONTAINS "World War II" AND c.length > 1000
        RETURN COUNT(c.ID) AS long_comment_count;
    """
    return _execute(graph, 20, query)


def run_query21(graph: Graph):
    "Has Bill Moore liked the post with ID 1649268446863?"
    query = """
        MATCH (p:Post)<-[:likePost]-(p2:Person)
        WHERE p2.firstName = "Bill" AND p2.lastName = "Moore"
          AND p.ID = 1649268446863
        RETURN COUNT(p.ID) > 0 AS liked;
    """
    return _execute(graph, 21, query)


def run_query22(graph: Graph):
    "Did anyone who works at Linxair create a comment that replied to a post?"
    query = """
        MATCH (p:Person)-[:workAt]->(o:Organisation),
              (c:Comment)-[:replyOfPost]->(post:Post),
              (c)-[:commentHasCreator]->(p)
        WHERE o.name = "Linxair"
        RETURN COUNT(DISTINCT c.ID) > 0 AS has_reply_comment;
    """
    return _execute(graph, 22, query)


def run_query23(graph: Graph):
    "Is there a person with last name Gurung who is a moderator of a forum tagged Norah_Jones?"
    query = """
        MATCH (p:Person)<-[:hasModerator]-(f:Forum)-[:forumHasTag]->(t:Tag)
        WHERE t.name = "Norah_Jones" AND p.lastName = "Gurung"
        RETURN COUNT(DISTINCT p.ID) > 0 AS has_moderator;
    """
    return _execute(graph, 23, query)


def run_query24(graph: Graph):
    "Is there a person who lives in Paris and is interested in Cate_Blanchett?"
    query = """
        MATCH (p:Person)-[:personIsLocatedIn]->(l:Place), (p)-[:hasInterest]->(t:Tag)
        WHERE l.name = "Paris" AND t.name = "Cate_Blanchett"
        RETURN COUNT(DISTINCT p.ID) > 0 AS has_person;
    """
    return _execute(graph, 24, query)


def run_query25(graph: Graph):
    "Does Amit Singh know anyone who studied at MIT_School_of_Engineering?"
    query = """
        MATCH (amit:Person)-[:knows]->(p2:Person)-[:studyAt]->(o:Organisation)
        WHERE amit.firstName = "Amit" AND amit.lastName = "Singh"
          AND o.name = "MIT_School_of_Engineering"
        RETURN COUNT(DISTINCT p2.ID) > 0 AS knows_someone;
    """
    return _execute(graph, 25, query)


def run_query26(graph: Graph):
    "Are there any forums with tag Benjamin_Franklin that person 10995116287854 is a member of?"
    query = """
        MATCH (f:Forum)-[:hasMember]->(p:Person), (f)-[:forumHasTag]->(t:Tag)
        WHERE p.ID = 10995116287854 AND t.name = "Benjamin_Franklin"
        RETURN COUNT(DISTINCT f.ID) > 0 AS has_forum;
    """
    return _execute(graph, 26, query)


def run_query27(graph: Graph):
    "Did any person from Toronto create a comment with tag Winston_Churchill?"
    query = """
        MATCH (c:Comment)-[:commentHasCreator]->(p:Person),
              (p)-[:personIsLocatedIn]->(l:Place),
              (c)-[:commentHasTag]->(t:Tag)
        WHERE l.name = "Toronto" AND t.name = "Winston_Churchill"
        RETURN COUNT(DISTINCT c.ID) > 0 AS has_comment;
    """
    return _execute(graph, 27, query)


def run_query28(graph: Graph):
    "Are there people in Manila interested in tags of type BritishRoyalty?"
    query = """
        MATCH (t:Tag)-[:hasType]->(tc:Tagclass),
              (p:Person)-[:hasInterest]->(t),
              (p)-[:personIsLocatedIn]->(l:Place)
        WHERE tc.name = "BritishRoyalty" AND l.name = "Manila"
        RETURN COUNT(DISTINCT p.ID) > 0 AS has_people;
    """
    return _execute(graph, 28, query)


def run_query29(graph: Graph):
    "Has Justine Fenter written a post using Safari?"
    query = """
        MATCH (p:Person)<-[:postHasCreator]-(post:Post)
        WHERE p.firstName = "Justine" AND p.lastName = "Fenter"
          AND post.browserUsed CONTAINS "Safari"
        RETURN COUNT(post.ID) > 0 AS has_written_post_with_safari;
    """
    return _execute(graph, 29, query)


def run_query30(graph: Graph):
    "Are there comments replying to posts created by the same person?"
    query = """
        MATCH (c:Comment)-[:commentHasCreator]->(creator:Person),
              (c)-[:replyOfPost]->(post:Post)-[:postHasCreator]->(creator)
        RETURN COUNT(DISTINCT c.ID) > 0 AS has_self_reply;
    """
    return _execute(graph, 30, query)


QUERY_FUNCTIONS: dict[int, Callable[[Graph], object]] = {
    1: run_query1,
    2: run_query2,
    3: run_query3,
    4: run_query4,
    5: run_query5,
    6: run_query6,
    7: run_query7,
    8: run_query8,
    9: run_query9,
    10: run_query10,
    11: run_query11,
    12: run_query12,
    13: run_query13,
    14: run_query14,
    15: run_query15,
    16: run_query16,
    17: run_query17,
    18: run_query18,
    19: run_query19,
    20: run_query20,
    21: run_query21,
    22: run_query22,
    23: run_query23,
    24: run_query24,
    25: run_query25,
    26: run_query26,
    27: run_query27,
    28: run_query28,
    29: run_query29,
    30: run_query30,
}


def _parse_selection(argv: list[str]) -> list[int] | None:
    if not argv:
        return None
    selection = argv[0].strip()
    if selection in {"run_all", "all"}:
        return None
    parts = [p.strip() for p in selection.split(",") if p.strip()]
    indices: list[int] = []
    for part in parts:
        try:
            indices.append(int(part))
        except ValueError:
            raise ValueError(f"Invalid query index: {part}")
    return indices


def main(graph: Graph, selected: list[int] | None = None) -> None:
    start = time.perf_counter()
    if selected is None:
        selected = list(QUERY_FUNCTIONS.keys())
    for idx in selected:
        func = QUERY_FUNCTIONS.get(idx)
        if func is None:
            print(f"Skipping unknown query index: {idx}")
            continue
        func(graph)
    elapsed = time.perf_counter() - start
    print(f"\nCompleted {len(selected)} query(ies) in {elapsed:.2f}s")


if __name__ == "__main__":
    db = FalkorDB(host=FALKORDB_HOST, port=FALKORDB_PORT)
    graph = db.select_graph(FALKORDB_GRAPH)
    selected_queries = _parse_selection(sys.argv[1:])
    main(graph, selected_queries)
    db.close()
