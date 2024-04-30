import json
import os
import shutil
import traceback

# "config_backup" for Back-up or "config" for selfBACK
import config_backup as config
from ConfigureQestionnaires import createQuestionnaireProperties
from CreateEducationCases import createEducationJson, createEducationWebJson
from CreateExerciseCases import createExerciseJson


def file_by_language(dir):
    """Walks through subdirectories.
    Returns the list of subdir names
    and filename of the single file in that directory.
    Ignores subdirs starting with '_'.
    """
    ret = []
    for language in os.listdir(dir):
        path = os.path.join(dir, language)
        if os.path.isdir(path) and not language.startswith('_'):
            filename = next(iter(os.listdir(path)), None)
            if filename:
                ret.append((language, os.path.join(path, filename)))
    return ret


def copy_by_extension(source_dir, target_dir, extension):
    """Copies all files with the specified extension from the source_dir to the target_dir"""
    for filename in os.listdir(source_dir):
        if filename.endswith('.' + extension):
            shutil.copy(source_dir + filename, target_dir)
            print('copying {} to {}'.format(filename, target_dir))


def createAchievementJson(language, filename, output_dir):
    """Prepares achievement json file to be uploaded to ES"""
    try:
        print("Creating achivement json for {} from {}".format(language, filename))
        input_file = open(filename, encoding="UTF-8")
        dict = json.load(input_file)
        # convert to ES index structure - adding _index, _type, _id and _source fields
        list_es = [{
            "_index": "data_description",
            "_type": "achievements_" + language,
            # "_type": "achievements_"+d["language"],
            "_id": d["achievementid"],
            "_source": d
        } for d in dict]
        output_file_name = output_dir + "achievements_" + language + ".json"
        with open(output_file_name, 'w', encoding='utf8') as json_file:
            json.dump(list_es, json_file, indent="\t", ensure_ascii=False)
    except Exception as e:
        print(e)

# path to Excel tables with static content.
# The directory has the following structure:
#
# education
#     - en
#     - da
#     - nb
# exercises
#     - en
#     - da
#     - nb

# Recreating temp directory
shutil.rmtree(config.OUTPUT_DIR, ignore_errors=True)
os.mkdir(config.OUTPUT_DIR)

print('*** creating json files for the exercise content')
for (language, filename) in file_by_language(config.STATIC_PATH + "exercises/"):
    print("Creating json for exercises in language {} from file '{}'".format(language, filename))
    try:
        createExerciseJson(language, filename, f"exercise_{language}", config.OUTPUT_DIR)
    except Exception as e:
        traceback.print_tb(e)
        print(e)

if hasattr(config, 'WEB_PATH'):
    for (language, filename) in file_by_language(config.WEB_PATH + "exercises/"):
        print("Creating json for WEB exercises in language {} from file '{}'".format(language, filename))
        try:
            createExerciseJson(language, filename, f"web_exercise_{language}", config.OUTPUT_DIR)
        except Exception as e:
            traceback.print_tb(e)
            print(e)

print('*** creating json files for the education content')
for (language, filename) in file_by_language(config.STATIC_PATH + "education/"):
    print("Creating json for APP education in language {} from file '{}'".format(language, filename))
    try:
        createEducationJson(language, filename, f"education_{language}", config.OUTPUT_DIR)
    except Exception as e:
        print(e)

if hasattr(config, 'WEB_PATH'):
    for (language, filename) in file_by_language(config.WEB_PATH + "education/"):
        print("Creating json for WEB education in language {} from file '{}'".format(language, filename))
        try:
            createEducationWebJson(language, filename, f"web_education_{language}", config.OUTPUT_DIR)
        except Exception as e:
            print(e)

print('*** creating json files for the achievement content')
# createAchievementJson("en", config.ACHIEVEMENT_DIR + "achievements_en.json", config.OUTPUT_DIR)
# createAchievementJson("da", config.ACHIEVEMENT_DIR + "achievements_da.json", config.OUTPUT_DIR)
createAchievementJson("nb", config.ACHIEVEMENT_DIR + "achievements_nb.json", config.OUTPUT_DIR)
# createAchievementJson("nl", config.ACHIEVEMENT_DIR + "achievements_nl.json", config.OUTPUT_DIR)
print('')

createQuestionnaireProperties(config.CODEBOOK_PATH, config.OUTPUT_DIR)

# copying tailoring files from Dropbox as they are.
copy_by_extension(config.TAILORING_DIR, config.OUTPUT_DIR, "json")

print('')
# copying all json files to the backend dir
if config.BACKEND_STATIC_DIR:
    copy_by_extension(config.OUTPUT_DIR, config.BACKEND_STATIC_DIR, "json")
    copy_by_extension(config.OUTPUT_DIR, config.BACKEND_RESOURCES_DIR, "properties")
    copy_by_extension(config.OUTPUT_DIR, config.BACKEND_RESOURCES_DIR, "ini")
    shutil.rmtree(config.OUTPUT_DIR)