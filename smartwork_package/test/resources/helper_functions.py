from datetime import datetime,timezone,timedelta

def delete_all_indicies(es):
    try:
        indices=dict(es.indices.get_alias(index="*")).keys()
        for index in indices:
            es.options(ignore_status=[400,404]).indices.delete(index=index)
        return True
    except:
        return False
    
def create_plan(es,start_time,username):
    ex=[]
    edu=[{'educationid': 'Cause of LBP_1',
      'used': False,
      'canbequiz': False,
      'thisweek': False,
      'expiry_weeks': 2,
      'priority': 4,
      'group': 28,
      'is_quiz': False}]
    for ex_name,sets,reps,duration in [("back_01_01",3,10,60),("back_01_01",3,10,30)]:
        #values here are random as its arbitrary what they are
        ex.append({'exerciseid': ex_name,
                    'title': ex_name,
                    'type': 'Ab',
                    'purpose': '-',
                    'instruction': '-',
                    'level': 1,
                    'repetitions': reps,
                    'sets': sets,
                    'time': duration,
                    'condition': 'LBP_NP',
                    'language': 'nb',
                    'link': '',
                    'description_type': 'exercise'})
    plan={'userid': username,
        'created': start_time.timestamp(),
        'start': start_time.timestamp(),
        'end': (start_time +timedelta(days=7)).timestamp(),
        'exercises_duration': len(ex)*5,
        'history': [],
        'plan': {'date': start_time.timestamp(),
        'educations': edu,
        'exercises': ex,
        'activity': {'goal': 3000,
        'recommended_min': 3000,
        'recommended_max': 10000}},
        'done': {'steps': 0,
        'date': start_time.timestamp(),
        'exercises': [],
        'educations': [],
        'activity': {'goal': 0, 'recommended_max': 0, 'recommended_min': 0}}}
    es.index(index='plan', body=plan)

