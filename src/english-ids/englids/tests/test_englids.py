"""
Unit tests!
"""

import unittest
import englids
import random
import os

def dict_path(name):
    """
    Helper function that takes the name of a local dictionary file and returns
    its full path
    """
    source = os.path.dirname(__file__)
    path = os.path.abspath(os.path.join(source, "dict", "{}.txt".format(name)))
    return path

class TestBasicOperation(unittest.TestCase):
    
    def setUp(self):
        """
        Fix the seed so results will be predictable.
        """
        random.seed(1)
    
    def test_happy_path(self):
        """
        Ensure the default load/id generation pattern works.
        """
        e = englids.Englids()
        
        self.assertEquals(e(), "RuddierMestizoesMap")
        
    def test_custom_files(self):
        """
        Make sure loading our own files works properly.
        """
        e = englids.Englids(
            nouns=dict_path("four_entries_proper_nouns"),
            verbs=dict_path("four_entries_proper_nouns"),
            adjectives=dict_path("four_entries_proper_nouns"))
        
        self.assertEquals(e(), 'BuddyVirgilBobby')
        
    def test_cycling(self):
        """
        Make sure calling the generator repeatedly will loop back around to 
        the beginning.
        """
        e = englids.Englids(
            nouns=dict_path("four_entries_proper_nouns"),
            verbs=dict_path("four_entries_proper_nouns"),
            adjectives=dict_path("four_entries_proper_nouns"))
        
        self.assertEquals(e(), 'BuddyVirgilBobby')
        self.assertEquals(e(), 'VirgilJulianVirgil')
        self.assertEquals(e(), 'BobbyBuddyBuddy')
        self.assertEquals(e(), 'JulianBobbyJulian')
        self.assertEquals(e(), 'BuddyVirgilBobby')
        self.assertEquals(e(), 'VirgilJulianVirgil')
        
    def test_stats(self):
        """
        Check the stats() method
        """
        e = englids.Englids(
            nouns=dict_path("four_entries_proper_nouns"),
            verbs=dict_path("four_entries_proper_nouns"),
            adjectives=dict_path("four_entries_proper_nouns"))
         
        expected = {
            'nouns': 4,
            'adjectives': 4,
            'verbs': 4,
            'combinations': 64,
            'last': None
        }
        
        self.assertEqual(e.stats, expected)
        
        expected['last'] = 'BuddyVirgilBobby'
        
        e()
        
        self.assertEqual(e.stats, expected)
        