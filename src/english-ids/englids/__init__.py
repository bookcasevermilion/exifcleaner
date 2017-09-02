import pkg_resources
import random

def load(path):
    """
    Load a dictionary file from a given open file pointer, process into a pre-shuffled list
    of capitalized words.
    """
    output = []
    
    with open(path, 'r') as fp:
        for word in fp:
            output.append(word.strip().capitalize())
            
        random.shuffle(output)
        
    return output
    
def local_db_path(filename):
    """
    Locate a bundled word list by name (in the dict/ diectory)
    """
    resource_package = __name__
    resource_path = '/'.join(('dict', filename))
    
    return pkg_resources.resource_filename(resource_package, resource_path)

def cycle(words):
    """
    Return the next word from the given list.
    
    Cycles around back to the beginning when the end of the list is reached.
    """
    while True:
        for word in words:
            yield word
    

class Englids:
    
    def __init__(self, nouns=None, verbs=None, adjectives=None):
        """
        nouns: file path. If provided, used as the source of nouns.
        verbs: file path. If passed, used as the source of verbs.
        adjectives: file path. If passed, used as the source of adjectives.
        """
        if nouns is None:
            nouns = local_db_path('noun.exc')
        if verbs is None:
            verbs = local_db_path('verb.exc')
        if adjectives is None:
            adjectives = local_db_path('adj.exc')
        
        self.nouns = load(nouns)
                
        self.verbs = load(verbs)
                
        self.adjectives = load(adjectives)
            
        self._noun = cycle(self.nouns)
        self._verb = cycle(self.verbs)
        self._adjective = cycle(self.adjectives)
        
        self._last = None
        
    @property
    def stats(self):
        stats = {
            'nouns': len(self.nouns),
            'adjectives': len(self.adjectives),
            'verbs': len(self.verbs),
            'combinations': 0,
            'last': self._last
        }
        
        stats['combinations'] = stats['nouns']*stats['adjectives']*stats['verbs']
        
        return stats
        
    @property
    def noun(self):
        return next(self._noun)
    
    @property
    def verb(self):
        return next(self._verb)
        
    @property
    def adjective(self):
        return next(self._adjective)
        
    def __call__(self):
        self._last = "{}{}{}".format(self.adjective, self.noun, self.verb)
        return self._last
        