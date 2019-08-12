'''
    the Flask server
    Muyang Shi, 6/24/2019
'''

import sys
import json
import ast
import flask
import random
import csv
from flask_util_js import FlaskUtilJs
from Configures import test_length_config as config
# import config
import psycopg2

app = flask.Flask(__name__)
fujs = FlaskUtilJs(app)

def get_connection():
	'''
	Returns a connection to the database described
	in the config module. Returns None if the
	connection attempt fails.
	'''
	connection = None
	try:
		connection = psycopg2.connect(host='localhost',
                                      database='fontsize',
									  user='fontsize',
									  password='wordcloudsbad?')
	except Exception as e:
		print(e, file=sys.stderr)
	return connection



# Get and render web pages
##########################################################################################################################################################################################################################
@app.after_request
def set_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/')
def get_hello_page():
	return flask.redirect(flask.url_for('get_landing_page'))

@app.route('/word_cognition_study')
def get_landing_page():
    return flask.render_template('landing.html')

# Get the description page, with turker_id as the data passed from HTML form from landing page
@app.route('/word_cognition_study/description', methods = ['POST'])
def get_description():
    turker_id = flask.request.form['turker_id']
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT turker_id FROM turker WHERE turker_id = %s",(turker_id,))
    existance = len(cursor.fetchall())
    print(cursor,type(cursor),existance,type(existance))
    connection.commit()
    cursor.close()
    connection.close()
    # id_list = ['1','2','3','4','5']
    participant = 'new'
    if existance != 1:
        participant = 'tested'
    return flask.render_template('description.html', ID = turker_id, Participant = participant)

# Get the description page; turker_id is passed from description page through HTML form
@app.route('/word_cognition_study/stimuli', methods = ['POST'])
def get_stimuli_page():
    turker_id = flask.request.form['turker_id']
    # print(turker_id)
    return flask.render_template('stimuli.html', ID = turker_id, List_From_Server=get_tasklist())

@app.route('/word_cognition_study/completion', methods=['POST'])
def get_completion():
    data = flask.request.form
    turker_id = data['turker_id']
    hash_code = hash(data['turker_id'] + 'Carleton')
    # print(hash_code,type(hash_code))
    return flask.render_template('completion.html', ID = turker_id, Hash_Code = hash_code)
##########################################################################################################################################################################################################################




# Send information from server py to frontend JS
##########################################################################################################################################################################################################################
# Get the tasklist from test_length_config.py, the tasklist is from test_length.csv
# The format of the tasklist is 
# [{'target_1_fontsize':int,'target_1_length':int,'target_2_fontsize':int,'target_2_length':int},{},{},...]
def get_tasklist():
    tasklist = config.tasklist
    return json.dumps(tasklist)

@app.route('/getStim/<target_1_fontsize>/<target_1_length>/<target_2_fontsize>/<target_2_length>')
def getStim(target_1_fontsize,target_1_length,target_2_fontsize,target_2_length, word = config.word): # word = config.experiment
    if word == 'pseudoword':
        return get_pseudo_stimuli(int(config.numberOfWords),{'length':int(target_1_length), 'fontsize':int(target_1_fontsize)}, {'length':int(target_2_length),'fontsize':int(target_2_fontsize)})
    if word == 'english':
        return get_english_stimuli(int(config.numberOfWords),{'length':int(target_1_length), 'fontsize':int(target_1_fontsize)}, {'length':int(target_2_length),'fontsize':int(target_2_fontsize)})

# No adescenders, pseudoword
def pseudoword(size = 5, charset = "weruosazxcvnm"):
    return ''.join(random.choice(charset) for _ in range(size))
def get_pseudo_stimuli(numberOfWords, target1, target2):
    words = []
    target_words = []
    distractor_words = []

    target_word_1 = {'text': pseudoword(size = target1['length']), 'fontsize': target1['fontsize'], 'html': 'target'}
    target_word_2 = {'text': pseudoword(size = target2['length']), 'fontsize': target2['fontsize'], 'html': 'target'}
    target_words.append(target_word_1)
    target_words.append(target_word_2)

    for i in range(int(numberOfWords) - 2):
        distractor = {'text': pseudoword(size = random.randint(config.minLen,config.maxLen)), 'fontsize': random.randint(config.minSize,config.maxSize), 'html': 'distractor'}
        distractor_words.append(distractor)

    return json.dumps(target_words + distractor_words)

# No adescenders, english words
def get_legit_word(wordlist,minLen,maxLen):
    legit_word_list = []
    adescenders = r"qtyiplkjhgfdb"
    for word in wordlist:
        if not any(char in word for char in adescenders):
            if not (len(word) < minLen or len(word) > maxLen):
                legit_word_list.append(word)
    return legit_word_list
def get_english_stimuli(numberOfWords, target1, target2):
    legit_words = get_legit_word(decent_word_list,config.minLen,config.maxLen)
    target_words = []
    distractor_words = []

    target1_text = ''
    while True:
        target1_text = random.choice(legit_words)
        if(len(target1_text) == target1['length']):
            legit_words.remove(target1_text)
            break
    
    target2_text = ''
    while True:
        target2_text = random.choice(legit_words)
        if(len(target2_text) == target2['length']):
            legit_words.remove(target2_text)
            break

    target_word_1 = {'text': target1_text, 'fontsize': target1['fontsize'], 'html': 'target'}
    target_word_2 = {'text': target2_text, 'fontsize': target2['fontsize'], 'html': 'target'}
    target_words.append(target_word_1)
    target_words.append(target_word_2)

    for i in range(int(numberOfWords) - 2):
        distractor = {'text': random.choice(legit_words), 'fontsize': random.randint(config.minSize,config.maxSize), 'html': 'distractor'}
        distractor_words.append(distractor)

    return json.dumps(target_words + distractor_words)

# Used for hypo2
# Specifications about the length of targets, fontsize of the correct and wrong, and the number of words
# are passed from the frontend to the server
# the specifications from the frontend are from tasklist.csv (test_length.csv)
@app.route('/getMultiTargets/<numberOfTargets>/<correct_fontsize>/<wrong_fontsize>/<word_length>')
def getMultiTargets(numberOfTargets,correct_fontsize,wrong_fontsize,word_length):
    legit_words = get_legit_word(decent_word_list,int(word_length),int(word_length))
    target_words = []
    for i in range(int(numberOfTargets)):
        correct_target = random.choice(legit_words)
        legit_words.remove(correct_target)
        target_words.append(correct_target)
    print(target_words)
    
    for i in range(int(numberOfTargets)):
        if i == 0:
            target_words[i] = {'text': target_words[i], 'fontsize': correct_fontsize, 'html': 'target'}
        else:
            target_words[i] = {'text': target_words[i], 'fontsize': wrong_fontsize, 'html': 'target'}
    print(target_words)
    return json.dumps(target_words)

# Used for hypo2
# Specifications about word length, fontsize, and number of distractors
# are found in the config file
# no parameters are needed from the frontend
# return a list of words in dictionary to the front end
@app.route('/getDistractors')
def getDistractors():
    legit_words = get_legit_word(decent_word_list,config.minLen,config.maxLen)
    distractor_words = []
    for i in range(int(config.numberOfWords)):
        distractor = {'text': random.choice(legit_words), 'fontsize': random.randint(config.minSize,config.maxSize), 'html': 'distractor'}
        distractor_words.append(distractor)
    return json.dumps(distractor_words)
##########################################################################################################################################################################################################################




# Write data to csvfile/database
##########################################################################################################################################################################################################################
# Write the turker's id into a csvfile --> client_id.csv
@app.route('/word_cognition_study/turker_id', methods = ['POST'])
def receive_id():
    data = flask.request.form
    turker_id = data["turker_id"]
    hashcode = hash(turker_id+'Carleton')

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT turker_id FROM turker WHERE turker_id = %s",(turker_id,))
    if len(cursor.fetchall()) == 0:
        cursor.execute("INSERT INTO turker (turker_id,hashcode) VALUES (%s, %s)",(turker_id,hashcode))
    connection.commit()
    cursor.close()
    connection.close()

    # with open('pilot_client_id.csv','a', newline='') as csvfile:
    #     writer = csv.writer(csvfile, delimiter = ',', quotechar='"')
    #     # hashcode = hash(turker_id+'Carleton')
    #     writer.writerow([turker_id,hashcode])
    return json.dumps({'id':turker_id,'hashcode':hashcode})

# Post stimuli data
@app.route('/randomStim/post_data', methods = ['POST'])
def post_data():
    data = flask.request.form # The following data are all casted into str class

    turker_id = data["turker_id"] #0

    cloud_width = data["cloud_width"] #1
    cloud_height = data["cloud_height"] #2
    cloud_center_x = data["cloud_center_x"] #3
    cloud_center_y = data["cloud_center_y"] #4

    clicked_word = data["clicked_word"] #5
    correct_word = data["correct_word"] #6
    wrong_word = data["wrong_word"] #7
    distance_between_targets = data["distance_between_targets"] #8
    time = data["time"] #9

    correct_word_x = data["correct_word_x"] #10
    correct_word_y = data["correct_word_y"] #11
    correct_word_fontsize = data["correct_word_fontsize"] #12
    correct_word_width = data["correct_word_width"] #13
    correct_word_height = data["correct_word_height"] #14
    correct_word_center_distance = data["correct_word_center_distance"] #15

    wrong_word_x = data["wrong_word_x"] #16
    wrong_word_y = data["wrong_word_y"] #17
    wrong_word_fontsize = data["wrong_word_fontsize"] #18
    wrong_word_width = data["wrong_word_width"] #19
    wrong_word_height = data["wrong_word_height"] #20
    wrong_word_center_distance = data["wrong_word_center_distance"] #21

    number_of_words = data["number_of_words"] #22
    span_content = data["span_content"] #23

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
            INSERT INTO pilot_data_on_circle (turker_id,cloud_width,cloud_height,cloud_center_x,cloud_center_y,clicked_word,correct_word,wrong_word,distance_between_targets,time,correct_word_x,correct_word_y,correct_word_fontsize,correct_word_width,correct_word_height,correct_word_center_distance,wrong_word_x,wrong_word_y,wrong_word_fontsize,wrong_word_width,wrong_word_height,wrong_word_center_distance,number_of_words,span_content)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """,
            (turker_id,cloud_width,cloud_height,cloud_center_x,cloud_center_y,clicked_word,correct_word,wrong_word,distance_between_targets,time,correct_word_x,correct_word_y,correct_word_fontsize,correct_word_width,correct_word_height,correct_word_center_distance,wrong_word_x,wrong_word_y,wrong_word_fontsize,wrong_word_width,wrong_word_height,wrong_word_center_distance,number_of_words,span_content))
    connection.commit()
    cursor.close()
    connection.close()


    # with open('pilot_client_data.csv','a', newline='') as csvfile:
    #     writer = csv.writer(csvfile, delimiter = ',', quotechar='"')
    #     # writer.writerow(['turker_id',
    #     # 'cloud_width','cloud_height','cloud_center_x','cloud_center_y',
    #     # 'clicked_word','correct_word','wrong_word','distance_between_targets',
    #     # 'correct_word_x','correct_word_y','correct_word_fontsize','correct_word_width','correct_word_height','correct_word_center_distance',
    #     # 'wrong_word_x','wrong_word_y','wrong_word_fontsize','wrong_word_width','wrong_word_height','wrong_word_center_distance',
    #     # 'number_of_words','span_content'])
    #     writer.writerow([turker_id,cloud_width,cloud_height,cloud_center_x,cloud_center_y,clicked_word,correct_word,wrong_word,distance_between_targets,time,correct_word_x,correct_word_y,correct_word_fontsize,correct_word_width,correct_word_height,correct_word_center_distance,wrong_word_x,wrong_word_y,wrong_word_fontsize,wrong_word_width,wrong_word_height,wrong_word_center_distance,number_of_words,span_content])
    return json.dumps("data")

# Post hypo2 stimuli data
@app.route('/word_cognition_study/post_data_multi',methods=['POST'])
def post_data_multi():
    data = flask.request.form

    turker_id = data["turker_id"] #0
    cloud_width = data["cloud_width"] #1
    cloud_height = data["cloud_height"] #2
    cloud_center_x = data["cloud_center_x"] #3
    cloud_center_y = data["cloud_center_y"] #4

    clicked_word = data["clicked_word"] #5
    time = data["time"] #6
    clicked_word_x = data["clicked_word_x"] #7
    clicked_word_y = data["clicked_word_y"] #8
    clicked_word_center_distance = data["clicked_word_center_distance"] #9
    clicked_word_fontsize = data["clicked_word_fontsize"] #10
    correct_fontsize = data["correct_fontsize"] #11
    wrong_fontsize = data["wrong_fontsize"] #12

    num_words_in_ring0 = data["num_words_in_ring0"] #13
    num_words_in_ring1 = data["num_words_in_ring1"] #14
    num_words_in_ring2 = data["num_words_in_ring2"] #15
    number_of_targets = data["number_of_targets"] #16
    number_of_words = data["number_of_words"] #17
    span_content = data["span_content"] #18

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
            INSERT INTO pilot_multi_target (turker_id,cloud_width,cloud_height,cloud_center_x,cloud_center_y,clicked_word,time,clicked_word_x,clicked_word_y,clicked_word_center_distance,clicked_word_fontsize,correct_fontsize,wrong_fontsize,num_words_in_ring0,num_words_in_ring1,num_words_in_ring2,number_of_targets,number_of_words,span_content)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """,
            (turker_id,cloud_width,cloud_height,cloud_center_x,cloud_center_y,clicked_word,time,clicked_word_x,clicked_word_y,clicked_word_center_distance,clicked_word_fontsize,correct_fontsize,wrong_fontsize,num_words_in_ring0,num_words_in_ring1,num_words_in_ring2,number_of_targets,number_of_words,span_content))
    connection.commit()
    cursor.close()
    connection.close()


    # with open('hypo2_client_data.csv','a',newline='') as csvfile:
    #     writer = csv.writer(csvfile,delimiter=',',quotechar='"')
    #     writer.writerow([turker_id,cloud_width,cloud_height,cloud_center_x,cloud_center_y,
    #     clicked_word,time,clicked_word_x,clicked_word_y,clicked_word_center_distance,clicked_word_fontsize,
    #     correct_fontsize,wrong_fontsize,
    #     num_words_in_ring0,num_words_in_ring1,num_words_in_ring2,number_of_targets,number_of_words,
    #     span_content])
    return json.dumps("success")


# Post demographic data
@app.route('/word_cognition_study/completion/post_demographic_data', methods=['POST'])
def post_demographic_data():
    data = flask.request.form
    turker_id = data["turker_id"]
    age = data["age"]
    gender = data["gender"]
    education = data["education"]
    difficulty = data["difficulty"]
    confidence = data["confidence"]
    eyetrace = data["eyetrace"]

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
            INSERT INTO pilot_demographic_data (turker_id,age,gender,education,difficulty,confidence,eyetrace)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
            (turker_id,age,gender,education,difficulty,confidence,eyetrace))
    connection.commit()
    cursor.close()
    connection.close()

    # with open('pilot_demographic_data.csv','a',newline='') as csvfile:
    #     writer = csv.writer(csvfile,delimiter = ',',quotechar='"')
    #     # writer.writerow(['tuerker_id','age','gender','difficulty','confidence','eyetrace'])
    #     writer.writerow([turker_id,age,gender,difficulty,confidence,eyetrace])
    return json.dumps("success saving data")
##########################################################################################################################################################################################################################

whole_word_list = []
def load_all_word():
    with open('COCA_UNQ.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            whole_word_list.append(row[0])
    return whole_word_list
print('Loading words...')
whole_word_list = load_all_word()
print('All words loaded, checking for indecent words...')

blacklist = ['ace', 'acerous', 'acers', 'aces', 'acne', 'acnes', 'acorn', 'acorns', 'acre', 'acres', 'aeons', 'anus', 'arc', 'arcs', 'are', 'ares', 'arose', 'arouse', 'ars', 'arson', 'aver', 'axe', 'axes', 'axon', 'axons', 'azure', 'azures', 'can', 'cane', 'caner', 'caners', 'canes', 'canoe', 'canoer', 'canoes', 'cans', 'car', 'care', 'cares', 'carouse', 'cars', 'carve', 'carves', 'case', 'cause', 'causer', 'cave', 'caver', 'cavern', 'cavernous', 'caverns', 'cavers', 'caves', 'censor', 'coarse', 'coarsen', 'coax', 'coaxer', 'coaxes', 'con', 'cone', 'cones', 'cons', 'convex', 'core', 'cores', 'corn', 'cornea', 'corneas', 'corns', 'course', 'cove', 'coven', 'covens', 'cover', 'covers', 'coves', 'crane', 'cranes', 'crave', 'craves', 'craze', 'crazes', 'crone', 'crones', 'crux', 'cruxes', 'cue', 'cues', 'cur', 'cure', 'cures', 'curs', 'curse', 'curve', 'curves', 'czar', 'czars', 'ear', 'earn', 'earns', 'ears', 'ecru', 'ecrus', 'ens', 'eon', 'eons', 'era', 'eras', 'eros', 'euro', 'euros', 'exon', 'exons', 'nares', 'nave', 'naves', 'near', 'nears', 'nervous', 'nevus', 'nexus', 'nor', 'norse', 'nos', 'nose', 'nova', 'novae', 'novas', 'nurse', 'nus', 'oar', 'oars', 'ocean', 'oceans', 'once', 'one', 'ones', 'onus', 'orca', 'ore', 'ores', 'ors', 'ounce', 'ounces', 'our', 'ours', 'ova', 'oven', 'ovens', 'over', 'overs', 'oxane', 'oxen', 'oxens', 'oxes', 'race', 'races', 'ran', 'rave', 'raven', 'ravenous', 'ravens', 'raves', 'raze', 'razes', 'reason', 'recon', 'rescan', 'rev', 'revs', 'roan', 'roans', 'roe', 'roes', 'rose', 'roue', 'roues', 'rouse', 'rove', 'roves', 'rue', 'rues', 'run', 'rune', 'runes', 'runs', 'ruse', 'sac', 'sane', 'saner', 'sauce', 'saucer', 'save', 'saver', 'savor', 'savour', 'sax', 'scan', 'scar', 'scare', 'scone', 'score', 'scorn', 'scour', 'sea', 'sear', 'senor', 'senora', 'sera', 'sex', 'snare', 'snore', 'soar', 'son', 'sonar', 'sore', 'sour', 'source', 'sox', 'suave', 'suaver', 'sue', 'suer', 'sun', 'sure', 'uncase', 'uncover', 'uncovers', 'unsex', 'urea', 'urn', 'urns', 'use', 'user', 'uvea', 'van', 'vane', 'vanes', 'vans', 'vase', 'vear', 'vears', 'venous', 'venus', 'vex', 'xerus', 'zas', 'zax', 'zaxes', 'zen', 'zens', 'zero', 'zeros', 'zoa', 'zoea', 'zoeas', 'zone', 'zoner', 'zoners', 'zones', 'zorse', 'zouave', 'zouaves']
naughtyList = ['anal', 'anus', 'arrse', 'arse', 'ass', 'asses','assfucker', 'assfukka', 'asshole', 'assholes', 'asswhole','b!tch', 'b00bs','b17ch','b1tch','ballbag','balls','ballsack','bastard','beastial','beastiality','bellend','bestial','bestiality','biatch','bitch','bitcher','bitchers','bitches','bitchin','bitching','bloody','blow job','blowjob','blowjobs','boiolas','bollock','bollok','boner','boob','boobs','booobs','boooobs','booooobs','booooooobs','bras','breasts','buceta','bugger','bum','bunny fucker','butt','butthole','buttmuch','buttocks','buttplug','c0ck','c0cksucker','carpet muncher','cawk','chink','cipa','cl1t','clit','clitoris','clits','cnut','cock','cock-sucker','cockface','cockhead','cockmunch','cockmuncher','cocks','cocksuck','cocksucked','cocksucker','cocksucking','cocksucks','cocksuka','cocksukka','cok','cokmuncher','coksucka','coon','cox','cracker','crap','cum','cummer','cumming','cums','cumshot','cunilingus','cunillingus','cunnilingus','cunt','cuntlick','cuntlicker','cuntlicking','cunts','cyalis','cyberfuc','cyberfuck','cyberfucked','cyberfucker','cyberfuckers','cyberfucking','d1ck','damn','diarrhea','dick','dickhead','dike','dildo','dildos','dink','dinks','dirsa','dlck','dog-fucker','doggin','dogging','donkeyribber','doosh','duche','dyke','ejaculate','ejaculated','ejaculates','ejaculating','ejaculatings','ejaculation','ejakulate','f u c k','f u c k e r','f4nny','fag','fagging','faggitt','faggot','faggs','fagot','fagots','fags','fanny','fannyflaps','fannyfucker','fanyy','fatass','fcuk','fcuker','fcuking','feces','feck','fecker','felching','fellate','fellatio','fingerfuck','fingerfucked','fingerfucker','fingerfuckers','fingerfucking','fingerfucks','fistfuck','fistfucked','fistfucker','fistfuckers','fistfucking','fistfuckings','fistfucks','flange','fook','fooker','fuck','fucka','fucked','fucker','fuckers','fuckhead','fuckheads','fucking','fuckings','fuckingshitmotherfucker','fuckme','fucks','fuckwhit','fuckwit','fudge packer','fudgepacker','fuk','fuker','fukker','fukkin','fuks','fukwhit','fukwit','fux','fux0r','f_u_c_k','gangbang','gangbanged','gangbangs','gaylord','gaysex','goatse','God','god-dam','god-damned','goddamn','goddamned','hardcoresex','hell','heshe','hoar','hoare','hoer','homo','homosexual','homosexuals','hooker','hore','horniest','horny','hotsex','"jack-off','jackoff','jap','jerk-off','jism','jiz','jizm','jizz','kawk','knob','knobead','knobed','knobend','knobhead','knobjocky','knobjokey','kock','kondum','kondums','kum','kummer','kumming','kums','kunilingus','l3i+ch','l3itch','labia','lesbian','lesbians','lesbo','lmfao','lust','lusting','m0f0','m0fo','m45terbate','ma5terb8','ma5terbate','masochist','massacre','master-bate','masterb8','masterbat*','masterbat3','masterbate','masterbation','masterbations','masturbate','mo-fo','mof0','mofo','mothafuck','mothafucka','mothafuckas','mothafuckaz','mothafucked','mothafucker','mothafuckers','mothafuckin','mothafucking','mothafuckings','mothafucks','mother fucker','motherfuck','motherfucked','motherfucker','motherfuckers','motherfuckin','motherfucking','motherfuckings','motherfuckka','motherfucks','muff','mutha','muthafecker','muthafuckker','muther','mutherfucker','n1gga','n1gger','nazi','nigg3r','nigg4h','nigga','niggah','niggas','niggaz','nigger','niggers','nob','nob jokey','nobhead','nobjocky','nobjokey','numbnuts','nutsack','orgasim','orgasims','orgasm','orgasms','p0rn','pawn','pecker','penis','penisfucker','phonesex','phuck','phuk','phuked','phuking','phukked','phukking','phuks','phuq','pigfucker','pimpis','piss','pissed','pisser','pissers','pisses','pissflaps','pissin','pissing','pissoff','playboy','poop','porn','porno','pornography','pornos','prick','pricks','pron','pube','pusse','pussi','pussies','pussy','pussys','rape','raper','rapist','rectum','retard','rimjaw','rimming','s hit','s.o.b.','sadist','schlong','screwing','scroat','scrote','scrotum','semen','sensual','sensuous','sex','sexes','"sh!+"','"sh!t"','sh1t','shag','shagger','shaggin','shagging','shemale','"shi+"','shit','shitdick','shite','shited','shitey','shitfuck','shitfull','shithead','shiting','shitings','shits','shitted','shitter','"shitters "','shitting','shittings','"shitty "','skank','slut','sluts','smegma','smut','snatch','"son-of-a-bitch"','spac','spunk','s_h_i_t','t1tt1e5','t1tties','teets','teez','testical','testicle','tit','titfuck','tits','titt','tittie5','tittiefucker','titties','tittyfuck','tittywank','titwank','tosser','turd','tw4t','twat','twathead','twatty','twunt','twunter','urinary','urine','uterus','v14gra','v1gra','vagina','vaginal','viagra','vulva','w00se','wang','wank','wanker','wanky','weiner','whoar','whore','whores','willies','willy','xrated','xxx','FALSE','corpses','corpse','bodies','auschwitz']

decent_word_list = []
for word in whole_word_list:
    # if word in blacklist or word in naughtyList:
    #     print(word)
    if not word in blacklist and not word in naughtyList:
        decent_word_list.append(word)
print('Done.')


def check_hashcode(hashcode):
    with open('pilot_client_id.csv','r',newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter = ',', quotechar='"')
        for row in reader:
            if str(hashcode) == row[1]:
                return True
    return False 

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('Usage: {0} host port'.format(sys.argv[0]))
		print('  Example: {0} allen.mathcs.carleton.edu xxxx'.format(sys.argv[0]))
		exit()
	
	host = sys.argv[1]
	port = int(sys.argv[2])
	app.run(host=host, port=port, debug=True)




# def list_of_stimuli():
#     # Messy Pointer, so read the file first time for length, 
#     # and then read it again for use
#     row_count = -1
#     with open('client_tasklist.csv','r',newline='') as csvfile:
#         row_counter = csv.reader(csvfile, delimiter = ',', quotechar='"')
#         # row_count = len(list(reader))
#         row_count = sum(1 for row in row_counter)
#         # print(row_count)
#     # Return a random row in the tasklist
#     with open('client_tasklist.csv','r',newline='') as csvfile:
#         client_tasklist = csv.reader(csvfile,delimiter = ',', quotechar='"')
#         task_list = []
#         random_row = random.randint(1,row_count) # 1 <= n <= row_count
#         # print(random_row)
#         for i in range(random_row-1):
#             next(client_tasklist)
#         row = next(client_tasklist)
#         # print(row)
#         for num in row:
#             task_list.append(int(num))
#         # print(task_list)
#     return task_list

# # Return a list of words in JSON format
# @app.route('/randomStim/<numberOfWords>')
# def randomStim(numberOfWords):
#     try:
#         random_words = random.sample(words, int(numberOfWords))
#         return json.dumps(random_words)
#     except ValueError:
#         print('numberOfWords is too big!')

# words = ['Apples', 'Apricots', 'Avocados',
#     'Bananas', 'Boysenberries', 'Blueberries', 'Bing Cherry',
#     'Cherries', 'Cantaloupe', 'Crab apples', 'Clementine', 'Cucumbers',
#     'Damson plum', 'Dinosaur Eggs', 'Dates', 'Dewberries', 'Dragon Fruit',
#     'Elderberry', 'Eggfruit', 'Evergreen Huckleberry', 'Entawak',
#     'Fig', 'Farkleberry', 'Finger Lime',
#     'Grapefruit', 'Grapes', 'Gooseberries', 'Guava',
#     'Honeydew melon', 'Hackberry', 'Honeycrisp Apples',
#     'Indian Prune', 'Indonesian Lime', 'Imbe', 'Indian Fig',
#     'Apples', 'Apricots', 'Avocados',
#     'Bananas', 'Boysenberries', 'Blueberries', 'Bing Cherry',
#     'Cherries', 'Cantaloupe', 'Crab apples', 'Clementine', 'Cucumbers',
#     'Damson plum', 'Dinosaur Eggs', 'Dates', 'Dewberries', 'Dragon Fruit',
#     'Elderberry', 'Eggfruit', 'Evergreen Huckleberry', 'Entawak',
#     'Fig', 'Farkleberry', 'Finger Lime',
#     'Grapefruit', 'Grapes', 'Gooseberries', 'Guava',
#     'Honeydew melon', 'Hackberry', 'Honeycrisp Apples',
#     'Indian Prune', 'Indonesian Lime', 'Imbe', 'Indian Fig',
#     'Apples', 'Apricots', 'Avocados',
#     'Bananas', 'Boysenberries', 'Blueberries', 'Bing Cherry',
#     'Cherries', 'Cantaloupe', 'Crab apples', 'Clementine', 'Cucumbers',
#     'Damson plum', 'Dinosaur Eggs', 'Dates', 'Dewberries', 'Dragon Fruit',
#     'Elderberry', 'Eggfruit', 'Evergreen Huckleberry', 'Entawak',
#     'Fig', 'Farkleberry', 'Finger Lime',
#     'Grapefruit', 'Grapes', 'Gooseberries', 'Guava',
#     'Honeydew melon', 'Hackberry', 'Honeycrisp Apples',
#     'Indian Prune', 'Indonesian Lime', 'Imbe', 'Indian Fig']

