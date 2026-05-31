# # from vector_store.chroma_store import vector_db

# # # Get all chunks
# # results = vector_db.table.get(include=['documents', 'metadatas'])

# # print(f"Total chunks: {len(results['documents'])}")
# # print(f"First document type: {type(results['documents'][0])}")
# # print(f"First document value: {results['documents'][0]}")
# # print(f"First metadata: {results['metadatas'][0]}")


# # Create file: check_pdf.py
# from vector_store.chroma_store import vector_db

# # Get all unique filenames
# results = vector_db.table.get(include=['metadatas'])
# filenames = set()
# for meta in results['metadatas']:
#     filenames.add(meta.get('filename', 'Unknown'))

# print("=" * 50)
# print("PDFs IN DATABASE:")
# print("=" * 50)
# for f in sorted(filenames):
#     print(f"  - {f}")

# print("\n" + "=" * 50)
# print(f"Total vectors: {len(results['metadatas'])}")
# print("=" * 50)

# Create file: debug_treatment.py
from retrieval.hybrid_search import hybrid_search

# Search for exact phrases from the treatment PDF
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