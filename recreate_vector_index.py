#!/usr/bin/env python3
"""
Recreate Neo4j vector index with correct retrieval query using OPTIONAL MATCH
"""
import os
from model.get_models import get_embeddings_model
from config.neo4jdb import get_db_manager
from langchain_community.vectorstores import Neo4jVector

# Get the corrected retrieval query
def get_retrieval_query():
    return """
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

def main():
    print("Creating Neo4jVector with correct retrieval query...")

    # Get models
    embeddings = get_embeddings_model()
    print(f"Embeddings model: {type(embeddings)}")

    # Get database manager
    db_manager = get_db_manager()
    print(f"DB Manager: {type(db_manager)}")

    # Create Neo4jVector store which will create the index with the correct query
    vector_store = Neo4jVector.from_existing_embeddings(
        embeddings,
        url=db_manager.neo4j_uri,
        username=db_manager.neo4j_username,
        password=db_manager.neo4j_password,
        index_name='vector',
        retrieval_query=get_retrieval_query(),
        embedding_property="embedding"
    )

    print("✅ Vector index recreated successfully!")
    print(f"Vector store type: {type(vector_store)}")

    # Test the index
    print("\nTesting vector index...")
    docs = vector_store.similarity_search("旷课学时", k=2)
    print(f"Found {len(docs)} results:")
    for i, doc in enumerate(docs[:2]):
        print(f"{i+1}. {doc.page_content[:100]}...")

if __name__ == "__main__":
    main()
