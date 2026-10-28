# -*- coding: utf-8 -*-
"""
Created on Sat Oct 10 22:50:44 2026

@author: ataly
"""

#valid anagram
from collections import Counter
from collections import defaultdict
from typing import List

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
    
    
#two-sum
class Solution1:
    def twoSum(self, nums: list[int], target: int) -> list[int]:    
        my_dict = {}
        num_output = []
        for i in range (len(nums)):
            if target-nums[i] in my_dict:
               num_output.append(my_dict.get(target-nums[i]))
               num_output.append(i)

            my_dict [nums[i]] = i
        return num_output
# reflection, my code was correct! I was just populating the dictionary before I checked it!

user = input('Enter an array of integers with : ')
user_target = int(input('Enter your target: '))
user_list = [int(num) for num in user.split()] 

two_sum = Solution1()
print(two_sum.twoSum(user_list, user_target))

#group_anagrams


class Solution2:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        groups = defaultdict(list)

        #holds the frequency for each word, can use counter but counter is o(n)
        for word in strs:
            counts = [0] *26
            #goes through every char in a word, find its index thro calculations andincrements the position the word is found at
            for char in word:
                index = ord(char) - ord("a")
                counts[index] +=1 
            #uses the freq array as a key to locate the word, rather than going through each word or comparing every word  "2, 1, 0" = word
            groups[tuple(counts)].append(word)


        return list(groups.values())
    
class Solution3:
    def containsDuplicate(self, nums:list[int])-> bool:
        seen= {}
        count =0
        for num in nums:
            if not num in seen:
               seen[num]= count + 1
            else:
               return True
          
        return False

class Solution4:
    def topKFrequent(self, nums:List[int], k:int)-> List[int]:
        length = len(nums) 
        max_num = max(nums)
        arr = [0]* (max_num +1)
        output= []
        for i in range(length):
            arr[nums[i]]+=1
            
        for i in range(len(arr)):
            if arr[i] >= k :
                output.append(i)
                
        return output
            
    

