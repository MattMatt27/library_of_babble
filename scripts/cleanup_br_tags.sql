-- SQL Script to Remove <br> Tags from Existing Reviews and Data
-- Run this against your PostgreSQL database

-- Clean up the reviews table
UPDATE reviews
SET review_text = REPLACE(REPLACE(REPLACE(review_text, '<br>', E'\n'), '<br/>', E'\n'), '<br />', E'\n')
WHERE review_text LIKE '%<br%';

-- Clean up the books table (my_review column)
UPDATE books
SET my_review = REPLACE(REPLACE(REPLACE(my_review, '<br>', E'\n'), '<br/>', E'\n'), '<br />', E'\n')
WHERE my_review LIKE '%<br%';

-- Clean up the books table (private_notes column)
UPDATE books
SET private_notes = REPLACE(REPLACE(REPLACE(private_notes, '<br>', E'\n'), '<br/>', E'\n'), '<br />', E'\n')
WHERE private_notes LIKE '%<br%';

-- Clean up the movies table (my_review column)
UPDATE movies
SET my_review = REPLACE(REPLACE(REPLACE(my_review, '<br>', E'\n'), '<br/>', E'\n'), '<br />', E'\n')
WHERE my_review LIKE '%<br%';

-- Clean up the tv_shows table (my_review column)
UPDATE tv_shows
SET my_review = REPLACE(REPLACE(REPLACE(my_review, '<br>', E'\n'), '<br/>', E'\n'), '<br />', E'\n')
WHERE my_review LIKE '%<br%';

-- Display summary of changes
SELECT
    'reviews' AS table_name,
    COUNT(*) AS rows_with_newlines
FROM reviews
WHERE review_text LIKE '%' || E'\n' || '%'
UNION ALL
SELECT
    'books (my_review)' AS table_name,
    COUNT(*) AS rows_with_newlines
FROM books
WHERE my_review LIKE '%' || E'\n' || '%'
UNION ALL
SELECT
    'books (private_notes)' AS table_name,
    COUNT(*) AS rows_with_newlines
FROM books
WHERE private_notes LIKE '%' || E'\n' || '%'
UNION ALL
SELECT
    'movies (my_review)' AS table_name,
    COUNT(*) AS rows_with_newlines
FROM movies
WHERE my_review LIKE '%' || E'\n' || '%'
UNION ALL
SELECT
    'tv_shows (my_review)' AS table_name,
    COUNT(*) AS rows_with_newlines
FROM tv_shows
WHERE my_review LIKE '%' || E'\n' || '%';
