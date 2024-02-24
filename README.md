# Library of Babble
I got tired of having to go to different websites to look at my content ratings (Goodreads, Letterboxd, Spotify, etc.) So I have decided to build a flask website that takes in csv exports from all those content libraries and aggregates them into one place. This allows me to add my own functionality like quote/note/review handling and other things that are harder to do on other platforms. 

## Source Files
| File        | Description | Required Columns | How To Generate | 
| ----------- | ----------- | --------------- |--------------- |
| **book_reviews.csv** | CSV file containing a list of book reviews | Book Id, Title, Author, Original Publication Year, Year Published, Cover Image URL, Date Read, My Rating, My Review | While logged into Goodreads go to My Books, then click on Import and export under Tools on the left. Export library as csv and you will get a file named `goodreads_library_export`. This will include all the books listed as Want to Read as well so filter down to just the books that you have read (For me that means just rows where Date Read is populated)|
| **book_quotes.csv** | CSV file containing a list of book quotes | Goodreads ID (Same as Book ID), Title, Quote, Page Number | Manually created |
| **movie_reviews.csv** | CSV file containing a list of movie reviews | Name, Director, Year, Movie Poster, Watched Date, Rating, Review | While logged into Letterboxd go to Settings, then Data, then click on Export Your Data. From the zip folder select the reviews file.|
| **movie_ratings.csv** | CSV file containing a list of movie ratings | Movie, Year, [User Name]| While logged into Letterboxd go to Settings, then Data, then click on Export Your Data. From the zip folder select the ratings file. Columns will need to be renamed manually.|
