import pickle

class DynamicTracker :

    @staticmethod
    def load(path) :
        with open(path,'rb') as f :
            content = pickle.load(f)
            dt = DynamicTracker(1.0,1)
         
            dt.threshold = content[0]
            dt.expiration = content[1]
            dt.D = content[2]
            dt.C = content[3]
            dt.frontier = content[4]
            dt.step = content[5]

            return dt

    @staticmethod
    def save(dt,path) :
        content = (
            dt.threshold,
            dt.expiration,
            dt.D,
            dt.C,
            dt.frontier,
            dt.step
        )
        with open(path,'wb') as f :
            pickle.dump(content,f)    
                        

    def __init__(self,threshold,expiration) :
        self.threshold = threshold
        self.expiration = expiration

        self.D = []
        self.C = []
        self.frontier = None
        self.step = -1

    @staticmethod
    def news_similarity(c1,c2) :
        stories1 = map(lambda x : x[0],c1['news'])
        stories2 = map(lambda x : x[0],c2['news'])
        return DynamicTracker.average_jaccard(stories1,stories2)

    @staticmethod
    def user_similarity(c1,c2) :
        users1 = c1['users']
        users2 = c2['users']
        return DynamicTracker.jaccard(users1,users2)


    @staticmethod
    def topic_similarity(c1,c2) :
        keywords1 = map(lambda x : x[0],c1['keywords'])
        keywords2 = map(lambda x : x[0],c2['keywords'])

        return DynamicTracker.average_jaccard(keywords1,keywords2)

    @staticmethod
    def jaccard(l1,l2) :
        '''
        Computes the standard Jaccard similarity between two lists of elements.
        Returns a float.

        '''
        s1 = set(l1)
        s2 = set(l2)
        return len(s1.intersection(s2)) / float( len(s1.union(s2)) )

    @staticmethod
    def average_jaccard(l1,l2) :
        '''
        Computes the Average Jaccard similarity between two ordered lists of elements.
        Returns a float.

        '''
        s = min(len(l1),len(l2))
        return sum([DynamicTracker.jaccard(l1[:i],l2[:i]) for i in xrange(1,1+s)]) / float(s)

    def significances(self) :
        '''
        Computes the significance of each dynamic community.
        Returns a list of tuples [(index,significance)].

        '''
        result = []

        for d in xrange(len(self.D)) :
            similarity_sum = sum(map(lambda (x,y,z) : z, self.D[d]))
            sig = similarity_sum / self.step
            result.append( (d,sig) )
        
        return result

    def stabilities(self) :

        result = []
        for index,dc in enumerate(self.D) :

            if len(dc) < 2 :
                continue

            dc_steps = [self.C[x][y]['users'] for x,y,_ in dc]
            dc_users = { u for step in dc_steps for u in step }
            dc_len = len(dc)

            user_counts = { u : 0 for u in dc_users}
            for u in dc_users :
                for step in dc_steps :
                    if u in step :
                        user_counts[u] += 1
            pis = []
            for i in xrange(1,1+dc_len) :
                pi = len([u for u,c in user_counts.items() if c >= i]) / float(len(user_counts))
                pis.append(pi)

            stability = sum(pis)/len(pis)
            result.append( (index,stability,pis) )
        return result

    def exclusivity(self) :

        ex = []
        for step_communities in self.C :
            
            gamma = {}
            for i,sc in enumerate(step_communities) :
                for u in set(sc['users']) :
                    gamma[(u,i)] = sc['users'].count(u) / float(len(sc['news']))

            ex.append([])
            for i,sc in enumerate(step_communities) :
                ex_i = 0.0
                for u in set(sc['users']) :
                    ex_i += (gamma[(u,i)] / sum([gamma[(x,j)] for x,j in gamma if x == u]))

                ex_i /= len(set(sc['users']))
                ex[-1].append(ex_i)

        return ex

                

            
            

    def DCG(self,weight=False) :
        '''
        Returns the DAG of the dynamic communities, represented as a list of edges.
        Each node is a tuple (time step,step community index).
        If weight is True, each edge is a triple with similarity value between step community as
        weight.

        '''
        edges = []
        for d in self.D :
            for i in xrange(0,len(d) - 1) :
                n1 = (d[i][0],d[i][1])
                n2 = (d[i+1][0],d[i+1][1])
                edge = (n1,n2,d[i+1][2]) if weight else (n1,n2)
                edges.append( edge )

        return edges
            


    def nextStep(self,communities) :
        '''
        Adds another step of dynamic community tracking, given a list of step communities.
        Each community in the list is represented as a list of tuples (element,weight).
        Returns None.

        '''        
        self.C.append(communities)
        self.step += 1

        if self.D == [] :
            
            # first step. initialize the frontier with the communities
            self.frontier = set()
            for i,c in enumerate(self.C[0]) :
                self.D.append( [(0,i,0)] )
                self.frontier.add(i)

        else :

            # look for expired dynamic communities
            for i in list(self.frontier) :
                last_step = self.D[i][-1][0]
                if (self.step - last_step) > self.expiration :
                    self.frontier.remove(i)

            # match the dynamic communities with the last step communities
            matches = {}

            new_dynamic_communities = set()
            for i,c in enumerate(self.C[-1]) :
                matched = False
                for j in self.frontier :
                    x,y,_ = self.D[j][-1]
                    d = self.C[x][y]                    
                    sim = self.similarity( d,c )
                    if sim > self.threshold :

                        if j in matches :
                            matches[j].append( (i, sim) )
                        else :
                            matches[j] = [(i, sim)]

                        matched = True

                if not matched :
                    new_id = len(self.D)
                    ptr = (self.step,i,0)
                    new_D = [ ptr ]
                    self.D.append( new_D )
                    new_dynamic_communities.add(new_id)

            self.frontier = self.frontier.union(new_dynamic_communities)

            for j,ml in matches.items() :
                if len(ml) > 0 :
                    i,sim = ml[0]
                    ptr = (self.step,i,sim)
                    self.D[j].append(ptr)
                    
                    for k in xrange(1,len(ml)) :
                        i,sim = ml[k]
                        ptr = (self.step,i,sim)
                        new_D = list(self.D[j][:-1])
                        new_D.append( ptr )
                        self.D.append( new_D )
                        self.frontier.add(len(self.D) - 1)
