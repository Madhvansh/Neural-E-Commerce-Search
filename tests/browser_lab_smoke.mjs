import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import { rankCatalog } from "../docs/assets/lab-core.mjs";

const catalog = [{ id: "mouse" }, { id: "charger" }, { id: "headphones" }];
const embeddings = [
  [1, 0],
  [0, 1],
  [0.8, 0.2],
];

const ranked = rankCatalog(catalog, embeddings, [1, 0], 2);
assert.deepEqual(
  ranked.map((item) => item.product.id),
  ["mouse", "headphones"],
);
assert.throws(
  () => rankCatalog(catalog, embeddings.slice(1), [1, 0], 2),
  /one embedding/,
);

const html = await readFile(new URL("../docs/lab.html", import.meta.url), "utf8");
const labScript = await readFile(new URL("../docs/assets/lab.js", import.meta.url), "utf8");
const remixGuide = await readFile(new URL("../docs/FORK_THE_LAB.md", import.meta.url), "utf8");
const publicCatalog = JSON.parse(
  await readFile(new URL("../docs/catalog.json", import.meta.url), "utf8"),
);
for (const contract of [
  'id="search-form"',
  'id="model-status"',
  'id="results"',
  'id="error-message"',
  'id="result-actions"',
  'id="share-search"',
  'src="./assets/lab.js"',
]) {
  assert.ok(html.includes(contract), `lab.html is missing ${contract}`);
}

assert.ok(labScript.includes('fetch("./catalog.json"'), "lab must load the remixable catalogue");
assert.ok(labScript.includes("requestIdleCallback"), "lab must prewarm on eligible connections");
assert.ok(remixGuide.includes("docs/catalog.json"), "remix guide must identify the catalogue file");
assert.equal(publicCatalog.length, 20, "public demo catalogue should contain 20 products");
for (const product of publicCatalog) {
  for (const field of ["id", "title", "category", "description", "tags"]) {
    assert.ok(product[field], `catalogue item is missing ${field}`);
  }
}

console.log("Browser lab ranking and DOM contract smoke passed.");
