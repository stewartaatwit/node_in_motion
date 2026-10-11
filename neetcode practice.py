# -*- coding: utf-8 -*-
"""
Created on Sat Oct 10 22:50:44 2026

@author: ataly
"""

#valid anagram
from collections import Counter

class Solution:
    def isAnagram (self, s:str, t:str) -> bool:
        return Counter(s)== Counter(t)
    

user = input('Enter two words with space: ')

words = user.split()

words1, words2 = words[0], words[1]

#create a solution object
anagram = Solution() 

if anagram.isAnagram(words1, words2):
    print('these words are anagrams')
else:
    print('these words are not anagrams')