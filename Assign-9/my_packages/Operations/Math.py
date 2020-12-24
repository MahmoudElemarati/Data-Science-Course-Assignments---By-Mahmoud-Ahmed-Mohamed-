from functools import reduce

def get_sum(num1=1,num2=1):
    return num1+num2

def get_average(LIST=[1,2,3,4,5,6,7,8,9,10]):
    summation = reduce(get_sum,LIST)
    return summation/len(LIST)