from math import log10
import gensim
from nltk.tokenize import casual_tokenize
from collections import Counter
from nltk.corpus import stopwords
import nltk
import string
from statistics import mean


class Vertex:
    """
    A class which will represent a vertex in the ranking graph
    """

    def __init__(self, word, count):
        """
        :param word: a word type from a given text
        :param count: the count of that word in the text
        """
        self.word = word
        self.count = count
        self.score = log10(count*10)
        self.sum_weights = None

    def set_sum_weights(self, neighbors, weights):
        """
        Sets the .sum_weights attribute to the sum of all the weights of this vertex's neighbors
        :param neighbors: an iterable of all the neighbors of this vertex
        :param weights: the weights between all vertices
        :return:
        """
        self_weights = [] # initialize a list which will hold all the weights between this vertex and others
        # iterate through the neighbors of this vertex
        for vj in neighbors:
            # if this vertex is in the collection of neighbors, skip it
            if vj is self:
                continue
            else:
                # get the weight between this vertex and another and append it to the list
                weight_self_j = weights[self.word][vj.word]
                self_weights.append(weight_self_j)

        # the sum_weights is not the sum of the entire weights list
        self.sum_weights = sum(self_weights)

    def update(self, d, neighbors, weights):
        """
        Update the vertex's score based on the weighted graph update rule in Mihalcea and Tarau's paper on TextRank
        :param d: a dampening factor (usually 0.85)
        :param neighbors: an iterable of all the neighbors of this vertex
        :param weights: a nested dictionary which maps two words (as strings) to the weight between them
        :return: "error", which is the difference between the score calculated at the end of this calculation and the
        score calculated last time, squared.
        """
        # save the score calculated last time in a local variable
        old_score = self.score

        votes_for_self = [] # initialize a list of the "votes" for this vertex
        # iterate through all the neighbors to get their information
        for vj in neighbors:
            weight_self_j = weights[self.word][vj.word]
            weight_score = weight_self_j / vj.sum_weights
            votes_for_self.append(weight_score * vj.score)

        self.score = (1-d) + (d * sum(votes_for_self))

        error = (self.score - old_score)**2
        return error


def get_search_terms(tags, text, file):
    """
    Returns a list of the original tags/search terms ranked using the provided text and a version of the TextRank
    algorithm presented in Mihalcea and Tarau's paper
    :param tags: the tags of the photo to be recommended
    :param text: the text which we can use to rank those tags
    :param file: a file to write information about the ranking process to.
    :return: the tag
    """
    # get the model for the weights
    print('loading model')
    model = gensim.models.KeyedVectors.load_word2vec_format('word2vec.6B.300d.model')
    print('model loaded')

    # tokenize the provided text
    tokens = casual_tokenize(text)
    # get a set of stopwords
    sw = set(stopwords.words())

    # append the tags to our list of tokens. Since word count factors in to the score and the tags which appear earlier
    # in the list are more likely to be accurate, append x copies of a given tag to the tokens, where x is the index + 1
    # of the tag in the reversed list
    tags.reverse()
    for i, tag in enumerate(tags):
        for j in range(i + 1):
            tokens.append(tag)

    tokens = nltk.pos_tag(tokens) # part-of-speech tag each of the tokens
    modded_tokens = []  # initialize a list which will hold the tokens that survive preprocessing
    for token, pos in tokens:
        # all the tokens must be lower case
        token = token.lower()
        # 's words do not appear in our word2vec model, remove the "'s"es
        if token[-2:] == "'s":
            token = token[:-2]
        # ignore the token if it is punctuation, a digit, or a stopword
        if token in string.punctuation or token.isdigit() or token in sw:
            continue
        # ignore the token if it is not in the word2vec model vocabulary
        elif token not in model.vocab:
            continue
        # ignore the token if it is in the following list of common Azure tags which are essentially useless for our
        # purposes.
        elif token in ['large', 'covered', 'background', 'standing', 'top', 'laying', 'tall', 'filled', 'many',
                       'several', 'small', 'little']:
            continue
        # This elif statement will become important in light of the following one.
        elif token in tags:
            modded_tokens.append(token)
        # If the token isn't in the tags and is not one of the following parts of speech, forget about it.
        elif pos not in ['NN', 'NNS', 'NNP', 'NPS', 'JJ']:
            continue

        # everything that survives, but in the modded_tokens list.
        else:
            modded_tokens.append(token)

    # get a dictionary which maps the tokens to their count in the list.
    type_counts = Counter(modded_tokens)
    # Having counted the tokens and reduced them to types, get a list of the types.
    types = list(type_counts.keys())

    # record some information
    word_type_log_string = '%d word types found' % len(types)
    print(word_type_log_string)
    file.write(word_type_log_string + '\n\n')

    # We start building the graph here.
    vertices = set() # initialize a set which will hold all the vertices

    # initialize a nested dictionary which maps words to dictionaries which map words to weights, thereby storing all
    # the weights between all the words
    weights = {word : {other_word : 0 for other_word in types} for word in types}

    # Iterate through all the different word types
    for word in types:
        vertex = Vertex(word, type_counts[word]) # make a vertex for the word type
        vertices.add(vertex) # add that vertex to the set.

        # put all the weights for this word into the nested dictionary
        for other_word in types:
            # the weight between each word is the words cosine similarity in the word2vec model, except with 1 added
            # and divided by 2, so that all weights are between 0 and 1.
            weights[word][other_word] = (model.similarity(word, other_word) + 1)/2
    # set the sum weights for each vertex
    for v in vertices:
        v.set_sum_weights(vertices, weights)
    print('graph built')

    print()
    print('beginning convergence')
    # now we begin the convergence
    mean_square_error = 1
    threshold = 0.00001
    file.write('threshold = %f' %threshold + '\n')
    file.write('Converging:\n')
    # as long as our mean squared error is above a certain threshold, keep trying to converge
    while mean_square_error > threshold:
        sqer = [] # initialize a list which will hold the squared errors for this iteration
        # update each of the vertices and append the squared error
        for v in vertices:
            error = v.update(0.85, vertices, weights)
            sqer.append(error)
        mean_square_error = mean(sqer)

        print(mean_square_error)
        file.write(str(mean_square_error) + '\n')
    file.write('\n')

    # now that we've converged, let's get those ordered tags/search terms
    search_terms = []
    ordered = list(vertices)
    # sort the vertices. the highest scores will come first.
    ordered.sort(key=lambda x: getattr(x, 'score'), reverse=True)
    # iterate through the vertices to weed out the ones which are not in our tag set.
    for v in ordered:
        word_ranking_log_string = '%s %d %f' %(v.word, v.count, v.score)
        if v.word in tags:
            indent = ''
            search_terms.append(v.word)
        else:
            indent = '\t'
        print(indent + word_ranking_log_string)
        file.write(indent + word_ranking_log_string + '\n')

    file.write('\n')

    return search_terms


if __name__ == "__main__":
    tags = ['outdoor', 'mountain', 'nature', 'forest', 'background', 'snow', 'lake', 'standing', 'covered', 'front',
            'tree', 'man', 'field', 'group', 'tall', 'hill', 'yellow', 'grazing', 'large', 'skiing', 'flock', 'slope']
    text = open('goat_mountain.output').read()
    file = open('mountain.output')
    get_search_terms(tags, text, file)