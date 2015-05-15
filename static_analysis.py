import json
import string
import os
from subprocess import call
import networkx as nx
import numpy as np
import scipy


if __name__ == '__main__' :

    from sys import argv

    resolved_path = argv[1]
    output_path = argv[2]
    temp_name = 'booh'
    overlapping = False
    path = lambda i : './data/tweets_{}.json'.format(str(i))

    with open(resolved_path,'r') as f :
        resolved = {}
        for line in f :
            try :
                k,v = line.strip().split(',')
            except ValueError :
                continue
            resolved[k] = v

    print "------------------------------"
    print "Loading tweets.json"
    print "------------------------------"

    tweets = set()

    for i in xrange(100) :
        try :
            with open(path(i),'r') as f :
                for line in f :
                    try :
                        t = json.loads(line)
                    except ValueError :
                        continue
                    user = t['user_id']
                    text = t['text']
                    if 'entities' in t and 'urls' in t['entities'] :
                        for x in t['entities']['urls'] :
                            url = x['expanded_url']
                            if not url in resolved :
                                continue
                            rurl = resolved[url]
                            tweets.add( (user,rurl,text) )
                            
        except IOError :
            continue

    print 'Prefiltering:'
    print 'N.Tweets:',len(tweets)
    print 'N.Users:',len({u for u,_,_ in tweets})
    print 'N.Urls:',len({u for _,u,_ in tweets})

    one_time = set()
    more_than_once = set()
    for _,url,_ in tweets :
        if not (url in one_time or url in more_than_once) :
            one_time.add( url )
        elif url in one_time :
            one_time.remove( url )
            more_than_once.add( url )

    filtered_tweets = {(user,url,text) for user,url,text in tweets if not url in one_time}
    tweets = filtered_tweets
    print 'Postfiltering:'
    print 'N.Tweets:',len(tweets)
    print 'N.Users:',len({u for u,_,_ in tweets})
    print 'N.Urls:',len({u for _,u,_ in tweets})

    print "------------------------------"
    print "Computing the User-User graph from tweets"
    print "------------------------------"

    G = nx.Graph()

    for user,link,_ in tweets :
        G.add_node(user, bipartite = 0)
        G.add_node(link,bipartite = 1)
        G.add_edge(user,link)

    user_nodes = [n for n,d in G.nodes(data=True) if d['bipartite'] == 0]

    A = nx.algorithms.bipartite.basic.biadjacency_matrix(G,user_nodes,dtype=np.float)

    # change representation to sparse CSR matrix
    A = scipy.sparse.csr_matrix(A)

    # normalize A (each row sums to one)
    S = np.array( [1./r.sum() for r in A]); 
    D = scipy.sparse.csr_matrix(np.diag(S))
    Norm_A = D.dot(A)

    # calculate the User-User matrix
    U = (Norm_A.dot(Norm_A.T)).todense()

    # remove self-loops
    np.fill_diagonal(U,0.0)

    # back again to a User-User graph
    UU = nx.from_numpy_matrix(U)

    mapping = dict(enumerate(user_nodes))
    UU = nx.relabel_nodes(UU,mapping,copy=False)
    
    print "------------------------------"
    print "Infomap"
    print "------------------------------"

    # export the graph in a temporary .pajek file
    nx.write_pajek(UU,'./temp/{}.net'.format(temp_name))

    # run Infomap
    with open(os.devnull, "w") as fnull:

        if overlapping :
            call(['Infomap/Infomap','-ipajek','--clu','--overlapping','./temp/{}.net'.format(temp_name),'temp'],stdout=fnull)
        else :
            call(['Infomap/Infomap','-ipajek','--clu','./temp/{}.net'.format(temp_name),'temp'],stdout=fnull)

    nodes_to_communities = []
    with open('./temp/{}.clu'.format(temp_name),'r') as f :
        for line in f :
            try :
                community = int(line)
                
            except ValueError :
                continue

            nodes_to_communities.append(community)

    node_names = UU.nodes()
    n_to_c = dict( [(node_names[i],c) for i,c in enumerate(nodes_to_communities)] )

    # convert dict to list of list
    c_to_n = {}
    for n,c in n_to_c.items() :
        if c in c_to_n :
            c_to_n[c].append(n)
        else :
            c_to_n[c] = [n]
                
    user_communities = c_to_n.values()
    
    with open(output_path,'w') as f :
        f.write(json.dumps(user_communities))
