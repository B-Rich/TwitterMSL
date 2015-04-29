
from TwitterAPI import TwitterAPI,TwitterError

import os,time


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

            
            next_cursor = (followers.json())['next_cursor']


            
        except TwitterError.TwitterRequestError as e :
            print 'Zzz'
            time.sleep(60 * 16)
    
    return uids
    


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

                for url in tweet['urls'] :
                    urls.add(url['expanded_url'])                

        except TwitterError.TwitterRequestError as e :
            sleep(60 * 16)
    
    return urls



if __name__ == '__main__' :
    project_folder = os.path.dirname(os.path.realpath(__file__)) + '/'
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

    api = TwitterAPI(c1,c2,c3,c4)

    from sys import argv
    username = argv[1]
    print 'Retrieving {} followers..'.format(username)
    followers = followers_seed(api,username)
    print 'Followers retrieved:',len(followers)
    

    













