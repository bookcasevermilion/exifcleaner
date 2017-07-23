import pkg_resources
import random

def load(db):
    resource_package = __name__
    resource_path = '/'.join(('dict', db))
    
    words = pkg_resources.resource_stream(resource_package, resource_path)
    
    output = []
    
    for line in words:
        # two per line for some reason
        parts = [x.capitalize() for x in line.decode("utf-8").strip().split(" ")]
        
        output.extend(parts)
        
    random.shuffle(output)
        
    return output

def cycle(words):
    """
    Return the next word from the given list.
    
    Cycles around back to the beginning when the end of the list is reached.
    """
    for word in words:
        yield word
    

class Englids:
    
    def __init__(self):
        self.nouns = load('noun.exc')
        self.verbs = load('verb.exc')
        self.adjectives = load('adj.exc')
        
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
        