import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";

const baseUrl = (process.env.ATOMVIEW_BASE_URL || "https://atom-view.vercel.app").replace(/\/$/, "");
const runLabel = new URL(baseUrl).hostname.includes("localhost") || new URL(baseUrl).hostname.includes("127.0.0.1") ? "local" : "production";
const edgePath = process.env.EDGE_EXECUTABLE_PATH || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const outputDir = "browser-artifacts";
await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ executablePath: edgePath, headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const consoleErrors = [];
const failedRequests = [];
page.on("pageerror", error => consoleErrors.push(error.message));
page.on("requestfailed", request => failedRequests.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText}`));

try {
    const response = await page.goto(`${baseUrl}/pages/organic_reactions.html`, { waitUntil: "networkidle", timeout: 90000 });
    assert.equal(response?.status(), 200, "organic reactions page should load successfully");
    await page.locator("#compound-form").waitFor();

    const compoundCounts = { starting: 0, target: 0 };
    async function addIupac(name, role) {
        await page.locator("#input-format").selectOption("iupacName");
        await page.locator("#structure-input").fill(name);
        await page.locator(`input[name="compound-role"][value="${role}"]`).check();
        await page.locator("#add-compound-button").click();
        await page.waitForFunction(() => !document.getElementById("add-compound-button").disabled, undefined, { timeout: 120000 });
        const list = page.locator(role === "starting" ? "#starting-list .compound-card" : "#target-list .compound-card");
        const statusText = await page.locator("#entry-status").innerText();
        if (!statusText.includes("merged duplicate")) {
            compoundCounts[role] += 1;
        }
        if (await list.count() !== compoundCounts[role]) {
            throw new Error(`Could not add ${name} as ${role}: ${await page.locator("#entry-status").innerText()}`);
        }
        console.log(`Added ${name} as ${role}: ${await list.last().locator("h3").innerText()}`);
    }

    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    for (const name of ["ethene", "ethane", "ethanol", "ethanoic acid", "benzene", "nitrobenzene", "propan-2-ol", "propanone"]) {
        await addIupac(name, "starting");
    }
    await addIupac("  benzene   ", "starting");
    assert.equal(await page.locator("#starting-list .compound-card").count(), 8, "repeated whitespace and duplicate benzene should merge to one starting-material entry");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage1-name-inputs.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethanol", "starting");
    await addIupac("ethanol", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.getByText(/already present in the supplied starting-material inventory/i).waitFor({ timeout: 90000 });
    assert.equal(await page.locator("#results-content .result-step").count(), 0, "identity route must contain zero reaction steps");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage3-identity-route.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethene", "starting");
    await addIupac("ethane", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /alkene|hydrogenation|ethane/i, "ethene hydrogenation route should expose the reaction and product");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage4-ethene-hydrogenation.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethyne", "starting");
    await addIupac("ethene", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /partial|lindlar|alkyne|ethene/i, "partial alkyne hydrogenation should expose Lindlar reduction and ethene");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage5-partial-alkyne-hydrogenation.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethyne", "starting");
    await addIupac("ethane", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /complete|alkyne|alkane|ethane/i, "complete alkyne hydrogenation should expose the alkane result");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage5-complete-alkyne-hydrogenation.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("benzaldehyde", "starting");
    await addIupac("phenylmethanol", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /aldehyde|hydrogenation|phenylmethanol/i, "benzaldehyde reduction should expose the aldehyde-to-primary-alcohol transformation");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage6-aldehyde-hydrogenation.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethanol", "starting");
    await addIupac("ethanal", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /primary alcohol|aldehyde|TEMPO|NaOCl|ethanal/i, "selective primary-alcohol oxidation should expose aldehyde formation");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage7-primary-alcohol-to-aldehyde.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethanol", "starting");
    await addIupac("ethanoic acid", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /primary alcohol|carboxylic acid|tungstate|hydrogen peroxide|ethanoic acid/i, "primary-alcohol-to-acid oxidation should expose the full oxidation path");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage8-primary-alcohol-to-acid.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("propan-2-ol", "starting");
    await addIupac("propanone", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /secondary alcohol|ketone|propanone|tungstate/i, "secondary-alcohol oxidation should expose ketone formation");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage9-secondary-alcohol-to-ketone.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("benzaldehyde", "starting");
    await addIupac("benzoic acid", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /aldehyde|carboxylic acid|hydrogen peroxide|benzoic acid/i, "aldehyde oxidation should expose benzoic-acid formation");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage10-aldehyde-to-acid.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethanoic acid", "starting");
    await addIupac("ethanol", "starting");
    await addIupac("ethyl ethanoate", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /Fischer|ester|water|ethyl ethanoate|sulfuric/i, "Fischer esterification should expose ester and water coproduct");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage11-fischer-esterification.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethyl benzoate", "starting");
    await addIupac("benzoic acid", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /saponification|carboxylate|benzoic acid|ethanol/i, "ethyl benzoate should follow saponification or a separate neutral-acid work-up");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage12-ester-hydrolysis.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("benzoic acid", "starting");
    await addIupac("benzoyl chloride", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /thionyl|acid chloride|benzoyl chloride|sulfur dioxide|hydrogen chloride/i, "acid activation should expose benzoyl chloride and coproducts");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage13-acid-chloride-formation.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethyl benzoate", "starting");
    await addIupac("benzamide", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.equal(await page.locator("#results-content .result-step").count(), 4, "ethyl benzoate -> benzamide must expose four transformations");
    assert.match(await page.locator("#results-content").innerText(), /saponification|acidification|acid chloride|ammon|benzamide/i, "four-step benzamide route should expose the complete sequence");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage14-benzamide-four-step.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("benzene", "starting");
    await addIupac("nitrobenzene", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /nitration|nitrobenzene|nitric acid|nitro/i, "benzene nitration should expose nitro-group substitution");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage15-benzene-nitration.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("benzene", "starting");
    await addIupac("1-phenylethan-1-one", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /Friedel-Crafts|acetyl|acetophenone|aluminium chloride|acetyl chloride/i, "Friedel-Crafts acylation should expose acetyl substitution");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage16-friedel-crafts-acylation.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("benzene", "starting");
    await addIupac("ethylbenzene", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /Friedel-Crafts|ethyl|ethylbenzene|chloroethane|aluminium chloride/i, "Friedel-Crafts ethylation should expose the ethyl substituent");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage17-friedel-crafts-ethylation.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("phenol", "starting");
    await addIupac("carbon dioxide", "starting");
    await addIupac("2-hydroxybenzoic acid", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.equal(await page.locator("#results-content .result-step").count(), 3, "Kolbe-Schmitt synthesis should expose phenoxide, carboxylation, and acidification");
    assert.match(await page.locator("#results-content").innerText(), /phenoxide|Kolbe|carbox|salicylic|hydroxybenzoic/i, "Kolbe-Schmitt route should expose ortho carboxylation");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage18-kolbe-schmitt.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("ethanal", "starting");
    await addIupac("hydrogen cyanide", "starting");
    await addIupac("ammonia", "starting");
    await addIupac("2-aminopropanoic acid", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.equal(await page.locator("#results-content .result-step").count(), 4, "Strecker route should expose imine, cyanide addition, hydrolysis, and acidification");
    assert.match(await page.locator("#results-content").innerText(), /imine|cyanide|aminonitrile|hydrolysis|acidification|alanine/i, "Strecker route should expose its four transformations");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage19-strecker-alanine.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("butane-1,4-dial", "starting");
    await addIupac("ammonia", "starting");
    await addIupac("1H-pyrrole", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /Paal-Knorr|pyrrole|water|ammonia/i, "Paal-Knorr route should expose ring closure and water coproducts");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage20-paal-knorr-pyrrole.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("benzene", "starting");
    await addIupac("ethene", "starting");
    await addIupac("2-phenylethan-1-ol", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.equal(await page.locator("#results-content .result-step").count(), 4, "benzene + ethene -> 2-phenylethanol should expose four steps");
    assert.match(await page.locator("#results-content").innerText(), /ethylbenzene|styrene|epoxide|2-phenylethanol|phenylethanol/i, "route should expose all side-chain intermediates");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage21-benzene-ethene-phenylethanol.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;
    await addIupac("1-(2-methylpropyl)benzene", "starting");
    await addIupac("2-[4-(2-methylpropyl)phenyl]propanoic acid", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content").innerText(), /ibuprofen|isobutyl|acetyl|carbonyl|para|meta|separat/i, "BHC route should expose separation, hydrogenation, and carbonylation");
    await page.screenshot({ path: `${outputDir}/${runLabel}-stage22-bhc-ibuprofen.png`, fullPage: true });
    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0;
    compoundCounts.target = 0;

    await addIupac("ethanol", "starting");
    await addIupac("ethanoic acid", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .result-step").first().waitFor({ timeout: 90000 });
    const routeText = await page.locator("#results-content").innerText();
    assert.match(routeText, /oxidation|alcohol|carboxylic acid/i, "route should explain the supported oxidation");
    assert.match(routeText, /ethanol|ethanoic acid/i, "route should render input and output species");
    assert.ok(await page.locator("#results-content img.depiction, #results-content svg").count(), "route should render a molecular depiction");
    await page.locator("#results-content .route-network svg[role='img']").waitFor();
    assert.equal(await page.locator("#results-content .route-network").getAttribute("data-convergent"), "false", "single-feedstock oxidation should not be marked convergent");
    await page.locator("#results-content .result-step details summary").click();
    assert.match(await page.locator("#results-content .result-step").innerText(), /provenance|Validation|Evidence class/i);
    await page.screenshot({ path: `${outputDir}/${runLabel}-supported-route.png`, fullPage: true });

    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0; compoundCounts.target = 0;
    await addIupac("phenol", "starting");
    await addIupac("carbon dioxide", "starting");
    await addIupac("2-hydroxybenzoic acid", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .route-network").waitFor({ timeout: 90000 });
    assert.equal(await page.locator("#results-content .route-network").getAttribute("data-convergent"), "false", "using a second feedstock in one reaction is not an independently developed branch");
    assert.doesNotMatch(await page.locator("#results-content .route-network").innerText(), /Step 2 · branch merge/i);
    assert.equal(await page.locator("#results-content .result-step").count(), 3, "Kolbe–Schmitt route should render its three transformations");
    await page.screenshot({ path: `${outputDir}/${runLabel}-kolbe-multifeedstock-route.png`, fullPage: true });

    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0; compoundCounts.target = 0;
    await addIupac("methylbenzene", "starting");
    await addIupac("benzene", "starting");
    await addIupac("N-phenylbenzamide", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.locator("#results-content .route-network[data-convergent='true']").waitFor({ timeout: 90000 });
    assert.equal(await page.locator("#results-content .result-step").count(), 6, "benzanilide should be built by six transformations on two feedstock branches");
    assert.match(await page.locator("#results-content").innerText(), /N-phenylbenzamide|benzanilide/i);
    assert.match(await page.locator("#results-content .route-network").innerText(), /1 branch merge/i);
    assert.equal(await page.locator("#results-content .route-network-scroll").evaluate(el => el.scrollWidth <= el.clientWidth + 1), true, "the branch-and-merge graph should fit without horizontal scrolling");
    await page.screenshot({ path: `${outputDir}/${runLabel}-benzanilide-route.png`, fullPage: true });

    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0; compoundCounts.target = 0;
    await addIupac("1-(2-methylpropyl)benzene", "starting");
    await addIupac("2-[4-(2-methylpropyl)phenyl]propanoic acid", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    const ibuprofenResponsePromise = page.waitForResponse(response => response.url().includes("/api/reaction_planner") && response.request().method() === "POST");
    await page.locator("#plan-button").click();
    const ibuprofenResponse = await ibuprofenResponsePromise;
    assert.equal(ibuprofenResponse.status(), 200, "the named BHC route request should complete successfully");
    await page.waitForFunction(() => !document.getElementById("plan-button").disabled, undefined, { timeout: 90000 });
    await page.screenshot({ path: `${outputDir}/${runLabel}-ibuprofen-debug.png`, fullPage: true });
    assert.equal(await page.locator("#results-content .result-step").count(), 3, `BHC ibuprofen route should have three transformations: ${await page.locator("#results-content").innerText()}`);
    assert.equal(await page.locator("#results-content .result-step").count(), 3, "BHC ibuprofen route should have acetylation, hydrogenation, and carbonylation");
    assert.match(await page.locator("#results-content .result-step").first().innerText(), /Required process operation:.*Separate para-isobutylacetophenone/i, "regioisomer separation must appear before hydrogenation");
    assert.match(await page.locator("#results-content .route-network svg .network-node.reaction title").first().textContent(), /Separate para-isobutylacetophenone from the meta isomer/i, "the route graph should expose the full required separation in its accessible node label");
    await page.screenshot({ path: `${outputDir}/${runLabel}-ibuprofen-route.png`, fullPage: true });

    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0; compoundCounts.target = 0;
    await addIupac("benzene", "starting");
    await addIupac("ethene", "starting");
    assert.equal(await page.locator("#target-list .compound-card").count(), 0, "the requested product must not be inserted as a starting material");
    await addIupac("2-phenylethan-1-ol", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    const phenethylResponsePromise = page.waitForResponse(response => response.url().includes("/api/reaction_planner") && response.request().method() === "POST");
    await page.locator("#plan-button").click();
    const phenethylResponse = await phenethylResponsePromise;
    assert.equal(phenethylResponse.status(), 200, "the benzene + ethene route should complete successfully");
    const phenethylResult = await phenethylResponse.json();
    await page.locator("#results-content .result-step").nth(3).waitFor({ timeout: 90000 });
    assert.deepEqual(phenethylResult.route.map(step => step.reactionId), [
        "benzene-ethene-ethylation",
        "ethylbenzene-dehydrogenation-to-styrene",
        "styrene-epoxidation",
        "styrene-oxide-hydrogenation-to-2-phenylethanol"
    ]);
    assert.equal(phenethylResult.route.at(-1).products.find(product => product.role === "desired product").canonicalSmiles, "OCCc1ccccc1", "the exact primary-alcohol connectivity must be returned");
    assert.match(await page.locator("#results-content").innerText(), /2-phenylethan-1-ol|2-phenylethanol/i);
    await page.locator("#results-content .result-step").last().locator("details summary").click();
    assert.match(await page.locator("#results-content .result-step").last().innerText(), /Product atom provenance|Hydrogen peroxide/i, "the product step should expose atom provenance and the external oxygen source");
    await page.screenshot({ path: `${outputDir}/${runLabel}-phenylethanol-route.png`, fullPage: true });

    const responsive = [];
    for (const width of [375, 724, 1280, 1600]) {
        await page.setViewportSize({ width, height: 900 });
        responsive.push(await page.evaluate(() => ({
            width: window.innerWidth,
            documentWidth: document.documentElement.scrollWidth,
            bodyWidth: document.body.scrollWidth
        })));
    }
    assert.ok(responsive.every(item => item.documentWidth <= item.width + 1), `page should fit mobile/tablet/desktop widths: ${JSON.stringify(responsive)}`);

    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0; compoundCounts.target = 0;
    await addIupac("benzene", "starting");
    await addIupac("bromobenzene", "target");
    await page.locator('input[name="reagent-mode"][value="auto"]').check();
    await page.locator("#plan-button").click();
    await page.waitForFunction(() => !document.getElementById("plan-button").disabled, undefined, { timeout: 90000 });
    assert.equal(await page.locator("#results-content .result-step").count(), 0, "unsupported transformation must not display a route");
    assert.match(await page.locator("#planner-status").innerText(), /no route|not supported|unsupported/i, "unsupported transformation should show a clear status");
    await page.screenshot({ path: `${outputDir}/${runLabel}-unsupported-route.png`, fullPage: true });

    await page.reload({ waitUntil: "networkidle" });
    compoundCounts.starting = 0; compoundCounts.target = 0;
    await page.locator("#structure-input").fill("not a valid IUPAC molecule xyz 12345");
    await page.locator("#add-compound-button").click();
    await page.waitForFunction(() => !document.getElementById("add-compound-button").disabled, undefined, { timeout: 90000 });
    assert.equal(await page.locator("#starting-list .compound-card").count(), 0, "invalid name must not be added to inventory");
    assert.match(await page.locator("#entry-status").innerText(), /failed|could not|invalid|parse/i, "invalid name should report a parse/validation error");

    const paclitaxelName = "[(1S,2S,3R,4S,7R,9S,10S,12R,15S)-4,12-diacetyloxy-15-[(2R,3S)-3-benzamido-2-hydroxy-3-phenylpropanoyl]oxy-1,9-dihydroxy-10,14,17,17-tetramethyl-11-oxo-6-oxatetracyclo[11.3.1.03,10.04,7]heptadec-13-en-2-yl] benzoate";
    await addIupac(paclitaxelName, "target");
    assert.match(await page.locator("#target-list .compound-card").innerText(), /C47H51NO14/, "large stereochemical IUPAC name should render the expected formula");

    assert.deepEqual(consoleErrors, [], `browser should have no uncaught page errors: ${consoleErrors.join(" | ")}`);
    assert.deepEqual(failedRequests, [], `browser should have no failed network requests: ${failedRequests.join(" | ")}`);
    console.log(JSON.stringify({
        result: "passed",
        browser: "Microsoft Edge via Playwright Chromium driver",
        baseUrl,
        pageStatus: response.status(),
        supportedRoute: "ethanol → ethanoic acid with a route dependency graph",
        multifeedstockRoute: "phenol + carbon dioxide → salicylic acid through three steps (the CO2 branch is not represented as independently transformed)",
        benzanilideRoute: "methylbenzene + benzene → N-phenylbenzamide with six transformations and an explicit network merge",
        ibuprofenRoute: "isobutylbenzene → ibuprofen through the BHC sequence with mandatory para/meta separation",
        phenylethanolRoute: "benzene + ethene → 2-phenylethan-1-ol through ethylbenzene, styrene, and styrene oxide",
        unsupportedRoute: "benzene → bromobenzene",
        invalidName: "rejected without adding an inventory item",
        largeName: "paclitaxel, formula C47H51NO14",
        responsive,
        consoleErrors,
        failedRequests,
        screenshots: [`${outputDir}/${runLabel}-supported-route.png`, `${outputDir}/${runLabel}-kolbe-multifeedstock-route.png`, `${outputDir}/${runLabel}-benzanilide-route.png`, `${outputDir}/${runLabel}-ibuprofen-route.png`, `${outputDir}/${runLabel}-phenylethanol-route.png`, `${outputDir}/${runLabel}-unsupported-route.png`]
    }, null, 2));
} finally {
    await browser.close();
}
