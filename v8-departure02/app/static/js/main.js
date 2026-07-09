// ════════════════════════════════════════════════════════════════
//  State
// ════════════════════════════════════════════════════════════════
let graph = null;   // full graph data from API
let currentStep = 0;
let playing = false;
let animTimer = null;
const FPS = 1.5;    // steps per second (easy to change)
const DELAY = 1000 / FPS;

// ════════════════════════════════════════════════════════════════
//  Init
// ════════════════════════════════════════════════════════════════
window.addEventListener('DOMContentLoaded', async () => {
    await loadFileList();
    window.addEventListener('resize', () => { if (graph) drawGraph(currentStep); });
});

// ════════════════════════════════════════════════════════════════
//  API:
//  - Gets the json-formatted file from the 'path' endpoint
// ════════════════════════════════════════════════════════════════

async function api(path, method = 'GET') {
    const r = await fetch(path, {
        method,
        headers: {
            'Content-Type': 'application/json'
        },
    });
    if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.detail || r.statusText);
    }
    const data = await r.json();        // parse JSON from stream
    console.log("Parsed JSON:", data);
    return data;
}

// ════════════════════════════════════════════════════════════════
//  File list:
//  - all files available in the /api/files endpoint
// ════════════════════════════════════════════════════════════════
async function loadFileList() {
    const { files } = await api('/api/files');
    const el = document.getElementById('file-list');
    if (!files.length) {
        el.innerHTML = '<div style="color:var(--muted);font-size:.7rem">No files found</div>';
        return;
    }
    el.innerHTML = '';
    files.forEach(f => {
        const btn = document.createElement('button');
        btn.className = 'file-btn';
        btn.textContent = f;
        console.log("inside forEach", f);
        btn.onclick = () => loadGraph(f, btn);
        el.appendChild(btn);
    });
}

// ════════════════════════════════════════════════════════════════
//  Load graph:
//  A very relevant function.
//  - POSTing to the api/load/<file name> will bring the graph data at the api/graph endpoint
//  - It will make the button of that graph inactive and will populate the table
//  - It will also set the Slider accordingly to initial state
//  - It will then set the buttons to manipulate the graph
// ════════════════════════════════════════════════════════════════

async function loadGraph(filename, btn) {
    stopAnimation();
    setStatus('status', 'loading…');
    try {
        await api(`/api/load/${filename}`, 'POST');
        graph = await api('/api/graph', 'GET');
    } catch (e) {
        toast(`Error: ${e.message}`, true);
        setStatus('status', 'error', true);
        return;
    }
    console.log("Graph loaded:", graph);
    // Mark active file button
    document.querySelectorAll('.file-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Update sidebar info
    document.getElementById('s-name').textContent = graph.name;
    document.getElementById('s-nodes').textContent = graph.nodes.length;
    document.getElementById('s-edges').textContent = graph.edges.length;
    document.getElementById('s-agents').textContent = graph.agents.length;
    document.getElementById('s-steps').textContent = graph.schedule.length;
    setStatus('status', 'ready', false, true);

    // Agent legend
    const legend = document.getElementById('agent-legend');
    legend.innerHTML = '';
    graph.agents.forEach(a => {
        const row = document.createElement('div');
        row.className = 'agent-row';
        row.innerHTML = `<div class="agent-dot" style="background:${a.color}"></div>${a.name}`;
        legend.appendChild(row);
    });

    // Slider
    const slider = document.getElementById('frame-slider');
    slider.min = 0;
    slider.max = graph.schedule.length - 1;
    slider.value = 0;
    slider.disabled = false;
    document.getElementById('slider-max-label').textContent = `Step ${graph.schedule.length - 1}`;

    // Buttons
    document.getElementById('btn-play').disabled = false;
    document.getElementById('btn-restart').disabled = false;

    document.getElementById('empty-state').style.display = 'none';

    currentStep = 0;
    drawGraph(0);
    toast(`Loaded: ${graph.name}`);
}

// ════════════════════════════════════════════════════════════════
//  Draw graph via Plotly:
//  this is nice one!
//  - It sets the values of W and H according to available screen
//  - Declare a couple of functions to normalize the scale separated by a const padding
//  - Gets the nodes, which all have an id assigned, from graph data into an object
//  - Configures the style of the edges (edge traces)
//  - Confgures the style of the nodes (node traces) and adds interactivity to them
//  - It would include a trailing: how the nodes navigate the traces (only last segment of the trail)
//  - It returns the lines and the nodes, configurated
//  - To be understood by Plotly, the resulting data structure must be a flattenned list
//  - Then, it goes by setting the layout
//  - The transition of the viz when data is modified is also configured there
//  - There are a couple of additional configurations of more general scope after the layout is configured
//  - Finally, the Plotly instance is filled with the data to be reactive and the Slider is also updated
// ════════════════════════════════════════════════════════════════
function drawGraph(step) {
    const wrap = document.getElementById('graph-wrap');
    const W = wrap.clientWidth;
    const H = wrap.clientHeight - 0; // controls are outside

    const PAD = 0.1; // normalized coord padding
    const scaleX = x => PAD + x * (1 - 2 * PAD);
    const scaleY = y => PAD + y * (1 - 2 * PAD);

    // getting nodes
    const nodeById = Object.fromEntries(graph.nodes.map(n => [n.id, n]));

    // ── Edge traces ──
    const edgeTraces = graph.edges.map(e => {
        const a = nodeById[e.from], b = nodeById[e.to];
        return {
            type: 'scatter', mode: 'lines',
            x: [scaleX(a.x), scaleX(b.x)],
            y: [scaleY(a.y), scaleY(b.y)],
            line: { color: '#1e2535', width: 2 },
            hoverinfo: 'none',
            showlegend: false,
        };
    });

    // ── Node trace ──
    const nodeTrace = {
        type: 'scatter', mode: 'markers+text',
        x: graph.nodes.map(n => scaleX(n.x)),
        y: graph.nodes.map(n => scaleY(n.y)),
        text: graph.nodes.map(n => n.label),
        textposition: 'top center',
        textfont: { family: 'Space Mono', size: 4, color: '#c8d0e0' },
        marker: {
            size: 18,
            //color: '#10141c',
            color: graph.nodes.map(n => n.color),
            line: { color: '#7b61ff', width: 2 },
            symbol: 'circle',
        },
        hovertemplate: graph.nodes.map(n => `Node ${n.label}<extra></extra>`),
        showlegend: false,
    };

    // ── Agent traces (current positions) ──
    const frame = graph.schedule[step];
    const agentTraces = graph.agents.map(agent => {
        const nodeId = frame[String(agent.id)];
        const node = nodeById[nodeId];

        // trail: last few steps
        const trailLen = 4;
        const trailXs = [], trailYs = [], trailOpacities = [];
        for (let i = Math.max(0, step - trailLen); i <= step; i++) {
            const nid = graph.schedule[i][String(agent.id)];
            const nd = nodeById[nid];
            trailXs.push(scaleX(nd.x));
            trailYs.push(scaleY(nd.y));
        }

        return [
            // trail line
            {
                type: 'scatter', mode: 'lines',
                x: trailXs, y: trailYs,
                line: { color: agent.color, width: 1.5, dash: 'dot' },
                opacity: 0.35,
                hoverinfo: 'none',
                showlegend: false,
            },
            // agent dot
            {
                type: 'scatter', mode: 'markers+text',
                x: [scaleX(node.x)],
                y: [scaleY(node.y)],
                text: [`${agent.name.split(' ')[1]?.[0] ?? agent.name[0]}`],
                textposition: 'middle center',
                textfont: { family: 'Syne', size: 10, color: '#000' },
                marker: {
                    size: 26,
                    color: agent.color,
                    symbol: 'circle',
                    line: { color: '#000', width: 1 },
                },
                hovertemplate: `${agent.name}<br>Node: ${node.label}<extra></extra>`,
                showlegend: false,
            }
        ];
    }).flat();

    const layout = {
        xaxis: { range: [0, 1], showgrid: false, zeroline: false, visible: false },
        yaxis: { range: [0, 1], showgrid: false, zeroline: false, visible: false, scaleanchor: 'x' },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        margin: { l: 20, r: 40, t: 40, b: 40 },
        hoverlabel: {
            bgcolor: '#10141c',
            bordercolor: '#1e2535',
            font: { family: 'Space Mono', size: 11, color: '#c8d0e0' }
        },
        transition: { duration: Math.round(DELAY * 0.6), easing: 'cubic-in-out' },
    };

    const config = {
        displayModeBar: false,
        responsive: true,
    };

    Plotly.react('plotly-graph', [...edgeTraces, nodeTrace, ...agentTraces], layout, config);
    updateSlider(step);
}

// ════════════════════════════════════════════════════════════════
//  Animation:
//  - Check for graph, if any, show the pause icon and run the tick function
//
//  the tick function:
//  - use the schedule data to run the steps
//  - includes a stopAnimation function
//  - when stopped, it shows the play icon
//  - otherwise, it continues the tick by re-running the drawGraph function with values associated to that tick
//  - use a timeout to set the length of the tick
//
//  Helpers: the stopAnimation, the togglePlay, and the reStart functions
// ════════════════════════════════════════════════════════════════
function startAnimation() {
    if (!graph) return;
    playing = true;
    document.getElementById('btn-play').textContent = '⏸';
    tick();
}

function tick() {
    if (!playing) return;
    if (currentStep >= graph.schedule.length - 1) {
        stopAnimation();
        document.getElementById('btn-play').textContent = '▶';
        return;
    }
    currentStep++;
    drawGraph(currentStep);
    animTimer = setTimeout(tick, DELAY);
}

function stopAnimation() {
    playing = false;
    clearTimeout(animTimer);
    document.getElementById('btn-play').textContent = '▶';
}

function togglePlay() {
    if (!graph) return;
    playing ? stopAnimation() : startAnimation();
}

function restart() {
    if (!graph) return;
    stopAnimation();
    currentStep = 0;
    drawGraph(0);
}

// ════════════════════════════════════════════════════════════════
//  UI helpers:
//  
//  updateSlider:
//  - receives steps to update its position
//
//  setStatus:
//  - a minimal error handler focused on CSS classes updating
//
//  toast:
//  - a minimal info handler based on the setStatus status, with timeout
// ════════════════════════════════════════════════════════════════
function updateSlider(step) {
    const slider = document.getElementById('frame-slider');
    slider.value = step;
    document.getElementById('frame-counter').textContent =
        `Step ${step} / ${graph.schedule.length - 1}`;
}

function setStatus(field, value, isErr = false, isOk = false) {
    const el = document.getElementById(`s-${field}`);
    el.textContent = value;
    el.className = 'val' + (isErr ? ' err' : isOk ? ' ok' : '');
}

function toast(msg, isErr = false) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'show' + (isErr ? ' err' : '');
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.className = ''; }, 2800);
}

// ════════════════════════════════════════════════════════════════
//  Event listeners
//  eventhandlers to assing buttons and event listeners to animation helpers and the slider
// ════════════════════════════════════════════════════════════════
document.getElementById('btn-play').onclick = togglePlay;
document.getElementById('btn-restart').onclick = restart;

document.getElementById('frame-slider').addEventListener('input', e => {
    stopAnimation();
    currentStep = parseInt(e.target.value);
    drawGraph(currentStep);
});