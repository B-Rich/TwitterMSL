
from TwitterAPI import TwitterAPI,TwitterError
import requests

import os,time,random


def followers_seed(api,username) :
    '''
    Retrieves the followers of a Twitter profile, given its username (screen name).
    Returns a set of user IDs.

    '''
    uids = set()



    next_cursor = -1
    while next_cursor != 0 :

        try :
            followers = api.request('followers/ids', {'screen_name' : username, 'cursor' : str(next_cursor)})
            for u in followers :
                
                uids.add( u )

            if len(uids) == 0 :
                break
            next_cursor = (followers.json())['next_cursor']
            
        except TwitterError.TwitterRequestError as e :
            print 'Followers so far:',len(uids)
            print 'Zzz'
            time.sleep(60 * 16)
    
    return uids

def resolve(shortener) :
    r = requests.get(shortener)
    return r.url

    


def seed_to_urls(api,seed_users) :
    '''
    Retrieves a set of links shared from a seed community of Twitter users, given a list of user IDs.
    Returns a set of links.

    '''
    urls = set()
    
    for user_id in seed_users :

        user_timeline = api.request('statuses/user_timeline', {'user_id' : user_id})

        try :
            for tweet in user_timeline:

                if 'entities' in tweet and 'urls' in tweet['entities'] :
                    for url in tweet['entities']['urls'] :
                        urls.add(url['expanded_url'])

        except TwitterError.TwitterRequestError as e :
            print 'URLs so far:',len(urls)
            print 'Zzz'
            time.sleep(60 * 16)
    
    return urls



if __name__ == '__main__' :
    project_folder = os.path.dirname(os.path.realpath(__file__)) + '/'
    config_path = project_folder + 'config.csv'
    sample_size = 30
    
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

    api = TwitterAPI(c1,c2,c3,c4)


    from sys import argv
    username = argv[1]

    seed_path = 'seed_{}.txt'.format(username)
    domains_path = 'domains_{}.txt'.format(username)

    if not os.path.isfile(seed_path) :
        print 'Retrieving {} followers..'.format(username)
        followers = followers_seed(api,username)

        with open(seed_path,'w') as f :
            for uid in followers :
                f.write( str(uid) + '\n' )

    else :
        followers = set()
        with open(seed_path,'r') as f :
            for line in f :
                try :
                    uid = int(line.strip())
                    followers.add(uid)
                except ValueError :
                    continue

    print 'Followers retrieved:',len(followers)
    if not os.path.isfile(domains_path) :
        print 'Retrieving {} URLs..'.format(username)

        # retrieve URLs for a sample of the seed population
        followers = list(followers)
        sample_followers = [followers[i] for i in random.sample(xrange(len(followers)),sample_size)]

        urls = seed_to_urls(api,sample_followers)

        with open(domains_path,'w') as f :
            for url in urls :
                f.write( url + '\n' )

    else :
        urls = set()
        with open(domains_path,'r') as f :
            for line in f :
                if line != '' :
                    url = line.strip()
                    urls.add(url)

    print 'URLs retrieved:',len(urls)

    

    













