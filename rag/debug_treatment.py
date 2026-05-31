from retrieval.hybrid_search import hybrid_search

test_queries = [
    "uproot infected cassava plants",
    "whitefly control cassava", 
    "certified disease-free cuttings",
    "cypermethrin cassava"
]

print("=" * 60)
print("SEARCHING FOR TREATMENT PDF CONTENT")
print("=" * 60)

for query in test_queries:
    print(f"\nQuery: '{query}'")
    results = hybrid_search.search(query, top_k=5)
    
    found = False
    for r in results:
        if "cassava_mosaic_treatment" in r['filename']:
            print(f"  ✅ FOUND in treatment PDF! Score: {r['hybrid_score']:.4f}")
            print(f"     Text: {r['text'][:150]}...")
            found = True
        else:
            print(f"  ❌ From: {r['filename']} (score: {r['hybrid_score']:.4f})")
    
    if not found:
        print("  ❌ Treatment PDF NOT found in top results")