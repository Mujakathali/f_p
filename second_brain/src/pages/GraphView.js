import { Network, ZoomIn, ZoomOut } from 'lucide-react';
import { useEffect, useState } from 'react';
import ApiService from '../services/api';

const GraphView = () => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getGraph(100);
      const payload = response.graph || { nodes: [], edges: [] };

      // Compute connection counts for sizing
      const connectionCounts = {};
      (payload.edges || []).forEach(edge => {
        connectionCounts[edge.source] = (connectionCounts[edge.source] || 0) + 1;
        connectionCounts[edge.target] = (connectionCounts[edge.target] || 0) + 1;
      });

      const nodes = (payload.nodes || []).map(node => ({
        ...node,
        connections: connectionCounts[node.id] || 0,
        label: node.label || node.type || 'Node',
        type: node.type || 'unknown',
      }));

      setGraphData({
        nodes,
        edges: payload.edges || []
      });
      setError(null);
    } catch (err) {
      console.error('Failed to load graph data:', err);
      setError('Failed to load graph data. Please check if the backend is running.');
      // Fallback to sample data
      setGraphData({
        nodes: [
          { id: 'sample', label: 'Sample Memory', type: 'memory', emotion: '📝', connections: 1 }
        ],
        edges: []
      });
    } finally {
      setLoading(false);
    }
  };

  const getNodeColor = (type) => {
    switch (type) {
      case 'memory': return 'var(--primary-gradient)';
      case 'person': return 'var(--secondary-gradient)';
      case 'topic': return 'var(--bg-gray-100)';
      case 'location': return 'var(--accent-gradient)';
      case 'emotion': return 'var(--warning-gradient)';
      default: return 'var(--bg-gray-50)';
    }
  };

  const getNodeSize = (connections) => {
    return Math.max(40, connections * 8);
  };

  const handleNodeClick = (node) => {
    setSelectedNode(selectedNode?.id === node.id ? null : node);
  };

  return (
    <div className="graph-container">
      <div className="graph-header">
        <div className="graph-title">
          <Network size={24} />
          <h2>Knowledge Graph</h2>
        </div>
        <div className="graph-controls">
          <button className="control-btn" onClick={() => setZoomLevel(prev => Math.max(prev - 0.2, 0.5))}>
            <ZoomOut size={20} />
          </button>
          <span className="zoom-display">{Math.round(zoomLevel * 100)}%</span>
          <button className="control-btn" onClick={() => setZoomLevel(prev => Math.min(prev + 0.2, 3))}>
            <ZoomIn size={20} />
          </button>
        </div>
      </div>

      <div className="graph-legend">
        <div className="legend-item">
          <div className="legend-dot memory"></div>
          <span>Memories</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot person"></div>
          <span>People</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot topic"></div>
          <span>Topics</span>
        </div>
      </div>

      <div className="graph-canvas" style={{ transform: `scale(${zoomLevel})` }}>
        <div className="graph-nodes">
          {graphData.nodes.map((node, index) => (
            <div
              key={node.id}
              className={`graph-node ${node.type} ${selectedNode?.id === node.id ? 'selected' : ''}`}
              style={{
                left: `${20 + (index % 3) * 200}px`,
                top: `${50 + Math.floor(index / 3) * 150}px`,
                width: `${getNodeSize(node.connections)}px`,
                height: `${getNodeSize(node.connections)}px`
              }}
              onClick={() => handleNodeClick(node)}
            >
              <div className="node-content">
                {node.emotion && <span className="node-emotion">{node.emotion}</span>}
                <span className="node-label">{node.label}</span>
                <span className="node-connections">{node.connections}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Connection lines would be drawn here with SVG */}
        <svg className="graph-connections" width="100%" height="100%">
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7"
              refX="0" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="var(--border-medium)" />
            </marker>
          </defs>
          {/* Sample connections */}
          <line x1="100" y1="100" x2="300" y2="100" stroke="var(--border-medium)" strokeWidth="2" markerEnd="url(#arrowhead)" />
          <line x1="100" y1="100" x2="100" y2="250" stroke="var(--border-medium)" strokeWidth="2" markerEnd="url(#arrowhead)" />
          <line x1="300" y1="100" x2="500" y2="100" stroke="var(--border-medium)" strokeWidth="2" markerEnd="url(#arrowhead)" />
        </svg>
      </div>

      {selectedNode && (
        <div className="node-details-panel">
          <div className="panel-header">
            <h3>{selectedNode.label}</h3>
            <button className="close-btn" onClick={() => setSelectedNode(null)}>×</button>
          </div>
          <div className="panel-content">
            <div className="detail-item">
              <span className="detail-label">Type:</span>
              <span className="detail-value">{selectedNode.type}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Connections:</span>
              <span className="detail-value">{selectedNode.connections}</span>
            </div>
            {selectedNode.emotion && (
              <div className="detail-item">
                <span className="detail-label">Emotion:</span>
                <span className="detail-value">{selectedNode.emotion}</span>
              </div>
            )}
            <button className="explore-btn">Explore Connections</button>
          </div>
        </div>
      )}

      <div className="graph-stats">
        <div className="stat-item">
          <span className="stat-number">{graphData.nodes.length}</span>
          <span className="stat-label">Total Nodes</span>
        </div>
        <div className="stat-item">
          <span className="stat-number">12</span>
          <span className="stat-label">Connections</span>
        </div>
        <div className="stat-item">
          <span className="stat-number">3</span>
          <span className="stat-label">Clusters</span>
        </div>
      </div>
    </div>
  );
};

export default GraphView;
