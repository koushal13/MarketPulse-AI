#!/usr/bin/env python3
"""Test the stock search functionality"""

from stock_search import search_stocks

# Test searches
test_queries = ['Tata', 'Apple', 'Microsoft', 'Reliance', 'TD Bank']

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Searching for: '{query}'")
    print('='*60)
    
    results = search_stocks(query, limit=20)
    
    if results:
        print(f"Found {len(results)} results:\n")
        for i, r in enumerate(results[:10], 1):
            symbol = r.get('symbol', 'N/A')
            name = r.get('name', 'N/A')
            exchange = r.get('exchange', 'N/A')
            print(f"{i:2}. {symbol:15} - {name[:45]:45} ({exchange})")
    else:
        print("❌ No results found!")
