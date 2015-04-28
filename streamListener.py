
import requests
import json
from os import path

from TwitterAPI import TwitterAPI,TwitterError



def listener(c1,c2,c3,c4,query,tweets_path,max_errors) :

    api = TwitterAPI(c1,c2,c3,c4)

    tweets = open(tweets_path,'a')
    err_count = 0
    while err_count < max_errors :
        r = api.request('statuses/filter', {'track':query})
    
        try :        
            for tweet in r:
                if not 'user' in tweet :
                    print 'no user!'
                    continue
                
                if not 'entities' in tweet or not 'urls' in tweet['entities'] or len(tweet['entities']['urls']) == 0 :
                    print 'no urls!'
                    continue
                
                tweets.write( json.dumps(tweet) + '\n' )

        except Exception as e :
            print str(e)
            err_count += 1
            
    tweets.close()
                


if __name__ == '__main__' :

    project_folder = path.dirname(path.realpath(__file__)) + '/'
    config_path = project_folder + 'config.csv'
    
    with open(config_path,'r') as f :
        config_params = {}
        for line in f :
            try :
                pname,_,pvalue = map(lambda s : s.strip(),line.strip().partition(':'))
                config_params[pname] = pvalue
            except ValueError :
                continue

    c1 = config_params['c1']
    c2 = config_params['c2']
    c3 = config_params['c3']
    c4 = config_params['c4']
    query = config_params['query']
    max_errors = config_params['max_errors']
    tweets_path = config_params['tweets_path']
    tweets_path_abs = project_folder + tweets_path
    listener(c1,c2,c3,c4,query,tweets_path_abs,max_errors)

    


