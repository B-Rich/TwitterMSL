
from TwitterAPI import TwitterAPI,TwitterError
import requests

import os,time,random


def followers_seed(api,f,username) :
    '''
    Retrieves the followers of a Twitter profile, given its username (screen name).
    Returns a set of user IDs.

    '''
    uids = []

    next_cursor = -1
    while next_cursor != 0 :

        try :
            followers = api.request('followers/ids', {'screen_name' : username, 'cursor' : str(next_cursor)})
            for u in followers :
                
                uids.append( u )

            if len(uids) == 0 :
                break
            next_cursor = (followers.json())['next_cursor']
            
        except TwitterError.TwitterRequestError as e :
            print 'writing {} users'.format(str(len(uids)))
            for uid in uids :
                f.write( str(uid) + '\n' )
            uids = []
            print 'Zzz'
            time.sleep(60 * 16)
    

def resolve(shortener) :
    r = requests.get(shortener)
    return r.url

    


def seed_to_urls(api,f,seed_users) :
    '''
    Retrieves a set of links shared from a seed community of Twitter users, given a list of user IDs.
    Returns a set of links.

    '''
    urls = []

    ucount = 0
    tcount = 0

    tweets_per_user = 10
    for user_id in seed_users :
        
        user_timeline = api.request('statuses/user_timeline', {'user_id' : user_id})

        j = 0
        try :
            for tweet in user_timeline:

                if 'entities' in tweet and 'urls' in tweet['entities'] :
                    for url in tweet['entities']['urls'] :
                        urls.append(url['expanded_url'])
                        tcount += 1
                j += 1
                if j >= tweets_per_user :
                    break

        except TwitterError.TwitterRequestError as e :
            
            for u in urls :
                try :
                    f.write( u + '\n' )
                except UnicodeEncodeError :
                    continue
            urls = []
            print 'Zzz'
            time.sleep(60 * 16)

        ucount += 1
        print 'Users: {}/{} URLs: {}'.format(str(ucount),str(len(seed_users)),str(tcount))
    
def seed_to_urls2(api,f,seed_users) :
    '''
    Retrieves a set of links shared from a seed community of Twitter users, given a list of user IDs.
    Returns a set of links.

    '''
    urls = []
    i = 0
    tcount = 0
    while i < len(seed_users) :
        users = [seed_users[j] for j in xrange(i,i+100)]
        i += 100
        
        response = api.request('users/lookup', {'user_id' : users, 'include_entities' : 'true'})


        try :
            for x in response:

                if 'status' in x and 'entities' in x['status'] and 'urls' in x['status']['entities'] :
                    for url in x['status']['entities']['urls'] :
                        urls.append(url['expanded_url'])
                        tcount += 1

        except TwitterError.TwitterRequestError as e :
            
            for u in urls :
                try :
                    f.write( u + '\n' )
                except UnicodeEncodeError :
                    continue
            urls = []
            print 'Zzz'
            time.sleep(60 * 16)

        print 'Users: {}/{} URLs: {}'.format(str(i),str(len(seed_users)),str(tcount))    



if __name__ == '__main__' :
    project_folder = os.path.dirname(os.path.realpath(__file__)) + '/'
    config_path = project_folder + 'config.csv'
    sample_size = 50000
    
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
    resolved_path = 'resolved_domains_{}'.format(username)

    if not os.path.isfile(seed_path) :
        print 'Retrieving {} followers..'.format(username)
        with open(seed_path,'w') as f :
            followers_seed(api,f,username)
            exit()
    else :
        followers = set()
        with open(seed_path,'r') as f :
            for line in f :
                try :
                    uid = int(line.strip())
                    followers.add(uid)
                except ValueError :
                    continue

    if not os.path.isfile(domains_path) :
        print 'Retrieving {} URLs..'.format(username)

        # retrieve URLs for a sample of the seed population
        followers = list(followers)
        sample_followers = [followers[i] for i in random.sample(xrange(len(followers)),sample_size)]

        with open(domains_path,'w') as f :
            seed_to_urls2(api,f,sample_followers)
            exit()

    else :
        urls = []
        with open(domains_path,'r') as f :
            for line in f :
                if line != '' :
                    url = line.strip()
                    urls.append(url)

    if not os.path.isfile(resolved_path) :
        print 'Computing domains...'
        domains = {}
        i = 0
        already_resolved = {}
        with open(resolved_path,'w') as f :
            for url in urls :
                print '{}/{}'.format(str(i),str(len(urls)))
                if url in already_resolved :
                    resolved = already_resolved[url]
                else :
                    try :
                        resolved = resolve(url)
                        already_resolved[url] = resolved
                    except Exception :
                        continue
                
                f.write(resolved + '\n')
                i += 1

                dom = resolved.partition('://')[-1].partition('/')[0]
                if dom in domains :
                    domains[dom] += 1
                else :
                    domains[dom] = 1
                    
            domains = sorted(domains.items(),key=lambda x : x[1],reverse = True)
            with open('ranked_domains_{}.txt'.format(username),'w') as f :
                for d,c in domains :
                    f.write( '{},{}\n'.format(d,str(c)) )

    

    













