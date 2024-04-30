import json
import pandas as pd

EDUCATIONID = 'educationid'


def createEducationJson(language, filename, type, output_dir):
    """
    :param language:
    :param filename: the Excel file
    :param type: the ES document type. The output JSON file will also have name <type>.json
    :param output_dir
    """
    # df = pd.read_excel(filename, sheet_name='Sheet1')
    df = pd.read_excel(filename)
    print(df.columns)
    rename_map = {'Headcomponent': 'headcomponent',
                  'EducationID': EDUCATIONID,
                  'Short_message': 'shortmessage',
                  'Long_message': 'longmessage',
                  'Link_to_tool': 'link_to_tool',
                  'Tool': 'tool',
                  'Question': 'question',
                  'Correct_answer': 'answer',
                  'Answer': 'answer_text',
                  'Explanation': 'explanation'
                  }
    df.rename(columns=rename_map, inplace=True)

    # filtering only columns from rename_map
    colums2drop = set(df.columns).difference(set(rename_map.values()))
    df.drop(columns=colums2drop, inplace=True)
    
    df['language'] = language

    # trimming ids just in case
    df[EDUCATIONID] = df[EDUCATIONID].str.strip()
    df['tool'] = df['tool'].str.strip()
    df['headcomponent'] = df['headcomponent'].str.strip()
    df['answer'] = df['answer'] == 'Yes'
    df['link'] = None

    # dropping rows with comments in the end
    df.dropna(subset=[EDUCATIONID], inplace=True)
    # replacing numpy.nan values with None
    df = df.where(df.notnull(), None)

    # df = df.set_index('educationid')
    dict = df.to_dict(orient='records')
    list_es = [
        {
            "_index": "data_description",
            "_type": type,
            "_id": d[EDUCATIONID],
            "_source": d
        } for d in dict]

    output_file_name = f"{output_dir}{type}.json"
    with open(output_file_name, 'w', encoding='utf8') as json_file:
        json.dump(list_es, json_file, indent="\t", ensure_ascii=False)


    # list of ids of quizes
    quizes = df.dropna(subset=['answer_text'])
    f = open(output_dir + 'quizes.properties', "w")
    s = 'quiz_list=' + ','.join(quizes[EDUCATIONID].values)
    f.write(s)
    f.close()


def createEducationWebJson(language, filename, type, output_dir):
    """
    :param language:
    :param filename: the Excel file
    :param type: the ES document type. The output JSON file will also have name <type>.json
    :param output_dir
    """

    df = pd.read_excel(filename)
    rename_map = {
        'EducationID': EDUCATIONID,
        'group_order': 'group_order',
        'Headcomponent': 'headcomponent',
        'Caption': 'caption',
        'Short_message': 'shortmessage',
        'Button': 'button',
        'Long_message': 'longmessage',
        'Label_link_to_tool': 'label_link_to_tool',
        'Linked_tool': 'linked_tool',
    }
    df.rename(columns=rename_map, inplace=True)

    # filtering only columns from rename_map
    colums2drop = set(df.columns).difference(set(rename_map.values()))
    df.drop(columns=colums2drop, inplace=True)

    df['language'] = language

    text_columns = [
        EDUCATIONID,
        'headcomponent',
        'caption',
        'shortmessage',
        'button',
        'longmessage',
        'label_link_to_tool',
        'linked_tool',
    ]
    df[text_columns] = df[text_columns].apply(lambda x: x.str.strip())

    # dropping rows with comments in the end
    df.dropna(subset=[EDUCATIONID], inplace=True)
    # replacing numpy.nan values with None
    df = df.where(df.notnull(), None)

    dict = df.to_dict(orient='records')
    list_es = [
        {
            "_index": "data_description",
            "_type": type,
            "_id": d[EDUCATIONID],
            "_source": d
        } for d in dict]

    output_file_name = f"{output_dir}{type}.json"
    with open(output_file_name, 'w', encoding='utf8') as json_file:
        json.dump(list_es, json_file, indent="\t", ensure_ascii=False)


# createEducationJson("nb","./data/education/nb/Education-ES-plain-nb.xlsx",None,"../")
