'''
Created on Apr 9, 2016

@author: ismith
'''
import math
from sklearn.feature_extraction.text import CountVectorizer
import apache_log_parser

line_parser = apache_log_parser.make_parser("%h - - %t \"%r\" %>s %b")

#log_line_data1 = line_parser('ppp111.cs.mci.com - - [01/Jul/1995:00:16:03 -0400] "GET /shuttle/missions/sts-74/mission-sts-74.html HTTP/1.0" 200 3707')
#print log_line_data1['request_first_line'].split("/")
#print log_line_data1

array = []
limit = 10000
count = 0

with open("Aug28_log", "r") as ins:
    for line in ins:
        if count < limit:
            array.append(line_parser(line)['request_first_line'].replace("/", " ").replace("GET", "").replace("HTTP", "").replace("pub", "").replace("images",""))
            count += 1
        else:
            break
        
count_vect = CountVectorizer()
X_train_counts = count_vect.fit_transform(array)
X_train_counts.shape

limit = 0
count = 72

match_prop_dict = {}

with open("intrusion_attempts", "r") as ins:
    for line in ins:
        #token_list = line_parser("d104.aa.net - - [10/Oct/2007:20:24:18 -0700] \"GET / webmin HTTP/1.0\" 404 726")['request_first_line'].split("/")
        token_list = line_parser(line)['request_first_line'].replace("/", " ").split(" ")

        matches = 0
        for token in token_list:
            if count_vect.vocabulary_.has_key(token):
                print token
                matches += 1
        
        #print matches
                
        if match_prop_dict.has_key(matches) == False:
            match_prop_dict[matches] = 0
            
        match_prop_dict[matches] += 1
        
        limit += 1
        if limit >= count:
            break
        
print match_prop_dict
print math.fsum(match_prop_dict.values())

#What are the odds that a request has 0,1,2,3,4... of the items?
#If there is a request from source A, how many known words does it have?
#What are the odds that this number of known words exist in a request
#Multiply the odds of successive requests to get the odds of the batch of successive requests?

#line_parser = apache_log_parser.make_parser("%h <<%P>> %t %Dus \"%r\" %>s %b  \"%{Referer}i\" \"%{User-Agent}i\" %l %u")
#log_line_data = line_parser('127.0.0.1 <<6113>> [16/Aug/2013:15:45:34 +0000] 1966093us "GET / HTTP/1.1" 200 3478  "https://example.com/" "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18)" - -')

#Get log data
#For each line...
###Extract HTTP requests
###Extract error codes





