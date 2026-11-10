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

assert.match(page, /<input id="show-inspector" type="checkbox"> 3D inspector/);
assert.match(page, /id="viewer-panel"[^>]*hidden/);
assert.match(page, /class="layout inspector-hidden" id="main-layout"/);
assert.match(page, /class="workspace-input"/);
assert.match(page, /class="workspace-results" id="results"/);
assert.match(page, /id="close-inspector-button"/);
assert.match(page, /function setInspectorVisible\(visible\)[\s\S]*?viewer-panel"\)\.hidden = !visible/);
assert.match(page, /function inspectCompound\(compound\)[\s\S]*?setInspectorVisible\(true\)/);
assert.match(page, /show-inspector"\)\.addEventListener\("change"[\s\S]*?setInspectorVisible\(event\.target\.checked\)/);

assert.match(page, /<input id="show-reaction-text" type="checkbox"> Show reaction explanations/);
assert.match(page, /querySelectorAll\("\.reaction-explanation"\)\.forEach\(description => \{/);
assert.match(page, /description\.hidden = !event\.target\.checked/);
assert.match(page, /async function loadReactionCatalogue\(\)/);
assert.match(page, /fetch\("\/api\/reaction_planner", \{ method: "GET" \}\)/);
assert.match(page, /Object\.fromEntries\(selectedReagents\)/);
assert.match(page, /step\.evidence\.references\.forEach\(reference/);
assert.match(page, /step\.conditionsUsed\.length/);
assert.match(page, /depictionSvg/);
assert.match(page, /structureImage\(compound\.depictionSvg/);
assert.match(page, /\.reaction-line-scroll\s*\{[^}]*overflow-x:\s*auto/);
assert.match(page, /lineScroll\.append\(line\)/);
assert.match(page, /return fallbackFormula \|\| "IUPAC name unavailable for this structure"/);
assert.match(page, /IUPAC name unavailable; molecular formula shown/);
assert.match(page, /@media \(max-width: 900px\)[\s\S]*?\.reaction-line \{[^}]*flex-direction: column/);
assert.match(page, /\.reaction-arrow \{[^}]*flex-direction: row/);
assert.doesNotMatch(page, /reaction-arrow-line\s*\{\s*width:\s*auto;\s*transform:\s*rotate/);
assert.match(page, /id="depiction-modal"/);
assert.match(page, /showDepiction\(svg, name\)/);
assert.match(page, /IUPAC name unavailable for this structure/);
assert.doesNotMatch(page, /SmilesDrawer|smiles-drawer/);
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
