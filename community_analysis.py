import json
import string
import os
import re


from gensim import corpora,models



class KeywordExtractor :

    def __init__(self,punctuation='',stopwords=[]) :
        self.punctuation = punctuation
        self.stopwords = stopwords

    def preprocess(self,document,remove_urls=True) :
        # convert to lowercase
        lower_doc = document.lower()


        if remove_urls :
            pattern = r'http[\S]+'
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

    community_path = argv[1]
    output_path = argv[2]
    path = lambda i : './data/tweets_{}.json'.format(str(i))

    with open(community_path,'r') as f :
        communities = json.loads(f.read())

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
                    tweets.add( (user,text) )
                  
        except IOError :
            continue

    with open('stopwords.txt') as f :
        stopwords = []
        for line in f :
            s = line.strip()
            if len(s) > 0 : 
                stopwords.append( s )


    user_text = {}
    for user,text in tweets :
        if user in user_text :
            user_text[user] += ' ' + text
        else :
            user_text[user] = text

    ke = KeywordExtractor(punctuation = string.punctuation, stopwords = stopwords)
    ke.train_model( user_text.values() )

    with open(output_path,'w') as f :
        results = []
        for community in communities :

            c_size = len(community)

            kws = {}
            for user in community :
                doc = user_text[user]

                for k,v in ke.keywords(doc) :
                    if k in kws :
                        kws[k] += v
                    else :
                        kws[k] = v
            
            if len(kws) == 0 :
                continue


            scores = kws.values()
            avg_score = sum(scores) / float(len(scores))
            just_words = map(lambda x : x[0],sorted(kws.items(),key=lambda x : x[1],reverse=True))

            results.append( (avg_score,c_size,just_words[:10]) )

        results.sort(key = lambda x : x[0], reverse = True)

        for _,size,just_words in results :
            f.write( str(size) + ' : ' )
            for w in just_words :
                try :
                    f.write(w + ' ')
                except UnicodeEncodeError :
                    continue
            f.write('\n')

