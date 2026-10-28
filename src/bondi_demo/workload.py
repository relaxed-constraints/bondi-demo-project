"""Generate a workload from observed values in a MongoDB collection."""

from bondi.mongodb import (
    MongoCollectionRef,
    MongoGenerationConfig,
    MongoQueryPattern,
    MongoWorkloadGenerator,
)
from bondi.schema import Schema
from bondi.workload import Workload


def generate_workload(
    collection,
    *,
    num_patterns: int = 5,
    instances_per_pattern: int = 20,
    min_predicates: int = 1,
    max_predicates: int = 3,
    sample_size: int = 10000,
    include_fields: list[str] | None = None,
    seed: int = 42,
) -> tuple[Workload, list[MongoQueryPattern]]:
    """Sample schema values and generate find queries without selectivity constraints.

    The seed controls generation, not MongoDB's random sample. Save the workload
    to reuse exactly the same queries in subsequent benchmarks.
    """
    with collection.aggregate([{"$sample": {"size": sample_size}}]) as documents:
        schema = Schema.from_documents(documents, values="distinct")

    generator = MongoWorkloadGenerator(
        target=MongoCollectionRef(collection.database.name, collection.name),
        schema=schema,
        config=MongoGenerationConfig(
            min_predicates=min_predicates,
            max_predicates=max_predicates,
            include_fields=include_fields,
            limit_probability=0.7,  # fixed for these experiments
            sort_probability=0.5,  # fixed for these experiments
        ),
    )
    return generator.generate(
        num_patterns=num_patterns,
        instances_per_pattern=instances_per_pattern,
        seed=seed,
        return_patterns=True,
    )
