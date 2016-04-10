'''
Created on Apr 9, 2016

@author: ismith
'''
import math
from sklearn.feature_extraction.text import CountVectorizer
import apache_log_parser

#What are the odds that a request has 0,1,2,3,4... of the items?
#If there is a request from source A, how many known words does it have?
#What are the odds that this number of known words exist in a request
#Multiply the odds of successive requests to get the odds of the batch of successive requests?

line_parser = apache_log_parser.make_parser("%h - - %t \"%r\" %>s %b")

#print line_parser('ppp111.cs.mci.com - - [01/Jul/1995:00:16:03 -0400] "GET /shuttle/missions/sts-74/mission-sts-74.html HTTP/1.0" 200 3707')
#exit()
#print log_line_data1['request_first_line'].split("/")
#print log_line_data1

array = []
limit = 10000
count = 0

with open("access_log_Jul95-3", "r") as ins:
    for line in ins:
        if count < limit:
            array.append(line_parser(line)['request_first_line']
                         .replace("/", " ")
                         .replace("GET", "")
                         .replace("HTTP", "")
                         .replace("pub", "")
                         .replace("images","")
                         )
            count += 1
        else:
            break
        
count_vect = CountVectorizer()
X_train_counts = count_vect.fit_transform(array)
X_train_counts.shape

limit = 0
match_prop_dict = {}
scores_for_host = {}

with open("access_log_Jul95-3", "r") as ins:
    for line in ins:
        parsed_line = line_parser(line)
        token_list = parsed_line['request_first_line'].replace("/", " ").split(" ")

        matches = 0
        for token in token_list:
            if count_vect.vocabulary_.has_key(token):
                print token
                matches += 1
                
        if match_prop_dict.has_key(matches) == False:
            match_prop_dict[matches] = 0
            
        match_prop_dict[matches] += 1
        
        limit += 1
        if limit >= count:
            break

print match_prop_dict

sum_of_all_matched_items = math.fsum(match_prop_dict.values()) 
#Compute probability for each match
match_prop_dict_probabilities = {}
for match_count in match_prop_dict.keys():
    match_prop_dict_probabilities[match_count] = match_prop_dict.get(match_count) / sum_of_all_matched_items

print match_prop_dict_probabilities

scores_for_host = {}

limit = 0
count = 11     

#with open("acccess_log_Jul95-3_scalp_hacker_access", "r") as ins:
with open("access_log_Jul95-3_end", "r") as ins:
    for line in ins:
        parsed_line = line_parser(line)
        token_list = parsed_line['request_first_line'].replace("/", " ").split(" ")

        matches = 0
        for token in token_list:
            if count_vect.vocabulary_.has_key(token):
                print token
                matches += 1
        
        if scores_for_host.has_key(parsed_line['remote_host']) == False:
            scores_for_host[parsed_line['remote_host']] = list()
            
        scores_for_host[parsed_line['remote_host']].append(matches)
        
        limit += 1
        if limit >= count:
            break

print scores_for_host

#Compute probability of sequence occurring
prob_of_sequence = {}
for host in scores_for_host.keys():
    prob_of_sequence[host] = 1
    for match_score in scores_for_host.get(host):
        prob_of_sequence[host] = prob_of_sequence[host] * match_prop_dict_probabilities[match_score]
        
print prob_of_sequence


