SELECT bi.url, b.title, b.biblionumber
FROM biblio b
JOIN biblioitems bi USING (biblionumber)
WHERE bi.url <> ''
