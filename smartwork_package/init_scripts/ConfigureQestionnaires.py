import configparser
import json

import numpy as np
import pandas as pd
from pandas import DataFrame

CONFIG_FILE_NAME = "questionnaires.ini"

TAILORING_NAME = 'tailoring_name'
FORMULAS_BASELINE = 'formulas_baseline'
FORMULAS_FOLLOWUP = 'formulas_followup'

NAME = 'name'
NAME_FOLLOWUP = 'followup_name'
NAME_BASELINE = 'baseline_name'
QUEST_NAME = 'quest_name'
"""union of BASELINE_NAME and FOLLOWUP_NAME columns"""

VALIDATION = 'validation'
BACKEND_VALUE = 'backend_value'
QUEST_VALUE = 'quest_value'

OPTIONAL_QUESTIONS = ['PSFS_q02',
                      'otherDiseasesConditions_q03_limb_yes1',
                      'otherDiseasesConditions_q03_limb_yes2',
                      'otherDiseasesConditions_q_breathAtRest']


# def test():
#     import config_backup as config
#     createQuestionnaireProperties(config.CODEBOOK_PATH, config.BACKEND_RESOURCES_DIR)

def createQuestionnaireProperties(filename, output_dir):
    """
    :param filename: the Excel file
    :param output_dir
    """
    print(f'Creating {CONFIG_FILE_NAME} from {filename}')

    # df = pd.read_excel(filename, sheet_name='Sheet1')
    df: DataFrame = pd.read_excel(filename, sheet_name='SmaRTWork Codebook (norwegian)', dtype=str)
    rename_map = {'Assigned values': QUEST_VALUE,
                  'Backend values': BACKEND_VALUE,
                  'Validation regex': VALIDATION,
                  'Web Questionnaire Variable': NAME_BASELINE,
                  'Follow up Web Questionnaire Variable': NAME_FOLLOWUP,
                  'myCBR Variable': NAME,
                  'Baseline formula': FORMULAS_BASELINE,
                  'Followup formula': FORMULAS_FOLLOWUP,
                  'Tailoring Question': TAILORING_NAME,
                  }
    df.rename(columns=rename_map, inplace=True)
    # filtering only columns from rename_map
    print(df.columns)
    df = df[list(rename_map.values())]

    # trimming ids just in case
    # trimming all strings
    df = df.applymap(lambda x: x.strip() if type(x) is str else x)
    df.replace('', np.nan, inplace=True)

    #(selfBACK legacy) replacing "NOT PART OF" with None
    df.loc[df[NAME_BASELINE].str.startswith("NOT PART", na=False), NAME_BASELINE] = np.nan
    df.loc[df[NAME_FOLLOWUP].str.startswith("NOT PART", na=False), NAME_FOLLOWUP] = np.nan

    # if any of BASELINE_NAME or FOLLOWUP_NAME is present it is assigned to QUEST_NAME
    df[QUEST_NAME] = df[NAME_BASELINE].where(df[NAME_BASELINE].notna(), df[NAME_FOLLOWUP])

    df_name_mapping = df[df[QUEST_NAME].notna() & df[NAME].notna() & df[FORMULAS_BASELINE].isna() & df[FORMULAS_FOLLOWUP].isna()]
    "Maps backend names/CBR attribute to the quest names if applicable. Ignore attributes calculated by formula"

    df_value_mapping = df.dropna(subset=[QUEST_VALUE, BACKEND_VALUE])
    "Map quest values to the backend values if applicable"
    df_value_mapping[QUEST_NAME].ffill(inplace=True)

    # creating config
    properties = configparser.ConfigParser()
    # prevent conversion to lowcase
    properties.optionxform = lambda option: option
    properties.add_section(VALIDATION)
    validation_section = properties[VALIDATION]

    # The list of baseline and follow-up required questions.
    # The conditional questions like p07_q01 and p14_q01
    # are processed in the backend validation logic.
    df_baseline = df.dropna(subset=[NAME_BASELINE], inplace=False)
    df_followup = df.dropna(subset=[NAME_FOLLOWUP], inplace=False)
    # PSFS_q02 is an optional second PSFS question
    df_baseline = df_baseline.drop(df_baseline[df_baseline[NAME_BASELINE].isin(OPTIONAL_QUESTIONS)].index)
    df_followup = df_followup.drop(df_followup[df_followup[NAME_FOLLOWUP].isin(OPTIONAL_QUESTIONS)].index)
    properties.add_section('required_questions')
    properties.set('required_questions', 'baseline', ";".join(df_baseline[NAME_BASELINE].tolist()))
    properties.set('required_questions', 'followup', ";".join(df_followup[NAME_FOLLOWUP].tolist()))

    properties.add_section('quest_to_backend')
    properties.add_section('backend_from_quest')
    for quest, name in zip(df_name_mapping[QUEST_NAME], df_name_mapping[NAME]):
        properties.set('quest_to_backend', quest, name)
        properties.set('backend_from_quest', name, quest)

    for index, row in df_value_mapping.iterrows():
        quest = row[QUEST_VALUE]
        backend = row[BACKEND_VALUE]
        section = f'value_mapping.{row[QUEST_NAME]}'
        if not properties.has_section(section):
            properties.add_section(section)
        properties.set(section, str(quest), backend)

    properties.add_section(FORMULAS_BASELINE)
    for index, row in df[df[FORMULAS_BASELINE].notna()].iterrows():
        name = row[NAME]
        formula = row[FORMULAS_BASELINE]
        properties.set(FORMULAS_BASELINE, name, formula)

    properties.add_section(FORMULAS_FOLLOWUP)
    for index, row in df[df[FORMULAS_FOLLOWUP].notna()].iterrows():
        name = row[NAME]
        formula = row[FORMULAS_FOLLOWUP]
        properties.set(FORMULAS_FOLLOWUP, name, formula)


    for index, row in df[df[VALIDATION].notna()].iterrows():
        validation = row[VALIDATION]
        question_id = row[QUEST_NAME]
        if pd.notnull(question_id):
            # validation = str(validation).replace('\\', '\\\\')
            validation = "^" + validation + "$"
            validation_section[str(question_id)] = validation
        else:
            print(f'Skipping validation regex at index {index} {question_id}/{row[NAME]}: {validation}')

    with open(output_dir + CONFIG_FILE_NAME, 'w') as configfile:
        properties.write(configfile)
