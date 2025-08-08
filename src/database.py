import sqlite3
import json
from typing import List, Dict, Any
from models import ResultItem


class DatabaseManager:
    def __init__(self, db_path: str = "products.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS search_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    products_count INTEGER DEFAULT 0
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_query_id INTEGER,
                    product_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    brand TEXT,
                    price REAL,
                    score REAL,
                    available BOOLEAN,
                    link_url TEXT,
                    image_url TEXT,
                    image_urls TEXT,
                    rating TEXT,
                    vendorcode TEXT,
                    reviewscount TEXT,
                    categories TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (search_query_id) REFERENCES search_queries (id)
                )
            ''')
            conn.commit()

    def save(self, query: str, products: List[Dict[str, Any]]) -> int:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO search_queries (query, products_count) VALUES (?, ?)',
                (query, len(products))
            )
            qid = c.lastrowid
            for p in products:
                c.execute('''
                    INSERT INTO products (
                        search_query_id, product_id, name, brand, price, score,
                        available, link_url, image_url, image_urls, rating,
                        vendorcode, reviewscount, categories
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    qid,
                    p.get('id'),
                    p.get('name'),
                    p.get('brand'),
                    p.get('price'),
                    p.get('score'),
                    p.get('available'),
                    p.get('link_url'),
                    p.get('image_url'),
                    json.dumps(p.get('image_urls', [])),
                    json.dumps(p.get('attributes', {}).get('rating', [])),
                    json.dumps(p.get('attributes', {}).get('vendorcode', [])),
                    json.dumps(p.get('attributes', {}).get('reviewscount', [])),
                    json.dumps([
                        {
                            'id': cat.get('id'),
                            'name': cat.get('name'),
                            'direct': cat.get('direct'),
                            'link_url': cat.get('link_url'),
                            'image_url': cat.get('image_url')
                        }
                        for cat in p.get('categories', [])
                    ])
                ))
            conn.commit()
            return qid

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                'SELECT id, query, timestamp, products_count FROM search_queries ORDER BY timestamp DESC LIMIT ?',
                (limit,)
            )
            return [
                {'id': i, 'query': q, 'timestamp': t, 'products_count': pc}
                for i, q, t, pc in c.fetchall()
            ]

    def get_by_query_id(self, qid: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT product_id, name, brand, price, score, available,
                       link_url, image_url, image_urls, rating, vendorcode,
                       reviewscount, categories
                FROM products
                WHERE search_query_id = ?
                ORDER BY score DESC
            ''', (qid,))
            return [
                {
                    'id': i,
                    'name': n,
                    'brand': b,
                    'price': p,
                    'score': s,
                    'available': a,
                    'link_url': lu,
                    'image_url': iu,
                    'image_urls': json.loads(ius or "[]"),
                    'attributes': {
                        'rating': json.loads(r or "[]"),
                        'vendorcode': json.loads(vc or "[]"),
                        'reviewscount': json.loads(rc or "[]")
                    },
                    'categories': json.loads(cats or "[]")
                }
                for i, n, b, p, s, a, lu, iu, ius, r, vc, rc, cats in c.fetchall()
            ]

    def get_by_query_text(self, text: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT p.product_id, p.name, p.brand, p.price, p.score, p.available,
                       p.link_url, p.image_url, p.image_urls, p.rating, p.vendorcode,
                       p.reviewscount, p.categories
                FROM products p
                JOIN search_queries sq ON p.search_query_id = sq.id
                WHERE sq.query LIKE ?
                ORDER BY p.score DESC
            ''', (f'%{text}%',))
            return [
                {
                    'id': i,
                    'name': n,
                    'brand': b,
                    'price': p,
                    'score': s,
                    'available': a,
                    'link_url': lu,
                    'image_url': iu,
                    'image_urls': json.loads(ius or "[]"),
                    'attributes': {
                        'rating': json.loads(r or "[]"),
                        'vendorcode': json.loads(vc or "[]"),
                        'reviewscount': json.loads(rc or "[]")
                    },
                    'categories': json.loads(cats or "[]")
                }
                for i, n, b, p, s, a, lu, iu, ius, r, vc, rc, cats in c.fetchall()
            ]

    def get_stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM search_queries')
            tq = c.fetchone()[0]
            c.execute('SELECT COUNT(*) FROM products')
            tp = c.fetchone()[0]
            c.execute('SELECT AVG(products_count) FROM search_queries')
            avg = c.fetchone()[0] or 0
            c.execute('''
                SELECT query, COUNT(*) as count
                FROM search_queries
                GROUP BY query
                ORDER BY count DESC
                LIMIT 5
            ''')
            top = [{'query': q, 'count': c} for q, c in c.fetchall()]
            return {
                'total_queries': tq,
                'total_products': tp,
                'avg_products_per_query': round(avg, 2),
                'popular_queries': top
            }


db_manager = DatabaseManager()
