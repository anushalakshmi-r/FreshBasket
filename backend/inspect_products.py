import csv

rows = list(csv.DictReader(open('catalog/data/products.csv', encoding='utf-8-sig')))
print(f"Total: {len(rows)}")

with open('products_summary.txt', 'w', encoding='utf-8') as f:
    for r in rows:
        f.write(f"{r['sku']}\t{r['name']}\t{r['category']}\t{r['subcategory']}\t{r['image_url']}\n")

print("Written products_summary.txt")
