export function dot(left, right) {
  if (left.length !== right.length) {
    throw new Error("Embedding dimensions must match");
  }

  let total = 0;
  for (let index = 0; index < left.length; index += 1) {
    total += left[index] * right[index];
  }
  return total;
}

export function rankCatalog(catalog, catalogEmbeddings, queryEmbedding, topK) {
  if (catalog.length !== catalogEmbeddings.length) {
    throw new Error("Every catalogue item must have one embedding");
  }
  if (!Number.isInteger(topK) || topK < 1) {
    throw new Error("topK must be a positive integer");
  }

  return catalog
    .map((product, index) => ({
      product,
      score: dot(queryEmbedding, catalogEmbeddings[index]),
    }))
    .sort((left, right) => right.score - left.score)
    .slice(0, topK);
}
