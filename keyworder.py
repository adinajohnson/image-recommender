from math import log10
import gensim
from nltk.tokenize import casual_tokenize
from collections import Counter
from nltk.corpus import stopwords
import nltk
import string
from statistics import mean


class Vertex:

    def __init__(self, word, count):
        """
        :param word: a word type from a given text
        :param count: the count of that word in the text
        """
        self.word = word
        self.count = count
        self.score = log10(count*10)
        self.sum_weights = None

    def get_sum_weights(self, neighbors, weights):
        self_weights = []
        for vj in neighbors:
            weight_self_j = weights[self.word][vj.word]
            self_weights.append(weight_self_j)
        self.sum_weights = sum(self_weights)

    def update(self, d, neighbors, weights):
        old_score = self.score

        i_votes = []
        for vj in neighbors:
            weight_self_j = weights[self.word][vj.word]
            weight_score = weight_self_j / vj.sum_weights
            i_votes.append(weight_score * vj.score)

        self.score = (1-d) + (d * sum(i_votes))

        error = (self.score - old_score)**2
        return error


def get_search_terms(tags, text):
    print('imports complete')

    # get the model for the weights
    model = gensim.models.KeyedVectors.load_word2vec_format('word2vec.6B.300d.txt')
    print('model loaded')

    tokens = list(casual_tokenize(text))
    sw = set(stopwords.words())
    modded_tokens = []

    tags.reverse()
    for i, pos in enumerate(tags):
        for j in range(i + 1):
            tokens.append(pos)

    tokens = nltk.pos_tag(tokens)
    for token, pos in tokens:
        token = token.lower()
        if token[-2:] == "'s":
            token = token[:-2]
        if token in string.punctuation or token.isdigit() or token in sw:
            continue
        elif token not in model.vocab:
            continue

        elif token in ['large', 'covered', 'background', 'standing', 'top', 'laying', 'tall', 'filled', 'many',
                       'several', 'small', 'little']:
            continue
        elif token in tags:
            modded_tokens.append(token)
        elif pos not in ['NN', 'NNS', 'NNP', 'NPS', 'JJ']:
            continue

        else:
            modded_tokens.append(token)
    type_counts = Counter(modded_tokens)
    types = list(type_counts)
    print('word types retrieved. %d word types found' % len(types))

    vertices = set()
    weights = {word : {other_word : 0 for other_word in types} for word in types}
    for word in types:
        vertex = Vertex(word, type_counts[word])
        vertices.add(vertex)
        for other_word in types:
            weights[word][other_word] = (model.similarity(word, other_word) + 1)/2
    for v in vertices:
        v.get_sum_weights(vertices, weights)
    print('graph built')

    print()
    print('beginning convergence')
    # now we begin the convergence
    mean_square_error = 1
    while mean_square_error > 0.00001:
        sqer = []
        for v in vertices:
            error = v.update(0.85, vertices, weights)
            sqer.append(error)
        mean_square_error = mean(sqer)
        print(mean_square_error)

    search_terms = []
    ordered = list(vertices)
    ordered.sort(key=lambda x: getattr(x, 'score'), reverse=True)
    for v in ordered:
        if v.word in tags:
            print('\t', v.word, v.count, v.score)
            search_terms.append(v.word)
        else:
            print(v.word, v.count, v.score)

    search_terms = search_terms[:3]
    return search_terms


if __name__ == "__main__":
    tags = ['outdoor', 'mountain', 'nature', 'forest', 'background', 'snow', 'lake', 'standing', 'covered', 'front',
            'tree', 'man', 'field', 'group', 'tall', 'hill', 'yellow', 'grazing', 'large', 'skiing', 'flock', 'slope']
    text = open('goat_mountain.output').read()
    get_search_terms(tags, text)