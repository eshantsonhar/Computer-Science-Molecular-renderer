const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const page = fs.readFileSync(
    path.join(__dirname, "..", "pages", "organic_reactions.html"),
    "utf8"
);
const editor = fs.readFileSync(
    path.join(__dirname, "..", "molecule_editor.html"),
    "utf8"
);

assert.match(page, /<input id="show-inspector" type="checkbox"> Show 3D Structure Inspector/);
assert.match(page, /id="viewer-panel"[^>]*hidden/);
assert.match(page, /class="layout inspector-hidden" id="main-layout"/);
assert.match(page, /function setInspectorVisible\(visible\)[\s\S]*?viewer-panel"\)\.hidden = !visible/);
assert.match(page, /function inspectCompound\(compound\)[\s\S]*?setInspectorVisible\(true\)/);
assert.match(page, /show-inspector"\)\.addEventListener\("change"[\s\S]*?setInspectorVisible\(event\.target\.checked\)/);

assert.match(page, /<input id="show-reaction-text" type="checkbox"> Show reaction text/);
assert.match(page, /description\.hidden = !event\.target\.checked/);
assert.match(page, /canvas\.dataset\.scheme = "true"/);
assert.match(page, /BACKGROUND: "#ffffff"/);
assert.match(page, /Verified IUPAC name unavailable/);
assert.match(page, /Identify IUPAC &amp; Add/);
assert.match(editor, /Clear Drawing/);

for (const removedText of [
    "Evidence-limited planner - not a general synthesis predictor",
    "The initial rule set contains two exact acetyl chloride examples",
    "The current drawing editor records atom and bond topology",
    "Drag to rotate; scroll or pinch to zoom",
    "Organic atom donors, including ethanol, must be present"
]) {
    assert.equal(page.includes(removedText), false, `Unexpected visible copy: ${removedText}`);
}

console.log("Organic Reactions UI source checks passed.");
