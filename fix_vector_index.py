#!/usr/bin/env python3
"""
Directly create Neo4j vector index with correct retrieval query using Neo4j driver
"""
from neo4j import GraphDatabase
from config.neo4jdb import get_db_manager

def create_vector_index():
    db_manager = get_db_manager()

    # Connect directly to Neo4j
    driver = GraphDatabase.driver(
        db_manager.neo4j_uri,
        auth=(db_manager.neo4j_username, db_manager.neo4j_password)
    )

    # The corrected retrieval query with OPTIONAL MATCH
    retrieval_query = """
    WITH collect(node) as nodes
    WITH
    collect {
        UNWIND nodes as n
        MATCH (n)<-[:MENTIONS]-(c:__Chunk__)
        WITH distinct c, count(distinct n) as freq
        RETURN {id:c.id, text: c.text} AS chunkText
        ORDER BY freq DESC
        LIMIT 3
    } AS text_mapping,
    collect {
        UNWIND nodes as n
        OPTIONAL MATCH (n)-[:IN_COMMUNITY]->(c:__Community__)
        WITH distinct c, c.community_rank as rank, c.weight AS weight
        WHERE c IS NOT NULL
        RETURN c.summary
        ORDER BY rank, weight DESC
        LIMIT 3
    } AS report_mapping,
    collect {
        UNWIND nodes as n
        MATCH (n)-[r]-(m:__Entity__)
        WHERE NOT m IN nodes
        RETURN r.description AS descriptionText
        ORDER BY r.weight DESC
        LIMIT 10
    } as outsideRels,
    collect {
        UNWIND nodes as n
        MATCH (n)-[r]-(m:__Entity__)
        WHERE m IN nodes
        RETURN r.description AS descriptionText
        ORDER BY r.weight DESC
        LIMIT 10
    } as insideRels,
    collect {
        UNWIND nodes as n
        RETURN n.description AS descriptionText
    } as entities
    RETURN {
        Chunks: text_mapping,
        Reports: report_mapping,
        Relationships: outsideRels + insideRels,
        Entities: entities
    } AS text, 1.0 AS score, {} AS metadata
    """

    # Create the vector index
    cypher_create = """
    CREATE VECTOR INDEX `vector` FOR (c:__Chunk__) ON (c.embedding)
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 1024,
            `vector.similarity_function`: 'cosine'
        }
    }
    """

    with driver.session() as session:
        result = session.run(cypher_create)
        print("✅ Vector index created successfully!")

        # Set the retrieval query as metadata
        # Note: In Neo4j 5.x, we can't directly set query options on indexes
        # The query is passed from LangChain each time
        print("⚠️  Note: Query will be passed from LangChain application")

    driver.close()

if __name__ == "__main__":
    create_vector_index()
