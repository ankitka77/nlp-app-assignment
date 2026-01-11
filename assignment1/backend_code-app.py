"""
================================================================================
KNOWLEDGE GRAPH APPLICATION - FLASK BACKEND
================================================================================


================================================================================
DEPENDENCIES:
================================================================================
- Flask: Web framework for building the backend API
- Flask-CORS: Handles Cross-Origin Resource Sharing for frontend-backend communication
- NetworkX: Graph library for constructing, updating, and querying the knowledge graph
- Pandas: Data manipulation library for processing CSV files

Install dependencies:
    pip install Flask networkx flask-cors pandas

================================================================================
API ENDPOINTS:
================================================================================
| Method | Endpoint              | Description                           |
|--------|----------------------|---------------------------------------|
| GET    | /                    | Serve the frontend HTML page          |
| POST   | /api/add_relationship| Add a new relationship to the graph   |
| POST   | /api/upload_csv      | Upload CSV file for bulk import       |
| POST   | /api/query           | Query the graph for entity information|
| GET    | /api/graph_data      | Get all graph data for visualization  |
| GET    | /api/graph_stats     | Get graph statistics                  |
| POST   | /api/clear_graph     | Clear and reset the graph             |

================================================================================
"""

# ==============================================================================
# IMPORTS
# ==============================================================================

# Flask framework for building web applications
from flask import Flask, request, jsonify, send_from_directory

# Flask-CORS for handling Cross-Origin Resource Sharing
# This allows the frontend to communicate with the backend API
from flask_cors import CORS

# NetworkX for graph operations
# Used to construct, update, and query the knowledge graph
import networkx as nx

# Pandas for reading and processing CSV files
import pandas as pd

# JSON for data serialization (imported but not directly used - jsonify handles it)
import json

# OS for file system operations
import os

# Datetime for timestamp operations (if needed for future enhancements)
from datetime import datetime


# ==============================================================================
# FLASK APPLICATION INITIALIZATION
# ==============================================================================

# Create Flask application instance
# - static_folder: Directory containing static files (HTML, CSS, JS)
# - static_url_path: URL path prefix for static files (empty = root)
app = Flask(__name__, static_folder='static', static_url_path='')

# Enable CORS (Cross-Origin Resource Sharing)
# This allows the frontend to make API requests to the backend
# even if they're running on different ports during development
CORS(app)


# ==============================================================================
# KNOWLEDGE GRAPH INITIALIZATION
# ==============================================================================

# Initialize the Knowledge Graph as a Directed Graph (DiGraph)
# DiGraph is used because relationships have direction:
# e.g., "John Doe" --[enrolled_in]--> "Computer Science"
# The arrow indicates the direction of the relationship
knowledge_graph = nx.DiGraph()


# ==============================================================================
# SAMPLE DATA INITIALIZATION
# ==============================================================================

def initialize_sample_data():
    """
    Initialize the knowledge graph with sample University Academic Network data.
    
    This function populates the graph with pre-defined relationships representing
    a university academic network including:
    - Students (John Doe, Jane Smith)
    - Faculty (Dr. Smith, Dr. Johnson)
    - Departments (Computer Science, Engineering Department)
    - Courses (Machine Learning, Data Structures)
    - Research Groups (Research Group A)
    
    Relationship Types:
    - enrolled_in: Student is enrolled in a department/course
    - advised_by: Student is advised by a faculty member
    - teaches: Faculty teaches a course
    - belongs_to: Faculty belongs to a department
    - offered_by: Course is offered by a department
    - part_of: Department is part of a larger unit
    - led_by: Research group is led by a faculty member
    - member_of: Student is member of a research group
    
    Returns:
        int: Number of relationships added to the graph
    """
    
    # Define sample relationships as tuples: (Entity1, Relationship, Entity2)
    sample_relationships = [
        # Student enrollment and advising relationships
        ("John Doe", "enrolled_in", "Computer Science"),
        ("John Doe", "advised_by", "Dr. Smith"),
        ("Jane Smith", "enrolled_in", "Computer Science"),
        ("Jane Smith", "advised_by", "Dr. Smith"),
        
        # Faculty relationships
        ("Dr. Smith", "teaches", "Machine Learning"),
        ("Dr. Smith", "belongs_to", "Computer Science"),
        ("Dr. Johnson", "teaches", "Data Structures"),
        ("Dr. Johnson", "belongs_to", "Computer Science"),
        
        # Course and department relationships
        ("Machine Learning", "offered_by", "Computer Science"),
        ("Data Structures", "offered_by", "Computer Science"),
        ("Computer Science", "part_of", "Engineering Department"),
        
        # Research group relationships
        ("Research Group A", "led_by", "Dr. Smith"),
        ("John Doe", "member_of", "Research Group A"),
    ]
    
    # Add each relationship to the graph
    # add_edge creates nodes automatically if they don't exist
    # The 'relationship' attribute stores the relationship type
    for entity1, relationship, entity2 in sample_relationships:
        knowledge_graph.add_edge(entity1, entity2, relationship=relationship)
    
    return len(sample_relationships)


# Initialize the graph with sample data when the module loads
initialize_sample_data()


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_graph_data_dict():
    """
    Convert the NetworkX graph to a dictionary format suitable for visualization.
    
    This function extracts all nodes and edges from the graph and formats them
    for the vis.js visualization library used in the frontend.
    
    Returns:
        dict: Dictionary containing:
            - success (bool): Whether the operation was successful
            - nodes (list): List of node objects with id, label, title
            - edges (list): List of edge objects with from, to, label, arrows, title
            - stats (dict): Basic graph statistics (total_nodes, total_edges)
            
    Node format:
        {
            'id': 'John Doe',      # Unique identifier
            'label': 'John Doe',   # Display label
            'title': 'Entity: ...' # Tooltip text
        }
        
    Edge format:
        {
            'from': 'John Doe',           # Source node
            'to': 'Computer Science',     # Target node
            'label': 'enrolled_in',       # Relationship label
            'arrows': 'to',               # Arrow direction
            'title': 'John Doe --[...]...' # Tooltip text
        }
    """
    try:
        nodes = []
        edges = []
        
        # Extract nodes from the graph
        # Each node becomes an entity in the visualization
        for node in knowledge_graph.nodes():
            nodes.append({
                'id': node,                    # Unique identifier for the node
                'label': node,                 # Text displayed on the node
                'title': f'Entity: {node}'     # Tooltip shown on hover
            })
        
        # Extract edges (relationships) from the graph
        # Each edge represents a relationship between two entities
        for source, target, data in knowledge_graph.edges(data=True):
            relationship = data.get('relationship', 'unknown')
            edges.append({
                'from': source,                # Source entity
                'to': target,                  # Target entity
                'label': relationship,         # Relationship type
                'arrows': 'to',                # Arrow points to target
                'title': f'{source} --[{relationship}]--> {target}'  # Tooltip
            })
        
        return {
            'success': True,
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_nodes': knowledge_graph.number_of_nodes(),
                'total_edges': knowledge_graph.number_of_edges()
            }
        }
    except Exception as e:
        # Return error information if something goes wrong
        return {
            'success': False,
            'message': f'Error getting graph data: {str(e)}'
        }


# ==============================================================================
# API ROUTES
# ==============================================================================

# ------------------------------------------------------------------------------
# Route: Serve Frontend
# ------------------------------------------------------------------------------
@app.route('/')
def index():
    """
    Serve the main HTML page.
    
    This route handles requests to the root URL ('/') and returns the
    frontend application (index.html) from the static folder.
    
    Returns:
        Response: The index.html file from the static directory
    """
    return send_from_directory('static', 'index.html')


# ------------------------------------------------------------------------------
# Route: Add Relationship
# ------------------------------------------------------------------------------
@app.route('/api/add_relationship', methods=['POST'])
def add_relationship():
    """
    Add a new relationship to the knowledge graph.
    
    This endpoint receives a JSON payload with entity and relationship information
    and adds a new edge (relationship) to the graph.
    
    Request Body (JSON):
        {
            "entity1": "John Doe",           # Source entity (required)
            "relationship": "enrolled_in",   # Relationship type (required)
            "entity2": "Computer Science"    # Target entity (required)
        }
    
    Response (JSON):
        Success:
            {
                "success": true,
                "message": "Relationship added: John Doe --[enrolled_in]--> Computer Science",
                "graph_data": {...}  # Updated graph data for visualization
            }
        
        Error:
            {
                "success": false,
                "message": "Error description"
            }
    
    HTTP Status Codes:
        - 200: Success
        - 400: Bad Request (missing fields)
        - 500: Internal Server Error
    """
    try:
        # Get JSON data from request body
        data = request.json
        
        # Extract and clean the input values
        # strip() removes leading/trailing whitespace
        entity1 = data.get('entity1', '').strip()
        relationship = data.get('relationship', '').strip()
        entity2 = data.get('entity2', '').strip()
        
        # Validate that all required fields are provided
        if not entity1 or not relationship or not entity2:
            return jsonify({
                'success': False,
                'message': 'All fields (Entity 1, Relationship, Entity 2) are required'
            }), 400
        
        # Add the new edge to the graph
        # NetworkX automatically creates nodes if they don't exist
        # The relationship type is stored as an edge attribute
        knowledge_graph.add_edge(entity1, entity2, relationship=relationship)
        
        # Return success response with updated graph data
        return jsonify({
            'success': True,
            'message': f'Relationship added: {entity1} --[{relationship}]--> {entity2}',
            'graph_data': get_graph_data_dict()
        })
    
    except Exception as e:
        # Handle any unexpected errors
        return jsonify({
            'success': False,
            'message': f'Error adding relationship: {str(e)}'
        }), 500


# ------------------------------------------------------------------------------
# Route: Upload CSV
# ------------------------------------------------------------------------------
@app.route('/api/upload_csv', methods=['POST'])
def upload_csv():
    """
    Upload and process a CSV file to add multiple relationships.
    
    This endpoint accepts a CSV file upload and processes each row to add
    relationships to the knowledge graph. The CSV must have specific columns.
    
    Expected CSV Format:
        Entity1,Relationship,Entity2
        Alice Johnson,enrolled_in,Data Science
        Bob Miller,advised_by,Dr. Williams
    
    Request:
        - Content-Type: multipart/form-data
        - file: The CSV file to upload
    
    Response (JSON):
        Success:
            {
                "success": true,
                "message": "Successfully added X relationships from CSV",
                "added_count": X,
                "errors": [...] or null,  # List of row-level errors if any
                "graph_data": {...}
            }
        
        Error:
            {
                "success": false,
                "message": "Error description"
            }
    
    HTTP Status Codes:
        - 200: Success (even with partial errors)
        - 400: Bad Request (no file, wrong format)
        - 500: Internal Server Error
    """
    try:
        # Check if file was included in the request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if a file was actually selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Read CSV file using pandas
        # pandas automatically handles different CSV formats
        df = pd.read_csv(file)
        
        # Validate that required columns exist
        required_columns = ['Entity1', 'Relationship', 'Entity2']
        if not all(col in df.columns for col in required_columns):
            return jsonify({
                'success': False,
                'message': f'CSV must contain columns: {", ".join(required_columns)}'
            }), 400
        
        # Process each row in the CSV
        added_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Extract and clean values from the row
                entity1 = str(row['Entity1']).strip()
                relationship = str(row['Relationship']).strip()
                entity2 = str(row['Entity2']).strip()
                
                # Only add if all values are present
                if entity1 and relationship and entity2:
                    knowledge_graph.add_edge(entity1, entity2, relationship=relationship)
                    added_count += 1
            except Exception as e:
                # Record errors for specific rows but continue processing
                errors.append(f'Row {index + 1}: {str(e)}')
        
        # Return results
        return jsonify({
            'success': True,
            'message': f'Successfully added {added_count} relationships from CSV',
            'added_count': added_count,
            'errors': errors if errors else None,
            'graph_data': get_graph_data_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing CSV: {str(e)}'
        }), 500


# ------------------------------------------------------------------------------
# Route: Query Graph
# ------------------------------------------------------------------------------
@app.route('/api/query', methods=['POST'])
def query_graph():
    """
    Query the knowledge graph for information about an entity.
    
    This endpoint supports multiple query types to retrieve different
    information about an entity in the graph.
    
    Request Body (JSON):
        {
            "entity": "John Doe",     # Entity to query (required)
            "query_type": "all"       # Type of query (required)
        }
    
    Query Types:
        - "neighbors": Get incoming and outgoing relationships
        - "shortest_path": Find shortest paths to all other entities
        - "centrality": Calculate centrality measures (degree, betweenness)
        - "all": Return all of the above
    
    Response (JSON):
        Success:
            {
                "success": true,
                "entity": "John Doe",
                "query_type": "all",
                "results": {
                    "neighbors": {
                        "incoming": [...],
                        "outgoing": [...]
                    },
                    "shortest_paths": {...},
                    "centrality": {
                        "degree": 0.25,
                        "betweenness": 0.15
                    }
                }
            }
        
        Error:
            {
                "success": false,
                "message": "Error description"
            }
    
    HTTP Status Codes:
        - 200: Success
        - 400: Bad Request (missing entity)
        - 404: Not Found (entity doesn't exist)
        - 500: Internal Server Error
    """
    try:
        data = request.json
        query_type = data.get('query_type', '')
        entity = data.get('entity', '').strip()
        
        # Validate that entity name is provided
        if not entity:
            return jsonify({
                'success': False,
                'message': 'Entity name is required for query'
            }), 400
        
        # Check if entity exists in the graph
        if entity not in knowledge_graph:
            return jsonify({
                'success': False,
                'message': f'Entity "{entity}" not found in the graph'
            }), 404
        
        results = {}
        
        # ---- NEIGHBORS QUERY ----
        # Get all directly connected entities (incoming and outgoing)
        if query_type == 'neighbors' or query_type == 'all':
            # predecessors: entities that have edges pointing TO this entity
            predecessors = list(knowledge_graph.predecessors(entity))
            # successors: entities that this entity points TO
            successors = list(knowledge_graph.successors(entity))
            
            results['neighbors'] = {
                'incoming': [
                    {
                        'entity': pred,
                        'relationship': knowledge_graph[pred][entity].get('relationship', 'unknown')
                    }
                    for pred in predecessors
                ],
                'outgoing': [
                    {
                        'entity': succ,
                        'relationship': knowledge_graph[entity][succ].get('relationship', 'unknown')
                    }
                    for succ in successors
                ]
            }
        
        # ---- SHORTEST PATH QUERY ----
        # Find shortest paths from this entity to all other reachable entities
        if query_type == 'shortest_path' or query_type == 'all':
            if len(knowledge_graph.nodes()) > 1:
                paths = {}
                for target in knowledge_graph.nodes():
                    if target != entity:
                        try:
                            # nx.shortest_path finds the shortest path between two nodes
                            path = nx.shortest_path(knowledge_graph, entity, target)
                            paths[target] = path
                        except nx.NetworkXNoPath:
                            # No path exists between these nodes
                            pass
                results['shortest_paths'] = paths
        
        # ---- CENTRALITY QUERY ----
        # Calculate centrality measures for this entity
        if query_type == 'centrality' or query_type == 'all':
            # Degree centrality: fraction of nodes connected to this node
            degree_centrality = nx.degree_centrality(knowledge_graph)
            # Betweenness centrality: how often this node lies on shortest paths
            betweenness_centrality = nx.betweenness_centrality(knowledge_graph)
            
            results['centrality'] = {
                'degree': degree_centrality.get(entity, 0),
                'betweenness': betweenness_centrality.get(entity, 0)
            }
        
        return jsonify({
            'success': True,
            'entity': entity,
            'query_type': query_type,
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error querying graph: {str(e)}'
        }), 500


# ------------------------------------------------------------------------------
# Route: Get Graph Data
# ------------------------------------------------------------------------------
@app.route('/api/graph_data', methods=['GET'])
def get_graph_data():
    """
    Get current graph data for visualization.
    
    This endpoint returns all nodes and edges in a format suitable for
    the vis.js visualization library.
    
    Response (JSON):
        {
            "success": true,
            "nodes": [...],
            "edges": [...],
            "stats": {
                "total_nodes": X,
                "total_edges": Y
            }
        }
    """
    data = get_graph_data_dict()
    if data['success']:
        return jsonify(data)
    else:
        return jsonify(data), 500


# ------------------------------------------------------------------------------
# Route: Get Graph Statistics
# ------------------------------------------------------------------------------
@app.route('/api/graph_stats', methods=['GET'])
def get_graph_stats():
    """
    Get statistics about the knowledge graph.
    
    This endpoint returns various metrics about the current state of the graph.
    
    Response (JSON):
        {
            "success": true,
            "stats": {
                "total_nodes": 10,       # Number of entities
                "total_edges": 13,       # Number of relationships
                "is_connected": true,    # Whether graph is weakly connected
                "density": 0.144,        # Graph density (edges / possible edges)
                "average_degree": 2.6    # Average connections per node
            }
        }
    
    Graph Metrics Explained:
        - total_nodes: Count of unique entities in the graph
        - total_edges: Count of relationships between entities
        - is_connected: True if all nodes can reach all other nodes (ignoring direction)
        - density: Ratio of existing edges to possible edges (0 to 1)
        - average_degree: Average number of connections per node
    """
    try:
        stats = {
            'total_nodes': knowledge_graph.number_of_nodes(),
            'total_edges': knowledge_graph.number_of_edges(),
            'is_connected': nx.is_weakly_connected(knowledge_graph),
            'density': nx.density(knowledge_graph),
            'average_degree': sum(dict(knowledge_graph.degree()).values()) / knowledge_graph.number_of_nodes() if knowledge_graph.number_of_nodes() > 0 else 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting graph stats: {str(e)}'
        }), 500


# ------------------------------------------------------------------------------
# Route: Clear Graph -- Not used in the application
# ------------------------------------------------------------------------------
@app.route('/api/clear_graph', methods=['POST'])
def clear_graph():
    """
    Clear the entire graph and reset to sample data.
    
    This endpoint removes all nodes and edges from the graph,
    then reinitializes it with the sample University Academic Network data.
    
    Response (JSON):
        {
            "success": true,
            "message": "Graph cleared and reset. Removed X nodes and Y edges.",
            "graph_data": {...}
        }
    
    Note: This operation cannot be undone. All custom relationships will be lost.
    """
    try:
        global knowledge_graph
        
        # Store counts before clearing
        node_count = knowledge_graph.number_of_nodes()
        edge_count = knowledge_graph.number_of_edges()
        
        # Create a new empty directed graph
        knowledge_graph = nx.DiGraph()
        
        # Reinitialize with sample data
        initialize_sample_data()
        
        return jsonify({
            'success': True,
            'message': f'Graph cleared and reset. Removed {node_count} nodes and {edge_count} edges.',
            'graph_data': get_graph_data()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error clearing graph: {str(e)}'
        }), 500


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == '__main__':
    """
    Main entry point for the Flask application.
    
    This block runs when the script is executed directly (not imported).
    It starts the Flask development server with the following settings:
    - debug=True: Enable debug mode (auto-reload on code changes, detailed errors)
    - host='0.0.0.0': Listen on all network interfaces (allows external access)
    - port=5000: Run on port 5000
    
    To run the application:
        python app.py
    
    Then open a browser and navigate to:
        http://localhost:5000
    """
    
    # Create static directory if it doesn't exist
    # This ensures the frontend files can be served
    os.makedirs('static', exist_ok=True)
    
    # Print startup information
    print("=" * 60)
    print("Knowledge Graph Application - Flask Backend")
    print("=" * 60)
    print(f"Graph initialized with {knowledge_graph.number_of_nodes()} nodes and {knowledge_graph.number_of_edges()} edges")
    print("Server starting on http://localhost:5000")
    print("=" * 60)
    
    # Start the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)

