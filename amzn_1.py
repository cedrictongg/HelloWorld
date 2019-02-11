# import googlemaps
#
# api_key = 'AIzaSyDzqHUt2bSISOp6WQW0gPGPJtjnrW3Tih8'
#
# gmaps = googlemaps.Client(key=api_key)
#
# info = gmaps.distance_matrix('5901 East 7th Street, Long Beach, CA, USA', 'UNION STATION, Los Angeles, CA, USA')
# distance = info['rows'][0]['elements'][0]['distance']['text']
# km_to_mi = 0.621371
# print(float(distance[:4]) * km_to_mi)
#


"""
Write an algorithm to find the most frequently used word in the text excluding
the commonly used words

Input:
The input to the function/method consists of two arguments -
    literature_text, a strng representing the block of text
    words_to_exclude, a list of strings representing the commonly used words to
    be excluded while analyzing the word frequency

Output:
Return a list of strings representing the most frequently used words in the text
or in case of a tie, all of the most frequently used words in the text

# NOTE: Words that have difference case are counted as different words
        The order of words does not matter in the output list
        There is no punctuation in the text and the only white space is the
        space character
        All words in the words_to_exclude are unique

Example:
Input
    literature_text = 'jack and jill went to the market to buy bread and cheese
                        cheese is jack favorite food'
    words_to_exclude = ['and', 'he', 'the', 'to', 'a']
Output
['jack', 'cheese']
"""

literature_text = 'jack and jill went to the market to buy bread and cheese \
    cheese is jack favorite food'
words_to_exclude = ['and', 'he', 'the', 'to', 'a']


def map_and_remove(commons, literature_text):
    unique = {}
    word_list = literature_text.split(' ')
    for i in word_list:
        if i in unique:
            unique[i] += 1
        else:
            unique[i] = 1
    sw = dict((k, v) for k, v in unique.items() if k not in commons and k is not '')
    highest = max(sw.values())
    return [k for k, v in sw.items() if v == highest and k is not '']


print(map_and_remove(words_to_exclude, literature_text))
