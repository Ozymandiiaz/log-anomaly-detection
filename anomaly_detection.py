'''
Created on Apr 17, 2016

@author: ismith
'''
import math
import operator
import apache_log_parser

from sklearn.feature_extraction.text import CountVectorizer
from scipy.stats import ttest_1samp

def get_request_tokens_from_log(file_name, ignore_words, line_parser, line_limit):
    array = []
    count = 0
    #Read the file and add the tokens to a count vectorizer
    with open(file_name, "r") as ins:
        for line in ins:
            parsed_line = line_parser(line)  
            
            #Don't include it if the request wasn't a success
            if parsed_line['status'] != "200":
                continue
            
            parsed_request = parsed_line['request_first_line'].replace("/", " ")
            
            for word in ignore_words:
                parsed_request = parsed_request.replace(word, "")
                         
            array.append(parsed_request)
            
            count = count + 1
            if line_limit <= count:
                break
            
    return array

def get_token_matching_probabilities(file_name, count_vectorizer, line_parser, line_limit):
    match_prop_dict = {}
    tokens_used = []
    count = 0
    
    with open(file_name, "r") as ins:
        for line in ins:
            parsed_line = line_parser(line)
            
            #Don't include it if the request wasn't a success
            if parsed_line['status'] != "200":
                continue
            
            token_list = parsed_line['request_first_line'].replace("/", " ").split(" ")
    
            matches = 0
            for token in token_list:
                if count_vectorizer.vocabulary_.has_key(token):
                    tokens_used.append(token)
                    matches += 1
                    
            if match_prop_dict.has_key(matches) == False:
                match_prop_dict[matches] = 0
                
            match_prop_dict[matches] += 1
            
            count = count + 1
            if line_limit <= count:
                break
            
    sum_of_all_matched_items = math.fsum(match_prop_dict.values()) 
    
    #Compute probability for each match
    match_prop_dict_probabilities = {}
    for match_count in match_prop_dict.keys():
        match_prop_dict_probabilities[match_count] = match_prop_dict.get(match_count) / sum_of_all_matched_items
    
    return match_prop_dict_probabilities

def get_vocabulary_matches_for_host(filename, match_prop_dict, count_vect, line_parser):
    scores_for_host = {}
    
    with open(filename, "r") as ins:
        for line in ins:
            parsed_line = line_parser(line)
            
            token_list = parsed_line['request_first_line'].replace("/", " ").split(" ")
    
            matches = 0
            for token in token_list:
                if count_vect.vocabulary_.has_key(token):
                    matches += 1
            
            if scores_for_host.has_key(parsed_line['remote_host']) == False:
                scores_for_host[parsed_line['remote_host']] = list()
                
            scores_for_host[parsed_line['remote_host']].append(matches)
            
    return scores_for_host

def compute_normality_indexes_for_hosts(filename, match_prop_dict, count_vect, line_parser):
    scores_for_host = get_vocabulary_matches_for_host(filename, match_prop_dict, count_vect, line_parser)
    
    #Compute probability of sequence occurring
    prob_of_sequence = {}
    for host in scores_for_host.keys():
        
        for match_score in scores_for_host.get(host):
            if match_prop_dict.has_key(match_score):
                if prob_of_sequence.has_key(host) == False:
                    prob_of_sequence[host] = 1
                
                prob_of_sequence[host] = prob_of_sequence[host] * match_prop_dict[match_score]
    
    return prob_of_sequence

def get_requests_and_scores_for_host(filename, hostname, match_prop_dict, count_vect, line_parser):
    requests_for_host = {}
    
    with open(filename, "r") as ins:
        for line in ins:
            parsed_line = line_parser(line)
            
            token_list = parsed_line['request_first_line'].replace("/", " ").split(" ")
            
            if (parsed_line['remote_host'] != hostname):
                continue
    
            matches = 0
            for token in token_list:
                if count_vect.vocabulary_.has_key(token):
                    matches += 1
            
            requests_for_host[parsed_line['request_first_line'] + " " + parsed_line['status']] = matches
        
    return requests_for_host

def compute_normality_indexes_using_runs_test(filename, low_scores, match_prop_dict, count_vect, line_parser):
    scores_for_hosts = get_vocabulary_matches_for_host(filename, match_prop_dict, count_vect, line_parser)
    suspicious_host_scores = {}
    
    popmean = 0
    for low_score in low_scores:
        popmean += match_prop_dict[low_score]
    
    for host in scores_for_hosts.keys():
        #Runs test only works for larger sized samples
        if len(scores_for_hosts.get(host)) < 10:
            continue
        
        binary_host_scores = []
        for score in scores_for_hosts.get(host):
            binary_score = int(int(score) in low_scores)
            binary_host_scores.append(binary_score)
            
        print(host)
        print(binary_host_scores)
        
        test_result = ttest_1samp(binary_host_scores, popmean)
        
        if test_result.statistic < 0:
            continue
        
        suspicious_host_scores[host] = test_result.pvalue
    
    return suspicious_host_scores

