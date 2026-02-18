"""
Graph-related API routes for Neo4j queries and visualization
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from auth.dependencies import get_current_user
from datetime import datetime

from db.neo4j_connector import Neo4jConnector
from db.postgresql_connector import PostgreSQLConnector

# Router instance
graph_router = APIRouter()

# Dependency injection
async def get_neo4j_db():
    return Neo4jConnector()

async def get_postgres_db():
    return PostgreSQLConnector()

@graph_router.get("/get_graph")
async def get_graph(
    memory_id: Optional[int] = None,
    limit: int = Query(100, le=500),
    current_user: Dict = Depends(get_current_user),
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db)
):
    """Get graph structure for visualization (scoped to current user)"""
    try:
        user_id = current_user["user_id"]
        graph_data = await neo4j_db.get_memory_graph(memory_id, limit, user_id=user_id)
        return {
            "graph": graph_data,
            "memory_id": memory_id,
            "limit": limit,
            "node_count": len(graph_data["nodes"]),
            "edge_count": len(graph_data["edges"]),
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph: {str(e)}")

@graph_router.get("/query_graph")
async def query_graph(
    query_type: str = Query(..., regex="^(person|location|emotion|event)$"),
    query_value: str = Query(..., min_length=1),
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db)
):
    """Query graph by entities or relationships"""
    try:
        if query_type == "person":
            results = await neo4j_db.query_by_person(query_value)
        elif query_type == "location":
            results = await neo4j_db.query_by_location(query_value)
        elif query_type == "emotion":
            results = await neo4j_db.query_by_emotion(query_value)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported query type: {query_type}")
        
        return {
            "query_type": query_type,
            "query_value": query_value,
            "results": results,
            "count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph query failed: {str(e)}")

@graph_router.get("/similar_memories_graph/{memory_id}")
async def get_similar_memories_graph(
    memory_id: int,
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db)
):
    """Get similar memories from graph relationships"""
    try:
        similar_memories = await neo4j_db.find_similar_memories(memory_id, threshold)
        return {
            "memory_id": memory_id,
            "threshold": threshold,
            "similar_memories": similar_memories,
            "count": len(similar_memories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar memories: {str(e)}")

@graph_router.get("/graph_stats")
async def get_graph_stats(
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db)
):
    """Get graph database statistics"""
    try:
        stats = await neo4j_db.get_statistics()
        return {
            "statistics": stats,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph stats: {str(e)}")

@graph_router.get("/entities/{entity_type}")
async def get_entities_by_type(
    entity_type: str,
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db)
):
    """Get all entities of a specific type"""
    try:
        entities = await postgres_db.get_entities_by_type(entity_type)
        return {
            "entity_type": entity_type,
            "entities": entities,
            "count": len(entities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entities: {str(e)}")

@graph_router.post("/create_relationship")
async def create_memory_relationship(
    memory_id_1: int,
    memory_id_2: int,
    relationship_type: str,
    similarity_score: float = 0.5,
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db),
    postgres_db: PostgreSQLConnector = Depends(get_postgres_db)
):
    """Create a relationship between two memories"""
    try:
        # Verify memories exist
        memory1 = await postgres_db.get_memory_by_id(memory_id_1)
        memory2 = await postgres_db.get_memory_by_id(memory_id_2)
        
        if not memory1 or not memory2:
            raise HTTPException(status_code=404, detail="One or both memories not found")
        
        # Create relationship in Neo4j
        success = await neo4j_db.create_similarity_relationship(
            memory_id_1, memory_id_2, similarity_score
        )
        
        if success:
            # Store in PostgreSQL as well
            async with postgres_db.connection_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory_relationships 
                    (memory_id_1, memory_id_2, relationship_type, similarity_score)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (memory_id_1, memory_id_2, relationship_type) 
                    DO UPDATE SET similarity_score = $4
                """, memory_id_1, memory_id_2, relationship_type, similarity_score)
            
            return {
                "message": "Relationship created successfully",
                "memory_id_1": memory_id_1,
                "memory_id_2": memory_id_2,
                "relationship_type": relationship_type,
                "similarity_score": similarity_score
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create relationship")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create relationship: {str(e)}")

@graph_router.get("/memory_connections/{memory_id}")
async def get_memory_connections(
    memory_id: int,
    depth: int = Query(1, ge=1, le=3),
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db)
):
    """Get all connections for a specific memory up to a certain depth"""
    try:
        # Get direct connections
        graph_data = await neo4j_db.get_memory_graph(memory_id, limit=200)
        
        return {
            "memory_id": memory_id,
            "depth": depth,
            "connections": graph_data,
            "total_nodes": len(graph_data["nodes"]),
            "total_edges": len(graph_data["edges"])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory connections: {str(e)}")

@graph_router.get("/timeline_graph")
async def get_timeline_graph(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db)
):
    """Get graph data filtered by time range and current user"""
    try:
        # Build time-based query with user filter
        if start_date and end_date:
            query = """
            MATCH (m:Memory)-[r]-(n)
            WHERE m.user_id = $user_id
            AND m.timestamp >= datetime($start_date) 
            AND m.timestamp <= datetime($end_date)
            RETURN m, r, n
            LIMIT 200
            """
            params = {
                "user_id": current_user["user_id"],
                "start_date": start_date, 
                "end_date": end_date
            }
        else:
            # Get recent memories if no date range specified
            query = """
            MATCH (m:Memory)-[r]-(n)
            WHERE m.user_id = $user_id
            AND m.timestamp >= datetime() - duration('P30D')
            RETURN m, r, n
            ORDER BY m.timestamp DESC
            LIMIT 200
            """
            params = {"user_id": current_user["user_id"]}
        
        async with neo4j_db.driver.session() as session:
            result = await session.run(query, **params)
            
            nodes = {}
            edges = []
            
            async for record in result:
                # Process memory node
                memory = record["m"]
                memory_data = dict(memory)
                memory_data["label"] = "Memory"
                nodes[f"memory_{memory['id']}"] = memory_data
                
                # Process connected node
                connected = record["n"]
                connected_data = dict(connected)
                node_labels = list(connected.labels)
                connected_data["label"] = node_labels[0] if node_labels else "Unknown"
                
                if "name" in connected_data:
                    node_key = f"{connected_data['label'].lower()}_{connected_data['name']}"
                else:
                    node_key = f"{connected_data['label'].lower()}_{connected.id}"
                
                nodes[node_key] = connected_data
                
                # Process relationship
                relationship = record["r"]
                edge = {
                    "source": f"memory_{memory['id']}",
                    "target": node_key,
                    "type": relationship.type,
                    "properties": dict(relationship)
                }
                edges.append(edge)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "graph": {
                "nodes": list(nodes.values()),
                "edges": edges
            },
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline graph: {str(e)}")

@graph_router.get("/entity_network/{entity_type}")
async def get_entity_network(
    entity_type: str,
    entity_name: Optional[str] = None,
    neo4j_db: Neo4jConnector = Depends(get_neo4j_db)
):
    """Get network of entities and their relationships"""
    try:
        if entity_name:
            # Get specific entity network
            query = f"""
            MATCH (e:{entity_type.title()} {{name: $entity_name}})-[r]-(m:Memory)-[r2]-(other)
            RETURN e, r, m, r2, other
            LIMIT 100
            """
            params = {"entity_name": entity_name}
        else:
            # Get all entities of this type
            query = f"""
            MATCH (e:{entity_type.title()})-[r]-(m:Memory)
            RETURN e, r, m
            LIMIT 100
            """
            params = {}
        
        async with neo4j_db.driver.session() as session:
            result = await session.run(query, **params)
            
            nodes = {}
            edges = []
            
            async for record in result:
                # Process all nodes in the record
                for key in record.keys():
                    node = record[key]
                    if hasattr(node, 'labels'):  # It's a node
                        node_data = dict(node)
                        node_labels = list(node.labels)
                        node_data["label"] = node_labels[0] if node_labels else "Unknown"
                        
                        if "name" in node_data:
                            node_key = f"{node_data['label'].lower()}_{node_data['name']}"
                        elif "id" in node_data:
                            node_key = f"{node_data['label'].lower()}_{node_data['id']}"
                        else:
                            node_key = f"{node_data['label'].lower()}_{node.id}"
                        
                        nodes[node_key] = node_data
                    elif hasattr(node, 'type'):  # It's a relationship
                        # We'll handle relationships separately
                        pass
        
        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "network": {
                "nodes": list(nodes.values()),
                "edges": edges
            },
            "node_count": len(nodes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity network: {str(e)}")
