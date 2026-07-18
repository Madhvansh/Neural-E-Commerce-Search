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
for (const contract of [
  'id="search-form"',
  'id="model-status"',
  'id="results"',
  'id="error-message"',
  'src="./assets/lab.js"',
]) {
  assert.ok(html.includes(contract), `lab.html is missing ${contract}`);
}

console.log("Browser lab ranking and DOM contract smoke passed.");
