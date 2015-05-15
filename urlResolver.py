import json
import requests
from threading import Thread
from Queue import Queue

def resolve(shortener,max_redirects=5,timeout=5) :
    session = requests.session()
    r = session.get(shortener, allow_redirects=False, timeout=timeout)
    resolved = r.url
    red_count = 0
    for redirect in session.resolve_redirects(r, r.request, timeout=timeout):
        red_count += 1
        resolved = redirect.url
        if red_count >= max_redirects :
            break
    return resolved


if __name__ == '__main__' :
    
    from sys import argv
    
    output_path = argv[1]
    n_threads = int(argv[2])
    
    chunk_size = 1000
    previously_resolved = set()
    try :
        with open(output_path,'r') as f :
            for line in f :
                try :
                    k,_ = line.strip().split(',')
                    previously_resolved.add(k)
                except ValueError :
                    continue
    except IOError :
        pass
    
    urls = set()    
    t_path = lambda x : './data/tweets_{}.json'.format(str(x))
    for x in xrange(10) :
        try :
            with open(t_path(x),'r') as f :
                print "Reading",t_path(x)
                for line in f :
                    try :
                        t = json.loads(line)
                    except ValueError :
                        continue
                    if 'entities' in t and 'urls' in t['entities'] :
                        for u in t['entities']['urls'] :
                            exurl = u['expanded_url']
                            if not exurl in previously_resolved :
                                urls.add( exurl )
        except IOError :
            continue


    # filter with shortener domain list            
    with open('shorturls.txt','r') as f :
        s_domains = set()
        for line in f :
            if line != '' :
                s_domains.add( line.strip() )

    with open(output_path,'a') as f :

        to_resolve = []

        for url in urls :
            domain = url.partition('//')[-1].partition('/')[0]
            if domain in s_domains :
                to_resolve.append( url )


            else :
                try :
                    f.write('{},{}\n'.format(url,url))
                except Exception :
                    continue

        def worker(in_queue,out_queue):
            while True :
                url = in_queue.get()
                try :
                    rurl = resolve(url)
                    out_queue.put((url,rurl))
                except Exception :
                    pass
                in_queue.task_done()

        tcount = len(to_resolve)
        while len(to_resolve) > 0 :

            print "Left: {}/{}".format(str(len(to_resolve)),str(tcount))

            in_queue = Queue()
            out_queue = Queue()

            for _ in xrange(chunk_size) :
                try :
                    url = to_resolve.pop()
                    in_queue.put( url )
                except IndexError :
                    break


            for i in range(n_threads):
                t = Thread(target=worker,args=(in_queue,out_queue))
                t.daemon = True
                t.start()
        
            try:
                print "Waiting for the workers to finish"
                in_queue.join()
                print "Workers finished crunching"
            except KeyboardInterrupt :
                exit()

            while not out_queue.empty() :
                k,v = out_queue.get()
                try :
                    f.write('{},{}\n'.format(k,v))
                except Exception :
                    continue
        

            

    
