const assert = require("node:assert/strict");

global.window = {};
require("../geometry-client.js");

function response(status, contentType, body) {
    return {
        ok: status >= 200 && status < 300,
        status,
        headers: { get: () => contentType },
        text: async () => body
    };
}

async function main() {
    global.fetch = async () => response(404, "text/html;charset=utf-8", "<!DOCTYPE html><h1>Not found</h1>");
    await assert.rejects(
        window.requestMolecularGeometry({ iupacName: "ethanol" }),
        error => error.message.includes("HTTP 404") &&
            error.message.includes("text/html") &&
            !error.message.includes("<!DOCTYPE")
    );

    global.fetch = async () => response(
        422,
        "application/json; charset=utf-8",
        JSON.stringify({ error: "Unsupported name." })
    );
    await assert.rejects(
        window.requestMolecularGeometry({ iupacName: "unknown" }),
        /Unsupported name\./
    );

    global.fetch = async () => response(200, "application/json", "null");
    await assert.rejects(
        window.requestMolecularGeometry({ iupacName: "ethanol" }),
        /invalid response shape/
    );

    const structure = {
        atoms: [],
        bonds: [],
        metadata: { canonicalSmiles: "CCO" }
    };
    global.fetch = async () => response(200, "application/json", JSON.stringify(structure));
    assert.deepEqual(
        await window.requestMolecularGeometry({ iupacName: "ethanol" }),
        structure
    );
}

main().then(
    () => console.log("Geometry client response checks passed."),
    error => {
        console.error(error);
        process.exitCode = 1;
    }
);
