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
    
    
#two-sum
class Solution1:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        listI = [0] * max(nums)
        for i in range(len(nums)):
            listI[nums[i]-1] += 1

        listF = []
        for j in range(len(nums)):

            if target > nums[j]:
                listF.append(j)

                goal = target - nums[j] 

                if listI[goal-1] != 0:

                    listF.append(nums.index(goal))
                
                if len(listF) ==2:
                    return listF



user = input('Enter an array of integers with : ')
user_target = int(input('Enter your target: '))
user_list = [int(num) for num in user.split()] 

two_sum = Solution1()
print(two_sum.twoSum(user_list, user_target))
