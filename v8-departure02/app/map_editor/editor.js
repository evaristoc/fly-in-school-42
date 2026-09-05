const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
let image = new Image();
let nodes = [];
let nodeCounter = 0;

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

// Click creates node
canvas.addEventListener("click", function (event) {
    let rect = canvas.getBoundingClientRect();
    let x = Math.round(event.clientX - rect.left);
    let y = Math.round(event.clientY - rect.top);
    let node = {
        id: nodeCounter,
        name: "waypoint" + nodeCounter,
        x: x,
        y: y,
        type: "hub"
    };
    nodes.push(node);
    nodeCounter++;
    draw();
});

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
    for (let node of nodes) {
        // circle
        ctx.beginPath();
        ctx.arc(
            node.x,
            node.y,
            8,
            0,
            Math.PI * 2
        );
        ctx.fillStyle = "blue";
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
function exportConfig() {
    let text = "";
    text += "nb_drones: 0\n\n";
    for (let node of nodes) {
        text +=
            `${node.type}: ${node.name} ${node.x} ${node.y} [color=blue]\n`;
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