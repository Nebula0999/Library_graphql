"""
add_books.py

Usage:
  - Add a single book via CLI args:
      python add_books.py --title "Title" --author "Author" --published-date 2021-01-01 --isbn 1234567890123 --pages 200 --language English [--cover-image URL]

  - Import from CSV (headers: title,author,published_date,isbn_number,pages,language,cover_image)
      python add_books.py --csv books.csv

Notes:
 - Sends GraphQL mutation to http://127.0.0.1:8000/graphql/ by default. Use --url to change.
 - Requires `requests` (see requirements.txt).
"""

import argparse
import csv
import json
import requests
import sys
from typing import Dict, Any

GRAPHQL_MUTATION = '''
mutation CreateBook($title: String!, $author: String!, $publishedDate: String!, $isbnNumber: String!, $pages: Int!, $coverImage: String, $language: String!) {
  createBook(title: $title, author: $author, publishedDate: $publishedDate, isbnNumber: $isbnNumber, pages: $pages, coverImage: $coverImage, language: $language) {
    ok
    errors
    book { id title author publishedDate isbnNumber pages coverImage language }
  }
}
'''

DEFAULT_URL = "http://127.0.0.1:8000/graphql/"


def post_book(url: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"query": GRAPHQL_MUTATION, "variables": variables}
    try:
        r = requests.post(url, json=payload, timeout=10)
    except Exception as e:
        return {"network_error": str(e)}

    try:
        return r.json()
    except ValueError:
        return {"non_json_response": r.text}


def add_single(args) -> int:
    vars = {
        "title": args.title,
        "author": args.author,
        "publishedDate": args.published_date,
        "isbnNumber": args.isbn,
        "pages": args.pages,
        "coverImage": args.cover_image,
        "language": args.language,
    }
    print(f"Posting book: {args.title} — {args.isbn}")
    resp = post_book(args.url, vars)
    print(json.dumps(resp, indent=2))

    # Return 0 on success, 1 on failure
    if isinstance(resp, dict) and 'data' in resp and resp['data'] and resp['data'].get('createBook', {}).get('ok'):
        return 0
    return 1


def import_csv(args) -> int:
    failures = 0
    total = 0
    with open(args.csv, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            total += 1
            # Map CSV headers to variables expected by mutation
            vars = {
                "title": row.get('title') or row.get('Title'),
                "author": row.get('author') or row.get('Author'),
                "publishedDate": row.get('published_date') or row.get('publishedDate') or row.get('PublishedDate'),
                "isbnNumber": row.get('isbn_number') or row.get('isbn') or row.get('ISBN'),
                "pages": int(row.get('pages') or 0),
                "coverImage": row.get('cover_image') or row.get('coverImage') or None,
                "language": row.get('language') or row.get('Language') or 'Unknown',
            }

            print(f"[{total}] Posting: {vars['title']} — {vars['isbnNumber']}")
            resp = post_book(args.url, vars)
            if not (isinstance(resp, dict) and 'data' in resp and resp['data'] and resp['data'].get('createBook', {}).get('ok')):
                print(" -> Failed:")
                print(json.dumps(resp, indent=2))
                failures += 1

    print(f"Imported {total} rows, failures: {failures}")
    return 0 if failures == 0 else 2


def main():
    p = argparse.ArgumentParser(description='Add books to the GraphQL endpoint')
    p.add_argument('--url', default=DEFAULT_URL, help='GraphQL endpoint URL')

    # Single book args
    p.add_argument('--title', help='Book title')
    p.add_argument('--author', help='Book author')
    p.add_argument('--published-date', dest='published_date', help='Published date YYYY-MM-DD')
    p.add_argument('--isbn', help='ISBN (10 or 13 digits)')
    p.add_argument('--pages', type=int, help='Number of pages')
    p.add_argument('--cover-image', dest='cover_image', help='Cover image URL')
    p.add_argument('--language', help='Language')

    # CSV import
    p.add_argument('--csv', help='Path to CSV file to import (will ignore single-book args)')

    args = p.parse_args()

    if args.csv:
        sys.exit(import_csv(args))

    # Require single-book required fields
    required = ['title', 'author', 'published_date', 'isbn', 'pages', 'language']
    missing = [f for f in required if getattr(args, f if f != 'published_date' else 'published_date') is None]
    if missing:
        print('Missing required fields for single book:', missing)
        p.print_help()
        sys.exit(3)

    sys.exit(add_single(args))


if __name__ == '__main__':
    main()
