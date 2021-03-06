import json
import string
import os
import re

from datetime import date,datetime

from gensim import corpora,models
from dynamicTracker import DynamicTracker


class KeywordExtractor :

    def __init__(self,punctuation='',stopwords=[]) :
        self.punctuation = punctuation
        self.stopwords = stopwords

    def preprocess(self,document,remove_urls=True,remove_usernames=True) :
        # convert to lowercase
        lower_doc = document.lower()


        if remove_urls :
            pattern = r'http[\S]+'
            lower_doc = re.sub(pattern,'',lower_doc)

        if remove_usernames :
            pattern = r'@[\S]+'
            lower_doc = re.sub(pattern,'',lower_doc)

        # remove punctuation
        no_p_doc = lower_doc
        for p in self.punctuation :
            no_p_doc = no_p_doc.replace(p,' ')

        # tokenize
        tokens = no_p_doc.split()

        # remove stopwords
        tokens = [t for t in tokens if t not in self.stopwords]

        return tokens

    def train_model(self,training_set) :

        # preprocess the documents
        preprocessed = [self.preprocess(d) for d in training_set]
        
        # extract a token dictionary
        self.dictionary = corpora.Dictionary(preprocessed)

        # convert the preprocessed documents into index vectors
        corpus = [self.dictionary.doc2bow(d) for d in preprocessed]

        # initialize the TFIDF model
        self.tfidf = models.TfidfModel(corpus)


    def keywords(self,document) :

        bow_vec = self.dictionary.doc2bow(self.preprocess(document))
        tfidf_vec = sorted(self.tfidf[bow_vec],key=lambda x : x[1],reverse=True)
        kw_vec = [(self.dictionary[k],v) for k,v in tfidf_vec]

        return kw_vec


if __name__ == '__main__' :

    from sys import argv

    try :
        community_path = argv[1]
        output_path = argv[2]
        threshold = float(argv[3])
        expiration = int(argv[4])
    except IndexError :
        print "input_path output_path threshold expiration"
        exit(1)

    path = lambda i : './data/tweets_{}.json'.format(str(i))

    with open(community_path,'r') as f :
        communities = json.loads(f.read())

    days = []
    for key in communities :
        year,month,day = map(int,key.strip().split('-'))
        days.append( date(year,month,day) )

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
                    day = datetime.strptime(t['created_at'], '%a %b %d %H:%M:%S +0000 %Y').date()

                    if day not in days :
                        continue
                    if 'entities' in t and 'urls' in t['entities'] :
                        for x in t['entities']['urls'] :
                            url = x['expanded_url']
                            tweets.add( (user,text,url,day) )
                  
        except IOError :
            continue

    with open('stopwords.txt') as f :
        stopwords = []
        for line in f :
            s = line.strip()
            if len(s) > 0 : 
                stopwords.append( s )


    one_time = set()
    more_than_once = set()
    for _,_,url,_ in tweets :
        if not (url in one_time or url in more_than_once) :
            one_time.add( url )
        elif url in one_time :
            one_time.remove( url )
            more_than_once.add( url )

    filtered_tweets = {(user,text,url,day) for user,text,url,day in tweets if not url in one_time}
    tweets = filtered_tweets


    user_text = {}
    for user,text in {(u,t) for u,t,_,_ in tweets} :
        if user in user_text :
            user_text[user] += ' ' + text
        else :
            user_text[user] = text

    ke = KeywordExtractor(punctuation = string.punctuation.replace('#',''), stopwords = stopwords)
    ke.train_model( user_text.values() )

    
    dt = DynamicTracker(threshold,expiration)
    dt.similarity = DynamicTracker.user_similarity

    print "Tracking.."
    for day in sorted(days) :
        day_str = '{}-{}-{}'.format(str(day.year),('0' if day.month < 10 else '') + str(day.month),str(day.day))
        print day_str
        step = []
        for com in communities[day_str] :
            step.append( {'users' : com} )

        dt.nextStep( step )
        
        

    with open(output_path,'w') as f :
        results = []
    
        for nd,d in enumerate(dt.D) :

            if len(d) < 2 :
                continue 
            print "{}/{}".format(str(nd),str(len(dt.D)))
            users = set()
            for x,y,_ in d :
                for u in dt.C[x][y]['users'] :
                    users.add( u )

            c_size = len(d)

            kws = {}
            for user in users :
                if user in user_text :
                    doc = user_text[user]

                    for k,v in ke.keywords(doc) :
                        if k in kws :
                            kws[k] += v
                        else :
                            kws[k] = v
            
            if len(kws) == 0 :
                print "Fuuu"
                continue

            score = c_size                     
            just_words = map(lambda x : x[0],sorted(kws.items(),key=lambda x : x[1],reverse=True))
            results.append( (score,c_size,just_words[:10]) )
        
        results.sort(key = lambda x : x[0], reverse = True)
        print "RESULTS!",len(results)
                      
        for _,size,just_words in results :
            f.write( str(size) + ' : ' )
            for w in just_words :
                try :
                    f.write(w + ' ')
                except UnicodeEncodeError :
                    continue
            f.write('\n')

