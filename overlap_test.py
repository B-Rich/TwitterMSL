import datetime
import json
import requests

def resolve(shortener) :
    r = requests.get(shortener)
    return r.url


tweets = set()
starting_date = datetime.date(2015,5,7)
resolved_path = 'resolved.csv'
output_path = 'overlap.csv'

resolve_urls = False


if resolve_urls :
    resolved = {}
    try :
        with open(resolved_path,'r') as f :
            for line in f :
                try :
                    k,v = line.strip().split(',')
                except ValueError :
                    continue
                resolved[k] = v
    except IOError :
        print "No resolved URLs file found"


    with open(resolved_path,'a') as fres :
        for i in xrange(10) :
            try :
                with open('data/tweets_{}.json'.format(str(i)),'r') as f :
                    print 'Parsing: data/tweets_{}.json'.format(str(i))
                    for line in f :
                        try :
                            t = json.loads(line)
                        except ValueError :
                            continue
                        day = datetime.datetime.strptime(t['created_at'], '%a %b %d %H:%M:%S +0000 %Y').date()
                        if day < starting_date :
                            continue
                        user = t['user_id']
                        for x in t['entities']['urls'] :
                            url = x['expanded_url']
                            if url in resolved :
                                rurl = resolved[url]
                            else :
                                try :
                                    print '.',
                                    rurl = resolve(url)
                                except Exception :
                                    print "couldn't resolve:",url
                                    continue
                                fres.write('{},{}\n'.format(url,rurl))
                                resolved[url] = rurl

                            t2 = (day, user, rurl)
                            tweets.add(t2)

                    print

            except IOError :
                continue

else :
    for i in xrange(10) :
        try :
            with open('data/tweets_{}.json'.format(str(i)),'r') as f :
                print 'Parsing: data/tweets_{}.json'.format(str(i))
                for line in f :
                    try :
                        t = json.loads(line)
                    except ValueError :
                        continue
                    day = datetime.datetime.strptime(t['created_at'], '%a %b %d %H:%M:%S +0000 %Y').date()
                    if day < starting_date :
                        continue
                    user = t['user_id']
                    for x in t['entities']['urls'] :
                        url = x['expanded_url']
                        t2 = (day, user, url)
                        tweets.add(t2)                    

        except IOError :
            continue

print 'Computing statistics'

with open(output_path,'w') as f :
    users_days = {}
    days_users = {}
    days_urls_users = {}

    for t in tweets :
        day,user,url = t

        if not user in users_days :
            users_days[user] = set()
        users_days[user].add( day )

        if not day in days_users :
            days_users[day] = set()
        days_users[day].add( user )

        if not day in days_urls_users :
            days_urls_users[day] = {}
        if not url in days_urls_users[day] :
            days_urls_users[day][url] = set()
        days_urls_users[day][url].add( user )
    

    lens = [len(d) for u,d in users_days.items()]
    activity = sorted([(n,lens.count(n)) for n in set(lens)])

    f.write("act.days,n.users\n")
    for x,y in activity :
        f.write('{},{}\n'.format(str(x),str(y)))


    f.write('------------------------------\n')

    f.write("day,shares,n.links\n")
    for i,day in enumerate(sorted(days_urls_users.keys())) :
        lens = [len(d) for u,d in days_urls_users[day].items()]
        activity = sorted([(n,lens.count(n)) for n in set(lens)])

        for x,y in activity :
            f.write('{},{},{}\n'.format(str(i),str(x),str(y)))


    f.write('------------------------------\n')
    s_days = sorted(days_users.keys())

    f.write("days,score\n")
    for i in xrange(1,len(s_days)) :
        d1 = s_days[i-1]
        d2 = s_days[i]
        u1 = days_users[d1]
        u2 = days_users[d2]
    
        score1 = len(u1.intersection(u2)) / float(len(u1.union(u2)))
        score2 = len(u1.intersection(u2)) / float(min([len(u1),len(u2)]))


        f.write('{},{},{}\n'.format(str(i),str(score1),str(score2)))
    










