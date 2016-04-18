'''
Created on Apr 9, 2016

@author: ismith
'''
import apache_log_parser

from sklearn.feature_extraction.text import CountVectorizer
from anomaly_detection import *

#filename = "log_files/Aug28_log"
#filename_short = "log_files/Aug28_log_end"

filename = "log_files/access_log_Jul95-3"
filename_short = "log_files/access_log_Jul95-3_end"

line_parser = apache_log_parser.make_parser("%h - - %t \"%r\" %>s %b")
ignore_words_list = ["GET", "HTTP", "1.0"]
request_tokens = get_request_tokens_from_log(filename, ignore_words_list, line_parser, 100000)
        
count_vect = CountVectorizer()
X_train_counts = count_vect.fit_transform(request_tokens)
X_train_counts.shape

match_prop_dict = get_token_matching_probabilities(filename, count_vect, line_parser, 100000)

normality_indexes = compute_normality_indexes_using_runs_test(filename_short, [0], match_prop_dict, count_vect, line_parser)

sorted_normality_indexes = sorted(normality_indexes.items(), key=operator.itemgetter(1))

print(match_prop_dict)
print(sorted_normality_indexes)
print get_requests_and_scores_for_host(filename_short, "myserv.edu", match_prop_dict, count_vect, line_parser)

