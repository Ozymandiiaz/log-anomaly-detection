'''
Created on Apr 17, 2016

@author: ismith
'''
import math
import operator
import apache_log_parser
from sets import Set
import logging

from sklearn.feature_extraction.text import CountVectorizer
from scipy.stats import ttest_1samp
from numpy import Infinity

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
            
            token_list = get_tokens_from_request(parsed_line['request_first_line'], ignore_words)
            
            if len(token_list) == 0:
                continue
            
            array.append(' '.join(token_list))
            
            count = count + 1
            if line_limit <= count:
                break
            
    return array

def get_token_matching_probabilities(file_name, count_vectorizer, line_parser, line_limit, is_match=True):
    match_prop_dict = {}
    tokens_used = []
    count = 0
    
    with open(file_name, "r") as ins:
        for line in ins:
            parsed_line = line_parser(line)
            
            #Don't include it if the request wasn't a success
            if parsed_line['status'] != "200":
                continue
            
            token_list = get_tokens_from_request(parsed_line['request_first_line'], ["get", "http", "gif"])
                        
            if len(token_list) == 0:
                logging.debug(parsed_line['request_first_line'] + " -> " + [].__str__() + " -> " + (0).__str__())
                continue
    
            matches = 0
            for token in token_list:
                if count_vectorizer.vocabulary_.has_key(token) == is_match:
                    tokens_used.append(token)
                    matches += 1
                    
            logging.debug(parsed_line['request_first_line'] + " -> " + token_list.__str__() + " -> " + matches.__str__())
            
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

def get_vocabulary_matches_for_host(filename, match_prop_dict, count_vect, line_parser, is_match=True):
    scores_for_host = {}
    
    with open(filename, "r") as ins:
        for line in ins:
            parsed_line = line_parser(line)
            
            token_list = get_tokens_from_request(parsed_line['request_first_line'], ["get", "http", "gif"])
            
            if len(token_list) == 0:
                continue
    
            matches = 0
            for token in token_list:
                if count_vect.vocabulary_.has_key(token) == is_match:
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
            if len(scores_for_host.get(host)) >= 10:
                continue
                
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
            
            token_list = get_tokens_from_request(parsed_line['request_first_line'], ["get", "http", "gif"])
            
            if (parsed_line['remote_host'] != hostname):
                continue
    
            matches = 0
            for token in token_list:
                if count_vect.vocabulary_.has_key(token):
                    matches += 1
            
            requests_for_host[parsed_line['request_first_line'] + " " + parsed_line['status']] = matches
        
    return requests_for_host

def compute_normality_indexes_using_runs_test(filename, low_score_threshold, match_prop_dict, count_vect, line_parser, is_match=True):
    scores_for_hosts = get_vocabulary_matches_for_host(filename, match_prop_dict, count_vect, line_parser, is_match)
    suspicious_host_scores = {}
    
    popmean = 1
    for score in match_prop_dict.keys():
        if score <= low_score_threshold:
            popmean -= match_prop_dict[score]
        
    logging.debug("Population Mean" + popmean.__str__())
    
    for host in scores_for_hosts.keys():
        #Runs test only works for larger sized samples
        if len(scores_for_hosts.get(host)) < 5:
            continue
        
        binary_host_scores = []
        last_binary_score = None
        
        all_binary_scores_the_same = True
        all_host_scores = scores_for_hosts.get(host)
        
        for score in all_host_scores:
            binary_score = int(int(score) > low_score_threshold)
            
            if last_binary_score == None:
                 last_binary_score = binary_score
            
            if last_binary_score != binary_score:
                all_binary_scores_the_same = False
            
            binary_host_scores.append(binary_score)
        
        
        if all_binary_scores_the_same == True and last_binary_score == 1:
            suspicious_host_scores[host] = 1
        else:
            test_result = ttest_1samp(binary_host_scores, popmean)
            suspicious_host_scores[host] = test_result.pvalue
        
    return suspicious_host_scores

def get_tokens_from_request(http_request_string, ignore_words):    
    ignore_words_set = Set(ignore_words)
         
    request_tokens = http_request_string.replace("/", " ").strip().split(" ")
    
    cv = CountVectorizer()
    
    try:
        cv.fit_transform(request_tokens)
    except UnicodeDecodeError:
        return []
    
    word_array = []
    
    for word in cv.vocabulary_.keys():
        if word not in ignore_words_set:
            word_array.append(word)
    
    return word_array
    
    
         
    

