"""
Neo4j graph database connector for relationship management
"""
from neo4j import AsyncGraphDatabase
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class Neo4jConnector:
    def __init__(self):
        self.driver = None
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')

    async def connect(self):
        """Create Neo4j driver connection"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            await self.verify_connectivity()
            await self.create_constraints()
            print("✅ Neo4j connected successfully")
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            raise

    async def disconnect(self):
        """Close Neo4j driver"""
        if self.driver:
            await self.driver.close()

    async def verify_connectivity(self):
        """Verify Neo4j connection"""
        async with self.driver.session() as session:
            await session.run("RETURN 1")

    async def health_check(self) -> bool:
        """Check Neo4j health"""
        try:
            await self.verify_connectivity()
            return True
        except:
            return False

    async def create_constraints(self):
        """Create unique constraints and indexes"""
        constraints = [
            "CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT location_name IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
            "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE INDEX memory_timestamp IF NOT EXISTS FOR (m:Memory) ON (m.timestamp)",
            "CREATE INDEX memory_user_id IF NOT EXISTS FOR (m:Memory) ON (m.user_id)",
            "CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX location_name_index IF NOT EXISTS FOR (l:Location) ON (l.name)"
        ]
        
        async with self.driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    # Constraint might already exist
                    pass

    async def create_memory_node(self, memory_id: int, text: str, memory_type: str, 
                                timestamp: str, sentiment: str = None, user_id: int = None) -> bool:
        """Create a Memory node"""
        query = """
        MERGE (m:Memory {id: $memory_id})
        SET m.text = $text,
            m.type = $memory_type,
            m.timestamp = datetime($timestamp),
            m.sentiment = $sentiment,
            m.user_id = $user_id,
            m.created_at = datetime()
        RETURN m
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query, 
                memory_id=memory_id, 
                text=text, 
                memory_type=memory_type,
                timestamp=timestamp,
                sentiment=sentiment,
                user_id=user_id
            )
            return await result.single() is not None

    async def create_person_node(self, name: str, memory_id: int) -> bool:
        """Create Person node and relationship to Memory"""
        query = """
        MERGE (p:Person {name: $name})
        WITH p
        MATCH (m:Memory {id: $memory_id})
        MERGE (p)-[:MENTIONED_IN]->(m)
        MERGE (m)-[:MENTIONS]->(p)
        RETURN p
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, name=name, memory_id=memory_id)
            return await result.single() is not None

    async def create_location_node(self, name: str, memory_id: int) -> bool:
        """Create Location node and relationship to Memory"""
        query = """
        MERGE (l:Location {name: $name})
        MATCH (m:Memory {id: $memory_id})
        MERGE (m)-[:LOCATED_AT]->(l)
        RETURN l
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, name=name, memory_id=memory_id)
            return await result.single() is not None

    async def create_organization_node(self, name: str, memory_id: int) -> bool:
        """Create Organization node and relationship to Memory"""
        query = """
        MERGE (o:Organization {name: $name})
        MATCH (m:Memory {id: $memory_id})
        MERGE (m)-[:MENTIONS]->(o)
        RETURN o
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, name=name, memory_id=memory_id)
            return await result.single() is not None

    async def create_event_node(self, event_name: str, memory_id: int, 
                               date: str = None) -> bool:
        """Create Event node and relationship to Memory"""
        query = """
        MERGE (e:Event {name: $event_name})
        SET e.date = $date
        WITH e
        MATCH (m:Memory {id: $memory_id})
        MERGE (e)-[:DESCRIBED_IN]->(m)
        MERGE (m)-[:DESCRIBES]->(e)
        RETURN e
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query, 
                event_name=event_name, 
                memory_id=memory_id, 
                date=date
            )
            return await result.single() is not None

    async def create_emotion_relationship(self, memory_id: int, emotion: str, 
                                        intensity: float = 0.5) -> bool:
        """Create emotion relationship for Memory"""
        query = """
        MATCH (m:Memory {id: $memory_id})
        MERGE (e:Emotion {type: $emotion})
        MERGE (m)-[r:HAS_EMOTION]->(e)
        SET r.intensity = $intensity
        RETURN r
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query, 
                memory_id=memory_id, 
                emotion=emotion, 
                intensity=intensity
            )
            return await result.single() is not None

    async def create_similarity_relationship(self, memory_id_1: int, memory_id_2: int, 
                                           similarity_score: float) -> bool:
        """Create similarity relationship between memories"""
        query = """
        MATCH (m1:Memory {id: $memory_id_1})
        MATCH (m2:Memory {id: $memory_id_2})
        MERGE (m1)-[r:SIMILAR_TO]-(m2)
        SET r.score = $similarity_score
        RETURN r
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query, 
                memory_id_1=memory_id_1, 
                memory_id_2=memory_id_2, 
                similarity_score=similarity_score
            )
            return await result.single() is not None

    async def get_memory_graph(self, memory_id: int = None, limit: int = 100, user_id: int = None) -> Dict:
        """Get graph structure for visualization (optionally scoped by user_id)"""
        # Ensure driver is ready
        if not self.driver:
            await self.connect()

        if memory_id:
            query = """
            MATCH (m:Memory {id: $memory_id})
            WHERE ($user_id IS NULL OR m.user_id = $user_id)
            MATCH (m)-[r]-(n)
            RETURN m, r, n
            LIMIT $limit
            """
            params = {"memory_id": memory_id, "limit": limit, "user_id": user_id}
        else:
            query = """
            MATCH (m:Memory)
            WHERE ($user_id IS NULL OR m.user_id = $user_id)
            MATCH (m)-[r]-(n)
            RETURN m, r, n
            LIMIT $limit
            """
            params = {"limit": limit, "user_id": user_id}
        
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            
            nodes = {}
            edges = []
            
            async for record in result:
                # Process memory node
                memory = record["m"]
                memory_data = dict(memory)
                memory_key = f"memory_{memory['id']}"
                memory_data["id"] = memory_key
                memory_data["label"] = "Memory"
                memory_data["type"] = "memory"
                nodes[memory_key] = memory_data
                
                # Process connected node
                connected = record["n"]
                connected_data = dict(connected)
                node_labels = list(connected.labels)
                connected_data["label"] = node_labels[0] if node_labels else "Unknown"
                
                if "name" in connected_data:
                    node_key = f"{connected_data['label'].lower()}_{connected_data['name']}"
                elif "type" in connected_data:
                    node_key = f"{connected_data['label'].lower()}_{connected_data['type']}"
                else:
                    node_key = f"{connected_data['label'].lower()}_{connected.id}"
                
                connected_data["id"] = node_key
                connected_data["type"] = connected_data.get("label", "unknown").lower()
                
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
                "nodes": list(nodes.values()),
                "edges": edges
            }

    async def query_by_person(self, person_name: str) -> List[Dict]:
        """Query memories by person"""
        query = """
        MATCH (p:Person {name: $person_name})-[:MENTIONED_IN]->(m:Memory)
        RETURN m
        ORDER BY m.timestamp DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, person_name=person_name)
            return [dict(record["m"]) async for record in result]

    async def query_by_location(self, location_name: str) -> List[Dict]:
        """Query memories by location"""
        query = """
        MATCH (l:Location {name: $location_name})-[:LOCATION_OF]->(m:Memory)
        RETURN m
        ORDER BY m.timestamp DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, location_name=location_name)
            return [dict(record["m"]) async for record in result]

    async def query_by_emotion(self, emotion_type: str) -> List[Dict]:
        """Query memories by emotion"""
        query = """
        MATCH (m:Memory)-[r:HAS_EMOTION]->(e:Emotion {type: $emotion_type})
        RETURN m, r.intensity as intensity
        ORDER BY r.intensity DESC, m.timestamp DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, emotion_type=emotion_type)
            return [{"memory": dict(record["m"]), "intensity": record["intensity"]} 
                   async for record in result]

    async def find_similar_memories(self, memory_id: int, threshold: float = 0.7) -> List[Dict]:
        """Find memories similar to given memory"""
        query = """
        MATCH (m1:Memory {id: $memory_id})-[r:SIMILAR_TO]-(m2:Memory)
        WHERE r.score >= $threshold
        RETURN m2, r.score as similarity
        ORDER BY r.score DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query, 
                memory_id=memory_id, 
                threshold=threshold
            )
            return [{"memory": dict(record["m2"]), "similarity": record["similarity"]} 
                   async for record in result]

    async def get_statistics(self) -> Dict:
        """Get graph statistics"""
        query = """
        MATCH (m:Memory) 
        OPTIONAL MATCH (p:Person)
        OPTIONAL MATCH (l:Location)
        OPTIONAL MATCH (e:Event)
        OPTIONAL MATCH (em:Emotion)
        RETURN 
            count(DISTINCT m) as memory_count,
            count(DISTINCT p) as person_count,
            count(DISTINCT l) as location_count,
            count(DISTINCT e) as event_count,
            count(DISTINCT em) as emotion_count
        """
        
        async with self.driver.session() as session:
            result = await session.run(query)
            record = await result.single()
            return dict(record) if record else {}
