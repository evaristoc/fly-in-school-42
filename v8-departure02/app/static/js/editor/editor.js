const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
let image = new Image();
const model = {
    nodes: [],
    edges: [],
    selectedNode: null,
    edgeMode: false,
    pendingEdgeNode: null,
    nextNodeId: 0,
    nextEdgeId: 0,
    showEdgeTable: false,
    edgeTableNode: null,
    selectedEdge: null
};

// Load PNG
document.getElementById("imageLoader")
    .addEventListener("change", function (event) {
        let file = event.target.files[0];
        console.log(file);
        let reader = new FileReader();
        reader.onload = function (e) {
            image.onload = function () {
                canvas.width = image.width;
                canvas.height = image.height;
                draw();
            };
            image.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });

function addEdge(nodeA, nodeB) {
    if (nodeA === nodeB) {
        console.log("Cannot connect node to itself");
        return;
    }
    if (edgeExists(nodeA, nodeB)) {
        console.log("Edge already exists");
        return;
    }
    const edge = {
        uid: model.nextEdgeId++,
        nodeA: nodeA.name,
        nodeB: nodeB.name,
        attributes: {
            max_link_capacity: 1
        }
    };
    model.edges.push(edge);
    console.log("New edge:", edge);
}

function edgeExists(nodeA, nodeB) {
    return model.edges.some(edge => {
        return (
            edge.nodeA === nodeA.name &&
            edge.nodeB === nodeB.name
        )
            ||
            (
                edge.nodeA === nodeB.name &&
                edge.nodeB === nodeA.name
            );
    });
}

// Click creates node
canvas.addEventListener("click", function (event) {
    let rect = canvas.getBoundingClientRect();
    let x = Math.round(event.clientX - rect.left);
    let y = Math.round(event.clientY - rect.top);
    // Check if clicking an existing node
    let clickedNode = findNodeAt(x, y);
    if (model.edgeMode) {
        if (clickedNode) {
            if (!model.pendingEdgeNode) {
                model.pendingEdgeNode = clickedNode;
                console.log(
                    "First edge node:",
                    clickedNode.name
                );
            } else {
                addEdge(
                    model.pendingEdgeNode,
                    clickedNode
                );
                model.pendingEdgeNode = null;
            }
        }
        draw();
        return;
    }
    if (clickedNode) {
        if (model.selectedNode == clickedNode) {
            clearSelection();
            return;
        }
        model.selectedNode = clickedNode;
        updatePropertiesPanel();
    } else {
        let id = model.nextNodeId++;
        let node = {
            uid: id,
            name: "waypoint" + id,
            x: x,
            y: y,
            category: "hub",
            attributes: {
                color: "blue",
                max_drones: 1
            }
        };
        model.nodes.push(node);
    }
    draw();
});

canvas.addEventListener(
    "contextmenu",
    function (event) {
        event.preventDefault();
        let rect = canvas.getBoundingClientRect();
        let x = Math.round(event.clientX - rect.left);
        let y = Math.round(event.clientY - rect.top);
        let node = findNodeAt(x, y);
        if (!node) {
            return;
        }
        if (model.edgeTableNode === node) {
            model.edgeTableNode = null;
            hideEdgeTable();
        } else {
            model.edgeTableNode = node;
            showEdgeTable(node);
        }
    }
);

// Draw everything
function draw() {
    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );
    if (image.src)
        ctx.drawImage(image, 0, 0);
    for (let edge of model.edges) {
        let nodeA =
            model.nodes.find(
                n => n.name === edge.nodeA
            );
        let nodeB =
            model.nodes.find(
                n => n.name === edge.nodeB
            );
        if (!nodeA || !nodeB)
            continue;
        ctx.beginPath();
        ctx.moveTo(
            nodeA.x,
            nodeA.y
        );
        ctx.lineTo(
            nodeB.x,
            nodeB.y
        );
        ctx.strokeStyle = "black";
        ctx.lineWidth = 2;
        ctx.stroke();
    }
    for (let node of model.nodes) {
        // circle
        ctx.beginPath();
        ctx.arc(
            node.x,
            node.y,
            8,
            0,
            Math.PI * 2
        );
        ctx.fillStyle =
            node === model.selectedNode
                ? "orange"
                : node.attributes.color;
        ctx.fill();
        // label
        ctx.fillStyle = "black";
        ctx.font = "14px Arial";
        ctx.fillText(
            node.name,
            node.x + 10,
            node.y
        );
        ctx.fillText(
            "(" + node.x + "," + node.y + ")",
            node.x + 10,
            node.y + 15
        );
    }
}

// Export your format
// function exportConfig() {
//     let text = "";
//     text += "nb_drones: 0\n\n";
//     for (let node of model.nodes) {
//         text +=
//             `${node.category}: ${node.name} ${node.x} ${node.y} [color=${node.attributes.color} max_drones=${node.attributes.max_drones}]\n`;
//     }
//     console.log(text);
//     let blob =
//         new Blob(
//             [text],
//             { type: "text/plain" }
//         );
//     let link =
//         document.createElement("a");
//     link.href =
//         URL.createObjectURL(blob);
//     link.download =
//         "map.cfg";
//     link.click();
// }
function exportConfig() {
    let text = "";
    text += "nb_drones: 0\n\n";
    for (let node of model.nodes) {
        text +=
            `${node.category}: ${node.name} ${node.x} ${node.y} ` +
            `[color=${node.attributes.color} max_drones=${node.attributes.max_drones}]\n`;
    }
    console.log(text);
    let blob =
        new Blob(
            [text],
            { type: "text/plain" }
        );
    let link =
        document.createElement("a");
    link.href =
        URL.createObjectURL(blob);
    link.download =
        "map.cfg";
    link.click();
}

function findNodeAt(x, y) {
    for (let node of model.nodes) {
        let distance =
            Math.sqrt(
                (node.x - x) ** 2 +
                (node.y - y) ** 2
            );
        if (distance < 10) {
            return node;
        }
    }
    return null;
}

function updatePropertiesPanel() {
    let panel =
        document.getElementById("properties");
    if (!model.selectedNode) {
        panel.innerHTML =
            "<h3>Node Properties</h3><p>Select a node</p>";
        return;
    }
    let node = model.selectedNode;
    // if (node) {
    //     if (model.selectedNode === clickedNode) {
    //         clearSelection();
    //         return;
    //     }
    // }
    // panel.innerHTML = `
    //     <h3>Node Properties</h3>
    //     <p>Name: ${node.name}</p>
    //     <p>Category: ${node.category}</p>
    //     <p>Coordinates:
    //     ${node.x}, ${node.y}</p>
    //     <p>Max drones:
    //     ${node.attributes.max_drones}</p>  
    // `;
    panel.innerHTML = `
    <h3>Node Properties</h3>
    <label>
        Name:
        <input id="nodeName" value="${node.name}">
    </label>
    <br><br>
    <label>
        Category:
        <select id="nodeCategory">
            <option value="hub" ${node.category === "hub" ? "selected" : ""}>
                hub
            </option>
            <option value="start_hub" ${node.category === "start_hub" ? "selected" : ""}>
                start_hub
            </option>
            <option value="end_hub" ${node.category === "end_hub" ? "selected" : ""}>
                end_hub
            </option>
        </select>
    </label>
    <br><br>
    <label>
        Max drones:
        <input 
            id="nodeMaxDrones"
            type="number"
            min="0"
            value="${node.attributes.max_drones}">
    </label>
    <br><br>
    <p>
        Coordinates:
        ${node.x}, ${node.y}
    </p>
`;
    document
        .getElementById("nodeName")
        .addEventListener("change", function () {
            node.name = this.value;
            draw();
        });

    document
        .getElementById("nodeCategory")
        .addEventListener("change", function () {
            node.category = this.value;
            draw();
        });

    document
        .getElementById("nodeMaxDrones")
        .addEventListener("change", function (event) {
            console.log("Before update:", node, event.target.value);
            node.attributes.max_drones = Number(this.value);
            console.log("After update:", node);
            draw();
        });

}

function clearSelection() {
    model.selectedNode = null;
    let panel = document.getElementById("properties");
    panel.innerHTML = `
        <h3>Node Properties</h3>
        <p>Select a node</p>
    `;
    draw();
}

// document
//     .getElementById("edgeModeButton")
//     .addEventListener("click", function () {
//         model.edgeMode = !model.edgeMode;
//         model.pendingEdgeNode = null;
//         console.log(
//             "Edge mode:",
//             model.edgeMode
//         );
//     });

document
    .getElementById("edgeModeButton")
    .addEventListener("click", function () {
        model.edgeMode = !model.edgeMode;
        model.pendingEdgeNode = null;
        console.log(
            "Edge mode:",
            model.edgeMode
        );
    });

function showEdgeTable(node) {
    const table =
        document.getElementById("edgeTable");
    table.innerHTML = "";
    for (let edge of model.edges) {
        // let nodeA =
        //     model.nodes.find(
        //         n => node.name === n.name
        //     );
        // let nodeB =
        //     model.nodes.find(
        //         n => node.name === n.name
        //     );
        let row =
            document.createElement("tr");
        if (edge.nodeA == node.name || edge.nodeB == node.name) {
            row.innerHTML = `
                <td>${edge.nodeA}</td>
                <td>${edge.nodeB}</td>
                <td>${edge.attributes.max_link_capacity}</td>
            `
        }
        row.addEventListener(
            "click",
            function () {
                selectEdge(edge);
            }
        );
        table.appendChild(row);
    }
}

function hideEdgeTable() {
    const table = document.getElementById("edgeTable");
    table.innerHTML = "";
}

function selectEdge(edge) {
    model.selectedEdge = edge;
    console.log(
        "Selected edge:",
        edge
    );
    draw();
}