"""Check that BONDI works locally without needing a running database."""

from bondi.mongodb import MongoCollectionRef, MongoFindQuery, MongoQueryPattern


def test_query_and_pattern_round_trip():
    # Queries are ordinary Python objects until an executor sends them to MongoDB.
    query = MongoFindQuery(
        MongoCollectionRef("bondi_demo", "electric_vehicles"),
        {"Make": "TESLA", "Model Year": {"$gte": 2020}},
    )

    # Saving and restoring must preserve the query and its reusable pattern.
    restored = MongoFindQuery.from_json(query.to_json())
    assert restored == query

    pattern = MongoQueryPattern.from_query(query)
    assert MongoQueryPattern.from_dict(pattern.to_dict()) == pattern
