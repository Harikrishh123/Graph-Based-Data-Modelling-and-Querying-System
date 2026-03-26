// --- Graph Initialization ---
const container = document.getElementById('graph-container');
const nodes = new vis.DataSet([]);
const edges = new vis.DataSet([]);

const data = { nodes, edges };

// Premium Neo-modern styling for the network map
const options = {
    nodes: {
        shape: 'dot',
        size: 6,
        font: {
            size: 10,
            color: '#e6edf3',
            face: 'Roboto Mono',
            background: 'rgba(13, 17, 23, 0.7)'
        },
        borderWidth: 2,
        shadow: {
            enabled: true,
            color: 'rgba(0,0,0,0.5)',
            size: 10,
            x: 0,
            y: 0
        }
    },
    edges: {
        width: 1.5,
        color: {
            color: '#2b3a4a',
            highlight: '#58a6ff',
            hover: '#79c0ff'
        },
        arrows: {
            to: { enabled: true, scaleFactor: 0.5 }
        },
        smooth: {
            type: 'continuous',
            roundness: 0.5
        },
        font: {
            size: 10,
            color: '#8b949e',
            face: 'Roboto Mono',
            background: 'rgba(13, 17, 23, 0.7)',
            align: 'middle'
        }
    },
    physics: {
        forceAtlas2Based: {
            gravitationalConstant: -50,
            centralGravity: 0.01,
            springLength: 100,
            springConstant: 0.08
        },
        maxVelocity: 50,
        solver: 'forceAtlas2Based',
        timestep: 0.35,
        stabilization: { iterations: 150 }
    },
    interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true
    },
    groups: {
        SalesOrder: { color: { background: '#2f81f7', border: '#a3c2ff' } },
        Delivery: { color: { background: '#d29922', border: '#f7d794' } },
        Billing: { color: { background: '#e34c26', border: '#ffb5a1' } },
        JournalEntry: { color: { background: '#238636', border: '#7ee787' } },
        Product: { color: { background: '#8957e5', border: '#bc90fb' }, shape: 'diamond', size: 8 },
        Customer: { color: { background: '#a371f7', border: '#e1ccff' }, shape: 'star', size: 10 },
        Plant: { color: { background: '#7ee787', border: '#238636' }, shape: 'triangle', size: 6 }
    }
};

const network = new vis.Network(container, data, options);

// Custom Tooltip Logic
const tooltip = document.createElement('div');
tooltip.className = 'custom-tooltip hidden';
document.body.appendChild(tooltip);

network.on('hoverNode', function(params) {
    const node = nodes.get(params.node);
    if (!node || !node.hoverData) return;
    
    // Calculate dynamically bound connections
    const connections = network.getConnectedEdges(params.node).length;
    let htmlContent = '';
    
    const lines = node.hoverData.split('\n');
    lines.forEach((line, index) => {
        if(index === 0) {
            htmlContent += `<div style="font-weight: 600; font-size: 14px; margin-bottom: 8px; color: #1f2328;">${line}</div>`;
        } else if(line.includes(':')) {
            const idx = line.indexOf(':');
            const key = line.substring(0, idx).trim();
            const val = line.substring(idx + 1).trim();
            htmlContent += `<div style="margin-bottom: 4px; display: flex;"><span style="color: #656d76; min-width: 150px; display: inline-block;">${key}</span> <span style="color: #24292f;">${val}</span></div>`;
        } else {
            htmlContent += `<div style="margin-bottom: 4px; color: #656d76; font-style: italic; font-size: 11px;">${line}</div>`;
        }
    });
    
    htmlContent += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eaeaea; color: #24292f; font-size: 11px;">Connections: ${connections}</div>`;
    
    tooltip.innerHTML = htmlContent;
    tooltip.classList.remove('hidden');
});

network.on('blurNode', function() {
    tooltip.classList.add('hidden');
});

network.on('hoverEdge', function(params) {
    const edge = edges.get(params.edge);
    if (!edge || !edge.hoverData) return;
    
    let htmlContent = '';
    const lines = edge.hoverData.split('\n');
    lines.forEach((line, index) => {
        if(index === 0) {
            htmlContent += `<div style="font-weight: 600; font-size: 14px; margin-bottom: 8px; color: #1f2328;">${line} (Connection)</div>`;
        } else if(line.includes(':')) {
            const idx = line.indexOf(':');
            const key = line.substring(0, idx).trim();
            const val = line.substring(idx + 1).trim();
            htmlContent += `<div style="margin-bottom: 4px; display: flex;"><span style="color: #656d76; min-width: 150px; display: inline-block;">${key}</span> <span style="color: #24292f;">${val}</span></div>`;
        } else {
            htmlContent += `<div style="margin-bottom: 4px; color: #656d76; font-style: italic; font-size: 11px;">${line}</div>`;
        }
    });

    htmlContent += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eaeaea; color: #24292f; font-size: 11px;">Connections: 2</div>`;

    tooltip.innerHTML = htmlContent;
    tooltip.classList.remove('hidden');
});

network.on('blurEdge', function() {
    tooltip.classList.add('hidden');
});

document.addEventListener('mousemove', function(e) {
    if(!tooltip.classList.contains('hidden')) {
        let left = e.pageX + 15;
        let top = e.pageY + 15;
        // Edge containment
        if(left + tooltip.offsetWidth > window.innerWidth) left = e.pageX - tooltip.offsetWidth - 15;
        if(top + tooltip.offsetHeight > window.innerHeight) top = e.pageY - tooltip.offsetHeight - 15;
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }
});

// UI Elements
const msgContainer = document.getElementById('chat-messages');
const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');
const stats = document.getElementById('graph-stats');
const clearBtn = document.getElementById('clear-graph-btn');

// Optional API Key Modal logic
let apiKey = localStorage.getItem('nexus_o2c_api_key');
if(!apiKey) { document.getElementById('setup-modal').classList.remove('hidden'); }

document.getElementById('save-key-btn').addEventListener('click', () => {
    const k = document.getElementById('api-key-input').value;
    if(k) {
        apiKey = k;
        localStorage.setItem('nexus_o2c_api_key', k);
        document.getElementById('setup-modal').classList.add('hidden');
    }
});

let chatHistory = [];

function updateStats() {
    stats.textContent = `Nodes: ${nodes.length} | Edges: ${edges.length}`;
}

clearBtn.addEventListener('click', () => {
    nodes.clear();
    edges.clear();
    updateStats();
});

function appendMessage(role, text) {
    const isUser = role === 'user';
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user-msg' : 'system-msg'}`;
    
    const avatar = document.createElement('div');
    avatar.className = `avatar ${isUser ? 'user-avatar' : 'system-avatar'}`;
    avatar.textContent = isUser ? 'YOU' : 'AI';
    
    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = text.replace(/\n/g, '<br>');
    
    div.appendChild(avatar);
    div.appendChild(bubble);
    
    // Remove loading indicator if exists
    const loader = msgContainer.querySelector('.loading-msg');
    if(loader && !isUser) loader.remove();
    
    msgContainer.appendChild(div);
    msgContainer.scrollTop = msgContainer.scrollHeight;
}

function showLoading() {
    const div = document.createElement('div');
    div.className = 'message system-msg loading-msg';
    div.innerHTML = `
        <div class="avatar system-avatar">AI</div>
        <div class="msg-bubble typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    msgContainer.appendChild(div);
    msgContainer.scrollTop = msgContainer.scrollHeight;
}

function processGraphData(graphData, shouldClear = false) {
    if(!graphData || (!graphData.nodes.length && !graphData.edges.length)) return;
    
    if (shouldClear) {
        nodes.clear();
        edges.clear();
    }
    
    // Merge new nodes/edges incrementally to keep layout stable
    const newNodes = [];
    graphData.nodes.forEach(n => {
        if(!nodes.get(n.id)) {
            const nodeToAdd = {...n};
            nodeToAdd.hoverData = n.title;
            delete nodeToAdd.title;
            delete nodeToAdd.label;
            newNodes.push(nodeToAdd);
        }
    });
    
    const newEdges = [];
    graphData.edges.forEach(e => {
        // Create unique ID for edge to prevent duplicates
        const eid = e.source + '_' + e.label + '_' + e.target;
        if(!edges.get(eid)) {
            newEdges.push({ id: eid, from: e.source, to: e.target, hoverData: e.title });
        }
    });
    
    nodes.add(newNodes);
    edges.add(newEdges);
    
    updateStats();
    
    // Fit network to new nodes
    if(newNodes.length > 0) {
        network.fit({ animation: { duration: 1000, easingFunction: 'easeInOutQuad' } });
    }
}

function highlightGraphData(graphData) {
    if(!graphData || (!graphData.nodes.length && !graphData.edges.length)) {
        return;
    }
    
    // Create sets of IDs from graphData
    const activeNodeIds = new Set(graphData.nodes.map(n => n.id.toString()));
    const activeEdgeIds = new Set(graphData.edges.map(e => e.source + '_' + e.label + '_' + e.target));
    
    // Update existing nodes
    const nodesToUpdate = [];
    nodes.get().forEach(n => {
        if(activeNodeIds.has(n.id.toString())) {
            nodesToUpdate.push({ id: n.id, opacity: 1.0, font: { color: '#e6edf3' } });
        } else {
            nodesToUpdate.push({ id: n.id, opacity: 0.15, font: { color: 'rgba(230,237,243,0.15)' } });
        }
    });
    nodes.update(nodesToUpdate);
    
    const edgesToUpdate = [];
    edges.get().forEach(e => {
        if(activeEdgeIds.has(e.id)) {
            edgesToUpdate.push({ id: e.id, color: { color: '#58a6ff', opacity: 1.0 }, width: 2.5 });
        } else {
            edgesToUpdate.push({ id: e.id, color: { color: 'rgba(43,58,74,0.15)', opacity: 0.15 }, width: 1.0 });
        }
    });
    edges.update(edgesToUpdate);
    
    // Also, if the graphData introduces NEW nodes, add them
    const newNodes = [];
    graphData.nodes.forEach(n => {
        if(!nodes.get(n.id)) {
            const nodeToAdd = {...n, opacity: 1.0};
            nodeToAdd.hoverData = n.title;
            delete nodeToAdd.title;
            delete nodeToAdd.label;
            newNodes.push(nodeToAdd);
        }
    });
    
    const newEdges = [];
    graphData.edges.forEach(e => {
        const eid = e.source + '_' + e.label + '_' + e.target;
        if(!edges.get(eid)) {
            newEdges.push({ id: eid, from: e.source, to: e.target, hoverData: e.title, color: { color: '#58a6ff', opacity: 1.0 }, width: 2.5 });
        }
    });
    
    if(newNodes.length > 0) nodes.add(newNodes);
    if(newEdges.length > 0) edges.add(newEdges);
    
    updateStats();
    
    // Focus on the highlighted nodes
    if(graphData.nodes.length > 0) {
        network.fit({ nodes: Array.from(activeNodeIds), animation: { duration: 1000, easingFunction: 'easeInOutQuad' } });
    }
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const txt = input.value.trim();
    if(!txt) return;
    
    appendMessage('user', txt);
    chatHistory.push({ role: 'user', content: txt });
    input.value = '';
    
    showLoading();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': apiKey ? `Bearer ${apiKey}` : ''
            },
            body: JSON.stringify({ messages: chatHistory })
        });
        
        const data = await response.json();
        
        if(data.content) {
            appendMessage('assistant', data.content);
            chatHistory.push({ role: 'assistant', content: data.content });
        } else {
            appendMessage('assistant', 'Error parsing response.');
        }
        
        if(data.graph) {
            highlightGraphData(data.graph); 
        }
        
    } catch(err) {
        console.error(err);
        appendMessage('assistant', 'Connection to backend failed. Make sure the server is running on port 8000.');
    }
});

async function initGraph() {
    try {
        const response = await fetch('/api/graph/init', {
            headers: {
                'Authorization': apiKey ? `Bearer ${apiKey}` : ''
            }
        });
        const data = await response.json();
        if(data && data.graph) {
            processGraphData(data.graph, false);
        }
    } catch(err) {
        console.error("Could not init graph: ", err);
    }
}
initGraph();
