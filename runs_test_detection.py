'''
Created on Apr 9, 2016

@author: ismith
'''
import apache_log_parser

from sklearn.feature_extraction.text import CountVectorizer
from anomaly_detection import *
import logging

logging.basicConfig(level=logging.INFO)

filename_learning = "log_files/test_case_2/xaa"
filenam_prob = "log_files/test_case_2/xab"
filename_short = "log_files/NASA-access_log_Jul95-3_end"

#filename_learning = "log_files/test_case_1/learning-test-case-1"
#filenam_prob  = "log_files/test_case_1/probabilities-test-case-1"
#filename_short = "log_files/test_case_1/analysis-test-case-1"

line_parser = apache_log_parser.make_parser("%h - - %t \"%r\" %>s %b")
ignore_words_list = ["get", "http", "gif"]

request_tokens = get_request_tokens_from_log(filename_learning, ignore_words_list, line_parser, 10000)

count_vect = CountVectorizer()
X_train_counts = count_vect.fit_transform(request_tokens)
X_train_counts.shape

#logging.info("Vocabulary Generated: " + count_vect.vocabulary_.__str__())

match_prop_dict = get_token_matching_probabilities(filenam_prob, count_vect, line_parser, 10000, True)

logging.info("Token Matching Probabilities: " + match_prop_dict.__str__())

normality_indexes = compute_normality_indexes_using_runs_test(filename_short, 1, match_prop_dict, count_vect, line_parser, True)

logging.info("Normality Indexes: " + normality_indexes.__str__())

sorted_normality_indexes = sorted(normality_indexes.items(), key=operator.itemgetter(1), reverse=False)

logging.info(sorted_normality_indexes)
