
from sys import argv

path = argv[1]

domains = {}
with open(path,'r') as f :
    for line in f :
        try :
            _,url = line.strip().split(',')
        except ValueError :
            continue

        if 'www.' in url :
            url = url.replace('www.','')
        dom = url.partition('//')[-1].partition('/')[0]
        if dom in domains :
            domains[dom] += 1
        else :
            domains[dom] = 1

ranked = sorted(domains.items(),key = lambda x : x[1], reverse = True)
for d,c, in ranked[:100] :
    print '{},{}'.format(str(d),str(c))
