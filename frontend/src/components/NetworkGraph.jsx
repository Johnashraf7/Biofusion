import React, { useEffect, useRef } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from "cytoscape";

const STYLESHEET = [
  {
    selector: "node",
    style: {
      "background-color": "#3b82f6",
      "label": "data(label)",
      "color": "#e2e8f0",
      "font-size": "10px",
      "font-family": "Inter, sans-serif",
      "text-valign": "bottom",
      "text-halign": "center",
      "text-margin-y": "6px",
      "width": "24px",
      "height": "24px",
      "border-width": "2px",
      "border-color": "#2563eb",
      "transition-property": "background-color, border-color, width, height",
      "transition-duration": "0.3s",
    },
  },
  {
    selector: "node[type='center']",
    style: {
      "background-color": "#06b6d4",
      "border-color": "#0891b2",
      "width": "36px",
      "height": "36px",
      "font-weight": "bold",
      "font-size": "12px",
    },
  },
  {
    selector: "edge",
    style: {
      "width": "data(width)",
      "line-color": "#3b82f6",
      "opacity": "data(opacity)",
      "curve-style": "bezier",
      "overlay-padding": "3px",
    },
  },
  {
    selector: "node:selected",
    style: {
      "background-color": "#f59e0b",
      "border-color": "#d97706",
      "width": "42px",
      "height": "42px",
    },
  },
];

const LAYOUT = {
  name: "cose",
  idealEdgeLength: 100,
  nodeOverlap: 20,
  refresh: 20,
  fit: true,
  padding: 30,
  randomize: false,
  componentSpacing: 100,
  nodeRepulsion: 400000,
  edgeElasticity: 100,
  nestingFactor: 5,
  gravity: 80,
  numIter: 1000,
  initialTemp: 200,
  coolingFactor: 0.95,
  minTemp: 1.0,
};

export default function NetworkGraph({ graph, onNodeTap }) {
  const cyRef = useRef(null);

  const elements = [
    ...graph.nodes.map((node) => ({
      data: { 
        id: node.id, 
        label: node.label, 
        type: node.type,
        fullData: node
      },
      position: { x: Math.random() * 500, y: Math.random() * 500 }
    })),
    ...graph.edges.map((edge, i) => ({
      data: {
        id: `e${i}`,
        source: edge.source,
        target: edge.target,
        width: 1 + (edge.weight || 0.5) * 4,
        opacity: 0.1 + (edge.weight || 0.5) * 0.6
      }
    }))
  ];

  useEffect(() => {
    if (cyRef.current) {
      cyRef.current.on("tap", "node", (event) => {
        const nodeData = event.target.data();
        if (onNodeTap) onNodeTap(nodeData.fullData);
      });
      
      const layout = cyRef.current.layout(LAYOUT);
      layout.run();

      // Ensure graph is centered and visible after layout
      setTimeout(() => {
        if (cyRef.current) {
          cyRef.current.fit();
          cyRef.current.center();
        }
      }, 500);
    }
  }, [graph, onNodeTap]);

  return (
    <div className="network-graph-container" style={{ 
      height: "600px", 
      background: "#0f172a", 
      borderRadius: "12px", 
      border: "1px solid #1e293b",
      overflow: "hidden",
      position: "relative"
    }}>
      <CytoscapeComponent
        elements={elements}
        style={{ width: "100%", height: "100%" }}
        stylesheet={STYLESHEET}
        layout={LAYOUT}
        cy={(cy) => { cyRef.current = cy; }}
        wheelSensitivity={0.1}
      />
      <div className="graph-controls" style={{
        position: "absolute",
        bottom: "1rem",
        right: "1rem",
        display: "flex",
        gap: "0.5rem",
        zIndex: 10
      }}>
        <button 
          onClick={() => cyRef.current.fit()}
          className="btn-glass"
          style={{ padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}
        >
          Reset View
        </button>
      </div>
    </div>
  );
}
