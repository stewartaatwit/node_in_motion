# -*- coding: utf-8 -*-
"""
Created on Sun Oct 25 17:21:16 2026

@author: ataly
"""

import math
import os
import random
import re
import sys

#
# Complete the 'compareTriplets' function below.
#
# The function is expected to return an INTEGER_ARRAY.
# The function accepts following parameters:
#  1. INTEGER_ARRAY a
#  2. INTEGER_ARRAY b
#

def compareTriplets(a, b):
    # Write your code here
    score_array= [0] *2
    for i in range(3):
        if a[i]> b[i]:
            score_array[0]=score_array[0]+1
        elif a[i]<b[i]:
            score_array[1]= score_array[1]+1
    return score_array
    

if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')

    a = list(map(int, input().rstrip().split()))

    b = list(map(int, input().rstrip().split()))

    result = compareTriplets(a, b)

    fptr.write(' '.join(map(str, result)))
    fptr.write('\n')

    fptr.close()
