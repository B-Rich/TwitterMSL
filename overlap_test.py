import datetime
import json

tweets = []
starting_date = datetime.date(2015,5,7)
resolved_path = 'resolved.csv'

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
    pass

with open(resolved_path,'a') as fres :
    for i in xrange(10) :
        try :
            with open('data/tweets_{}.json'.format(str(i)),'r') as f :
                for line in f :
                    try :
                        t = json.loads(line)
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
                                    rurl = resolve(url)
                                except Exception :
                                    continue
                                fres.write('{},{}\n'.format(url,rurl))
                                resolved[url] = rurl

                            t2 = {'day' : day, 'user' : user, 'url': rurl}
                            tweets.append(t2)

                    except ValueError :
                        continue
        except IOError :
            continue


users_days = {}
days_users = {}
days_urls_users = {}

for t in tweets :
    user = t['user']
    day = t['day']
    url = t['url']

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

print "act.days,n.users"
for x,y in activity :
    print '{},{}'.format(str(x),str(y))


print '------------------------------'

print "day,shares,n.links"
for i,day in enumerate(sorted(days_urls_users.keys())) :
    lens = [len(d) for u,d in days_urls_users[day].items()]
    activity = sorted([(n,lens.count(n)) for n in set(lens)])

    for x,y in activity :
        print '{},{},{}'.format(str(i),str(x),str(y))


print '------------------------------'
s_days = sorted(days_users.keys())

print "days,score"
for i in xrange(1,len(s_days)) :


    d1 = s_days[i-1]
    d2 = s_days[i]
    u1 = days_users[d1]
    u2 = days_users[d2]
    
    intrs = u1.intersection(u2)

    score = len(intrs) / float(min([len(u1),len(u2)]))

    print '{},{}'.format(str(i),str(score))
    










