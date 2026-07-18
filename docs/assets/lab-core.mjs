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

export function validateCatalog(catalog) {
  if (!Array.isArray(catalog) || catalog.length === 0) {
    throw new Error("Catalogue must be a non-empty JSON array");
  }

  const seenIds = new Set();
  const textFields = ["id", "title", "category", "description"];
  catalog.forEach((product, index) => {
    if (!product || typeof product !== "object" || Array.isArray(product)) {
      throw new Error(`Catalogue item ${index + 1} must be an object`);
    }
    for (const field of textFields) {
      if (typeof product[field] !== "string" || !product[field].trim()) {
        throw new Error(`Catalogue item ${index + 1} needs a non-empty ${field} string`);
      }
    }
    if (seenIds.has(product.id)) {
      throw new Error(`Catalogue id ${product.id} appears more than once`);
    }
    seenIds.add(product.id);
    if (
      !Array.isArray(product.tags) ||
      product.tags.length === 0 ||
      product.tags.some((tag) => typeof tag !== "string" || !tag.trim())
    ) {
      throw new Error(`Catalogue item ${index + 1} needs a non-empty array of tag strings`);
    }
  });
  return catalog;
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
