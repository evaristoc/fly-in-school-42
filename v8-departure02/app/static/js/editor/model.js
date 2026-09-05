const model = {
    nodes: [],
    edges: [],
    selectedNode: null,
    edgeMode: false,
    nextNodeId: 1
};

const nodeSchema = {

    categories: [
        "start_hub",
        "hub",
        "end_hub"
    ],
    attributes: {
        color: {
            default: "blue"
        },
        max_drones: {
            default: 1
        }
    }
};


const edgeSchema = {
    attributes: {
        max_link_capacity: {
            default: 1
        }
    }
};

// function addEdge(nodeA, nodeB) {
//     if (nodeA === nodeB) {
//         console.log("Cannot connect node to itself");
//         return;
//     }
//     if (edgeExists(nodeA, nodeB)) {
//         console.log("Edge already exists");
//         return;
//     }
//     let edge = {
//         uid: model.nextEdgeId++,
//         nodeA: nodeA.name,
//         nodeB: nodeB.name,
//         attributes: {
//             max_link_capacity: 1
//         }
//     };
//     model.edges.push(edge);
//     console.log("Created edge", edge);
// }

