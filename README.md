# Open Source Image Recommender
Final project for Machine Learning course at Oberlin College. By Lee Schumann, Adina Johnson, and Helen He.

To run our program, execute the following command:

python3 analyzeUrl.py <url-of-picture> <path-to-context-file>

This will find equivalents for the photo at <url-of-picture> in the unsplash database, using search terms as ranked
using the context of the text in the file at <path-to-context-file>

The following dependencies are necessary to run this program:

python-unsplash https://github.com/yakupadakli/python-unsplash

gensim https://radimrehurek.com/gensim/

nltk http://www.nltk.org