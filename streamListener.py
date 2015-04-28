
import requests
import json
import os

from TwitterAPI import TwitterAPI,TwitterError


class TweetsFiles :

    # ../tweets_N.json
    DEF_EXT = 'json'
    DEF_NAME = 'tweets'
    DEF_FILE_LIMIT = 100000

    def __init__(self,folder,limit=DEF_FILE_LIMIT,ext=DEF_EXT,name=DEF_NAME) :
        self.folder = folder
        self.limit = limit
        self.ext = ext
        self.file_name = name

        files = []
        for f in os.listdir(folder) :
            path = os.path.join(folder,f)
            if os.path.isfile( path ) :
                filename,_,extension = f.partition('.')
                if extension != self.ext :
                    continue
                name,_,index = filename.partition('_')
                if name != self.file_name :
                    continue
                files.append( (int(index),path) )
        
        if len(files) == 0 :
            print 'init: no files'
            self.current_index = 0
            self.create()
        else :

            files.sort(key=lambda x : x[0])
            self.current_index = files[-1][0]
            last_path = os.path.join(self.folder,files[-1][1])
            
            with open(last_path,'r') as f :
                last_length = len(f.read().strip().split('\n'))

            print 'init: last file',last_path,'len',last_length
            if last_length >= self.limit :               
                self.create()
            else :
                # READY
                self.current_size = last_length
                self.current_file = open(last_path,'a')
    
    def create(self) :
        new_index = self.current_index + 1
        new_filename = '{}_{}.{}'.format(self.file_name,str(new_index),self.ext)
        new_path = os.path.join( self.folder, new_filename )
        print 'creating new file:',new_path
        with open(new_path,'w') as f :
            pass

        # READY
        self.current_file = open(new_path,'a')
        self.current_index = new_index
        self.current_size = 0

    def write(self,data) :
        self.current_file.write(data + '\n')
        self.current_size += 1

        if self.current_size >= self.limit :
            print 'limit reached:',self.current_index,self.current_size
            self.current_file.close()
            self.create()

    def close(self) :
        self.current_file.close()

def listener(c1,c2,c3,c4,query,tweets_folder,max_errors) :

    api = TwitterAPI(c1,c2,c3,c4)
    tweets_files = TweetsFiles(tweets_folder)

    err_count = 0

    while err_count < max_errors :
        r = api.request('statuses/filter', {'track':query})
    
        try :        
            for tweet in r:
                if not 'user' in tweet :
                    continue
                
                if not 'entities' in tweet or not 'urls' in tweet['entities'] or len(tweet['entities']['urls']) == 0 :                   
                    continue
                
                tweets_files.write( json.dumps(tweet) )

        except Exception as e :
            print str(e)
            print 'Error count:',err_count
            err_count += 1
            
    tweets_files.close()
                


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
    query = config_params['query']
    max_errors = config_params['max_errors']
    tweets_folder = config_params['tweets_folder']
    tweets_folder_abs = project_folder + tweets_folder
    listener(c1,c2,c3,c4,query,tweets_folder_abs,max_errors)
    


