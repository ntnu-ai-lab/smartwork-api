import pandas as pd
import json

is_development = True

def createExerciseJson(language, filename, type, output_dir="./json/"):
    """Creates JSON file from the Excel table in filename
    :param language:
    :param filename: the Excel file
    :param type: the ES document type. The output JSON file will also have name <type>.json
    :param output_dir
    """
    baseurl = "https://dvlxmvtyf5r6m.cloudfront.net/exercises/videos/"
    format = ".mp4"
    existingvideos = ['back_01_01', 'back_01_02', 'back_02_01', 'back_06_01', 'flex_10_08', 'pain_03_03', 'pain_04_01']

    df = pd.read_excel(filename, sheet_name='Sheet1')
    rename_map = {
        'ExerciseID': 'exerciseid',
        'group_order': 'group_order',
        'Title': 'title',
        'Explanation': 'purpose',
        'Instruction': 'instruction',
        'Reps': 'repetitions',
        'Level': 'level',
        'Sets': 'sets',
        'Time': 'time',
        'Type': 'type',
        'Condition': 'condition',
        'Function': 'function',
        'Color': 'color',
        'Info': 'info'
    }
    df.rename(columns=rename_map, inplace=True)

    # filtering only columns from rename_map
    colums2drop = set(df.columns).difference(set(rename_map.values()))
    df.drop(columns=colums2drop, inplace=True)
    # df = df[list(rename_map.values())]

    df['language'] = language
    # trimming ids just in case
    df['exerciseid'] = df['exerciseid'].str.strip()
    df['type'] = df['type'].str.strip()
    df['link'] = df['exerciseid'].apply(lambda x: baseurl + x + format if existingvideos.__contains__(x) else "")

    # dropping rows with comments in the end
    df.dropna(subset=['exerciseid'], inplace=True)
    if is_development:
        df.dropna(inplace=True)

    df['level'] = df['level'].astype(int)
    df['sets'] = df['sets'].astype(int)
    df['repetitions'] = df['repetitions'].astype(int)
    df['time'] = df['time'].astype(int)
    # if 'group_order' in df.columns:
    #     df['group_order'] = df['group_order'].astype(int)
    df["description_type"]="exercise"
    dict = df.to_dict(orient='records')
    list_es = [
        {
            "_index": "exercise_description",
            "_id": d["exerciseid"],
            "_source": d
        } for d in dict]

    output_file_name = f"{output_dir}{type}.json"
    with open(output_file_name, 'w', encoding='utf8') as json_file:
        json.dump(list_es, json_file, indent="\t", ensure_ascii=False)
