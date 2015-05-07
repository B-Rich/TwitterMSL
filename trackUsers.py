
from TwitterAPI import TwitterAPI,TwitterError

import os,time,json


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
            self.current_index = 0
            self.create()
        else :

            files.sort(key=lambda x : x[0])
            self.current_index = files[-1][0]
            last_path = os.path.join(self.folder,files[-1][1])
            
            with open(last_path,'r') as f :
                last_length = len(f.read().strip().split('\n'))

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
            self.current_file.close()
            self.create()

    def close(self) :
        self.current_file.close()



def trackUsers(api,users,output_folder) :

    t_files = TweetsFiles(output_folder)
    
    last_tweet = { u : None for u in users }                    
    tweets = []
    i = 0
    tcount = 0
    itercount = 0
    while True :

        users100 = [users[j] for j in xrange(i,i+100)]
        i += 100

        if i >= len(seed_users) :
            itercount += 1
            i = 0
        
        response = api.request('users/lookup', {'user_id' : users100, 'include_entities' : 'true'})


        try :
            for x in response:                    
                u = x['user_id']
                if 'status' in x  and 'entities' in x['status'] and 'urls' in x['status']['entities'] :
                    t = x['status']
                    if last_tweet[u] == None or last_tweet[u] != t :
                        # add tweet
                        last_tweet[u] = t
                        tweets.append(t)
                        tcount += 1

        except TwitterError.TwitterRequestError as e :
            
            for t in tweets :
                try :
                    t_files.write( json.dumps(t) )
                except UnicodeEncodeError :
                    continue
            tweets = []
            print 'Iteration:',itercount
            print 'Tweets stored:',tcount
            print 'Zzz'
            time.sleep(60 * 16)


if __name__ == '__main__' :

    from sys import argv

    users_path = argv[1]

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
    tweets_folder = config_params['tweets_folder']
    tweets_folder_abs = project_folder + tweets_folder

    api = TwitterAPI(c1,c2,c3,c4)

    users = set()
    with open(users_path,'r') as f :
        for line in f :
            try :
                uid = int(line.strip())
                users.add(uid)
            except ValueError :
                continue
    users = list(users)

    trackUsers(api,users,tweets_folder_abs)
