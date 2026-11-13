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
        compoundCounts[role] += 1;
        if (await list.count() !== compoundCounts[role]) {
            throw new Error(`Could not add ${name} as ${role}: ${await page.locator("#entry-status").innerText()}`);
        }
        console.log(`Added ${name} as ${role}: ${await list.first().locator("h3").innerText()}`);
    }

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
    await page.locator("#results-content .route-network[data-convergent='true']").waitFor({ timeout: 90000 });
    assert.match(await page.locator("#results-content .route-network").innerText(), /convergent reaction/i, "two independent feedstocks should visibly converge in the route graph");
    assert.equal(await page.locator("#results-content .result-step").count(), 3, "Kolbe–Schmitt route should render its three transformations");
    await page.screenshot({ path: `${outputDir}/${runLabel}-convergent-route.png`, fullPage: true });

    const responsive = [];
    for (const width of [375, 724, 1280]) {
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
        convergentRoute: "phenol + carbon dioxide → salicylic acid through three steps",
        unsupportedRoute: "benzene → bromobenzene",
        invalidName: "rejected without adding an inventory item",
        largeName: "paclitaxel, formula C47H51NO14",
        responsive,
        consoleErrors,
        failedRequests,
        screenshots: [`${outputDir}/${runLabel}-supported-route.png`, `${outputDir}/${runLabel}-convergent-route.png`, `${outputDir}/${runLabel}-unsupported-route.png`]
    }, null, 2));
} finally {
    await browser.close();
}
