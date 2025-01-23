import argparse
parser=argparse.ArgumentParser()
parser.add_argument("--es_password")
parser.add_argument("--es_url")
parser.add_argument("--limesurvey_api_key")
parser.add_argument("--mycbr_url")
args=parser.parse_args()


ES_PASSWORD=args.es_password
LIMESURVEY_API_KEY=args.LIMESURVEY_API_KEY
ES_URL=args.es_url
MYCBR_URL=args.mycbr_url



STEP_GOAL_MIN=3000
STEP_GOAL_MAX=10000
EXERCISE_MAX_SIZE=12
EDUCATION_QUIZ_MAX=3
STEP_GOAL_MIN=3000
STEP_GOAL_MAX=10000
GROUPS_EXERCISES={'Cause of LBP_1': 0, 'Cause of LBP_2': 0, 'Cause of LBP_3': 0, 'Cause of LBP_4': 0, 'Cause of LBP_5': 0, 'Cause of LBP_6': 0, 'Guideline LBP_1': 1, 'Guideline LBP_2': 1, 'Guideline LBP_3': 1, 'Imaging_1': 2, 'Imaging_2': 2, 'Pain rating_1': 3, 'Reassurance_1': 4, 'Reassurance_2': 4, 'Reassurance_3': 4, 'Reassurance_4': 4, 'Reassurance_5': 4, 'Reassurance_6': 4, 'Reassurance_7': 4, 'Reassurance_8': 4, 'Reassurance_9': 4, 'Reassurance_10': 4, 'Stay active_1': 5, 'Stay active_2': 5, 'Stay active_3': 5, 'Stay active_4': 5, 'Stay active_5': 5, 'Stay active_6': 5, 'Stay active_7': 5, 'Stay active_8': 5, 'Stay active_9': 5, 'Stay active_10': 5, 'Stay active_11': 5, 'Stay active_12': 5, 'Stay active_13': 5, 'Stay active_14': 5, 'Start exercise_1': 6, 'Start exercise_2': 6, 'Start exercise_3': 6, 'Start exercise_4': 6, 'Start exercise_5': 6, 'Start exercise_6': 6, 'Start exercise_7': 6, 'Start exercise_8': 6, 'Start exercise_9': 6, 'Start exercise_10': 6, 'Structure of back_1': 7, 'Structure of back_2': 7, 'Structure of back_3': 7, 'Structure of back_4': 7, 'Mind-body connection_1': 8, 'Mind-body connection_2': 8, 'Mind-body connection_3': 8, 'Mind-body connection_4': 8, 'Mind-body connection_5': 8, 'Mind-body connection_6': 8, 'Mind-body connection_7': 8, 'Mind-body connection_8': 8, 'Mind-body connection_9': 8, 'Mind-body connection_10': 8, 'Encouragement to SM_1': 9, 'Encouragement to SM_2': 9, 'Encouragement to SM_4': 9, 'Encouragement to SM_5': 9, 'Encouragement to SM_6': 9, 'Encouragement to SM_7': 9, 'Encouragement to SM_8': 9, 'Accepting pain_1': 10, 'Accepting pain_2': 10, 'Accepting pain_3': 10, 'Anxious_1': 11, 'Anxious_2': 11, 'Anxious_3': 11, 'Attitude_1': 12, 'Attitude_2': 12, 'Attitude_3': 12, 'Attitude_4': 12, 'Attitude_5': 12, 'Attitude_6': 12, 'Changing negative thoughts_1': 13, 'Changing negative thoughts_2': 13, 'Changing negative thoughts_3': 13, 'Changing negative thoughts_4': 13, 'Changing negative thoughts_5': 13, 'Changing negative thoughts_6': 13, 'Changing negative thoughts_7': 13, 'Changing negative thoughts_9': 13, 'Changing negative thoughts_10': 13, 'Distraction_1': 14, 'Distraction_2': 14, 'Distraction_3': 14, 'Distraction_4': 14, 'Distraction_5': 14, 'Distraction_6': 14, 'Distress_1': 15, 'Fear-avoidance_1': 16, 'Fear-avoidance_2': 16, 'Fear-avoidance_3': 16, 'Fear-avoidance_4': 16, 'Fear-avoidance_5': 16, 'Fear-avoidance_6': 16, 'Stress_1': 17, 'Stress_2': 17, 'Stress_3': 17, 'Thoughts_1': 18, 'Thoughts_2': 18, 'Thoughts_3': 18, 'Thoughts_4': 18, 'Thoughts_5': 18, 'Thoughts_6': 18, 'Thoughts_7': 18, 'Daily activity_1': 19, 'Daily activity_2': 19, 'Daily activity_3': 19, 'Daily activity_4': 19, 'Daily activity_5': 19, 'Me time_1': 20, 'Me time_2': 20, 'FA Reassurance_2': 21, 'FA Reassurance_3': 21, 'FA Reassurance_4': 21, 'FA Reassurance_5': 21, 'FA Stay active_1': 22, 'FA Stay active_2': 22, 'FA Stay active_3': 22, 'FA Stay active_4': 22, 'FA Stay active_5': 22, 'FA Stay active_6': 22, 'FA Stay active_7': 22, 'Depression_1': 23, 'Anxiety_1': 24, 'Sleep disorders_1': 25, 'MSK pain_1': 26, 'Goal setting_1': 27, 'Goal setting_2': 27, 'Goal setting_3': 27, 'Goal setting_4': 27, 'Goal setting_5': 27, 'Action planning_1': 28, 'Action planning_2': 28, 'Action planning_3': 28, 'Pacing_1': 29, 'Pacing_2': 29, 'Pacing_3': 29, 'Pacing_4': 29, 'Pacing_5': 29, 'Pacing_6': 29, 'Problem solving_1': 30, 'Problem solving_2': 30, 'Problem solving_3': 30, 'Problem solving_4': 30, 'Relaxation_1': 31, 'Relaxation_2': 31, 'Relaxation_3': 31, 'Relaxation_4': 31, 'Relaxation_5': 31, 'Sleep_1': 32, 'Sleep_2': 32, 'Sleep_3': 32, 'Sleep_4': 32, 'Work_1': 33, 'Work_2': 33, 'Work_3': 33, 'Work_4': 33, 'Work_5': 33, 'Family and friends_1': 34, 'Family and friends_2': 34, 'Family and friends_3': 34, 'Family and friends_4': 34, 'Family and friends_5': 34, 'Family and friends_6': 34, 'Barrier time_1': 35, 'Barrier time_2': 35, 'Barrier tiredness_1': 36, 'Barrier tiredness_2': 36, 'Barrier support_1': 37, 'Barrier family work_1': 38, 'Barrier family work_2': 38, 'Barrier weather_1': 39, 'Barrier weather_2': 39, 'Barrier facilities_1': 40, 'Barrier facilities_2': 40, 'Barrier facilities_3': 40}

GENERIC_EDUCATION_ITEMS=["Cause of LBP_1", "Cause of LBP_2", "Cause of LBP_3", "Cause of LBP_4", "Cause of LBP_5", "Cause of LBP_6",
			"Guideline LBP_1", "Guideline LBP_2", "Guideline LBP_3",
			"Imaging_1", "Imaging_2",
			"Pain rating_1",
			"Reassurance_2", "Reassurance_4", "Reassurance_6", "Reassurance_8", "Reassurance_9", "Reassurance_10",
			"Stay active_1", "Stay active_2", "Stay active_3", "Stay active_4", "Stay active_5", "Stay active_6", "Stay active_7", "Stay active_8", "Stay active_9", "Stay active_10", "Stay active_11", "Stay active_12", "Stay active_13", "Stay active_14",
			"Start exercise_1", "Start exercise_2", "Start exercise_5", "Start exercise_8", "Start exercise_9", "Start exercise_10",
			"Structure of back_1", "Structure of back_2", "Structure of back_3", "Structure of back_4",
			"Mind-body connection_1", "Mind-body connection_2", "Mind-body connection_5", "Mind-body connection_8",
			"Encouragement to SM_1", "Encouragement to SM_5",
			"Attitude_1", "Attitude_2", "Attitude_3", "Attitude_4", "Attitude_5", "Attitude_6",
			"Distraction_2",
			"Thoughts_1", "Thoughts_3",
			"Daily activity_1", "Daily activity_2", "Daily activity_3", "Daily activity_4", "Daily activity_5",
			"Me time_1", "Me time_2",
			"Sleep disorders_1",
			"MSK pain_1",
			"Goal setting_1", "Goal setting_2", "Goal setting_3", "Goal setting_4", "Goal setting_5",
			"Action planning_1", "Action planning_2", "Action planning_3",
			"Pacing_1", "Pacing_2", "Pacing_3", "Pacing_4", "Pacing_5", "Pacing_6",
			"Relaxation_1", "Relaxation_2", "Relaxation_3", "Relaxation_4", "Relaxation_5",
			"Sleep_4",
			"Family and friends_3"]


##############
#rule exercises
##############

#bt_pain_average >=7
BT_PAIN_AVERAGE_HIGH_ADD=['Cause of LBP_1', 'Cause of LBP_3', 'Cause of LBP_4', 'Cause of LBP_5', 'Imaging_1', 'Imaging_2', 'Pain rating_1', 'Reassurance_2', 'Reassurance_5', 'Accepting pain_1', 'Accepting pain_3', 'Distraction_1', 'Distraction_4', 'Distraction_5', 'Distress_1', 'FA Reassurance_2', 'FA Reassurance_3', 'FA Reassurance_4', 'FA Reassurance_5', 'FA Stay active_1', 'FA Stay active_2', 'FA Stay active_3', 'FA Stay active_4', 'FA Stay active_5', 'FA Stay active_6', 'FA Stay active_7', 'Problem solving_1', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Relaxation_1', 'Relaxation_2', 'Relaxation_3', 'Relaxation_4', 'Relaxation_5']
BT_PAIN_AVERAGE_HIGH_RM=['Guideline_2', 'Guideline_3', 'Reassurance_8', 'Stay active_2', 'Stay active_3', 'Stay active_7', 'Stay active_12', 'Start exercise_1', 'Start exercise_2', 'Start exercise_3', 'Start exercise_4', 'Start exercise_5', 'Start exercise_6', 'Start exercise_7', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Depression_1', 'Anxiety_1', 'Sleep disorders_1', 'MSK Pain_1', 'Pacing_1']

#bt_pain_average_change>=3
BT_PAIN_AVERAGE_CHANGE_ADD=['Cause of LBP_1', 'Cause of LBP_3', 'Cause of LBP_4', 'Cause of LBP_5', 'Imaging_1', 'Imaging_2', 'Pain rating_1', 'Reassurance_2', 'Reassurance_5', 'Accepting pain_1', 'Accepting pain_3', 'Distraction_1', 'Distraction_4', 'Distraction_5', 'Distress_1', 'FA Reassurance_2', 'FA Reassurance_3', 'FA Reassurance_4', 'FA Reassurance_5', 'FA Stay active_1', 'FA Stay active_2', 'FA Stay active_3', 'FA Stay active_4', 'FA Stay active_5', 'FA Stay active_6', 'FA Stay active_7', 'Problem solving_1', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Relaxation_1', 'Relaxation_2', 'Relaxation_3', 'Relaxation_4', 'Relaxation_5']
BT_PAIN_AVERAGE_CHANGE_RM=['Guideline_2', 'Guideline_3', 'Reassurance_8', 'Stay active_2', 'Stay active_3', 'Stay active_7', 'Stay active_12', 'Start exercise_1', 'Start exercise_2', 'Start exercise_3', 'Start exercise_4', 'Start exercise_5', 'Start exercise_6', 'Start exercise_7', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Depression_1', 'Anxiety_1', 'Sleep disorders_1', 'MSK Pain_1', 'Pacing_1']

#6>=bt_pain_average>=3
BT_PAIN_AVERAGE_MEDIUM_ADD=['Cause of LBP_1', 'Cause of LBP_3', 'Cause of LBP_4', 'Cause of LBP_5', 'Guideline LBP_1', 'Guideline LBP_2', 'Guideline LBP_3', 'Pain rating_1', 'Reassurance_4', 'Reassurance_6', 'Reassurance_7', 'Stay active_1', 'Stay active_5', 'Stay active_6', 'Stay active_9', 'Stay active_10', 'Stay active_13', 'Start exercise_3', 'Start exercise_4', 'Start exercise_6', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Accepting pain_1', 'Accepting pain_2', 'Accepting pain_3', 'Distraction_3', 'Distraction_6', 'Thoughts_2', 'Thoughts_4', 'FA Reassurance_4', 'Daily activity_1', 'Daily activity_2', 'Daily activity_3', 'Daily activity_4', 'Daily activity_5', 'Me time_1', 'Me time_2', 'Problem solving_1', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Relaxation_1', 'Relaxation_2', 'Relaxation_3', 'Relaxation_4', 'Relaxation_5']
BT_PAIN_AVERAGE_MEDIUM_RM=['Sleep disorders_1', 'MSK pain_1']

#t_cpg_function>=5
T_CPG_ADD=['Guideline LBP_3', 'Reassurance_9', 'Reassurance_10', 'Stay active_1', 'Stay active_7', 'Stay active_12', 'Start exercise_5', 'Start exercise_9', 'Start exercise_10', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_5', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Fear-avoidance_4', 'Daily activity_1', 'Daily activity_2', 'Daily activity_3', 'Daily activity_4', 'Daily activity_5', 'Me time_1', 'Me time_2', 'FA Stay active_2', 'Goal setting_1', 'Goal setting_2', 'Goal setting_3', 'Goal setting_4', 'Goal setting_5', 'Action planning_1', 'Action planning_2', 'Action planning_3', 'Pacing_1', 'Pacing_2', 'Pacing_3', 'Pacing_4', 'Pacing_5', 'Pacing_6', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4']

#t_cpg_change>=2
T_CPG_CHANGE_ADD=['Guideline LBP_3', 'Reassurance_9', 'Reassurance_10', 'Stay active_1', 'Stay active_7', 'Stay active_12', 'Start exercise_5', 'Start exercise_9', 'Start exercise_10', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_5', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Fear-avoidance_4', 'Daily activity_1', 'Daily activity_2', 'Daily activity_3', 'Daily activity_4', 'Daily activity_5', 'Me time_1', 'Me time_2', 'FA Stay active_2', 'Goal setting_1', 'Goal setting_2', 'Goal setting_3', 'Goal setting_4', 'Goal setting_5', 'Action planning_1', 'Action planning_2', 'Action planning_3', 'Pacing_1', 'Pacing_2', 'Pacing_3', 'Pacing_4', 'Pacing_5', 'Pacing_6', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4']

#t_tampa_fear>=5
TAMPA_ADD=['Reassurance_1', 'Reassurance_3', 'Reassurance_8', 'Stay active_3', 'Stay active_4', 'Stay active_5', 'Stay active_6', 'Stay active_7', 'Stay active_8', 'Stay active_11', 'Stay active_13', 'Start exercise_1', 'Start exercise_4', 'Start exercise_6', 'Start exercise_7', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Structure of back_2', 'Structure of back_3', 'Mind-body connection_4', 'Mind-body connection_7', 'Encouragement to SM_2', 'Encouragement to SM_6', 'Encouragement to SM_7', 'Attitude_5', 'Attitude_6', 'Changing negative thoughts_1', 'Fear-avoidance_1', 'Fear-avoidance_2', 'Fear-avoidance_3', 'Fear-avoidance_4', 'Fear-avoidance_5', 'Fear-avoidance_6', 'Thoughts_5', 'Goal setting_2', 'Goal setting_3', 'Pacing_1', 'Pacing_2', 'Pacing_3', 'Pacing_5', 'Relaxation_3', 'Relaxation_4']
TAMPA_RM=['Pacing_4', 'Pacing_6']

#bt_wai>=3
BT_WAI_ADD=['Work_1', 'Work_2', 'Work_3', 'Work_4', 'Work_5', 'Family and friends_3', 'Barrier family work_2']

#t_sleep in ["Several times a week", "Sometimes"]
T_SLEEP_ADD=['Sleep disorders_1', 'Relaxation_1', 'Relaxation_2', 'Relaxation_4', 'Relaxation_5', 'Sleep_1', 'Sleep_2', 'Sleep_3', 'Sleep_4']

#["bt_pseq_2item"]<=8:
BT_PSEQ_ADD=['Reassurance_5', 'Reassurance_9', 'Stay active_1', 'Stay active_2', 'Stay active_3', 'Stay active_4', 'Stay active_5', 'Stay active_6', 'Stay active_7', 'Stay active_8', 'Stay active_9', 'Stay active_10', 'Stay active_11', 'Stay active_12', 'Stay active_13', 'Stay active_14', 'Start exercise_1', 'Start exercise_4', 'Start exercise_5', 'Start exercise_7', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Mind-body connection_2', 'Mind-body connection_3', 'Mind-body connection_4', 'Mind-body connection_6', 'Mind-body connection_10', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_4', 'Encouragement to SM_5', 'Encouragement to SM_6', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Accepting pain_1', 'Accepting pain_2', 'Accepting pain_3', 'Attitude_1', 'Attitude_2', 'Attitude_3', 'Attitude_4', 'Attitude_5', 'Attitude_6', 'Changing negative thoughts_6', 'Changing negative thoughts_9', 'Thoughts_4', 'Me time_1', 'Me time_2', 'Goal setting_1', 'Goal setting_2', 'Goal setting_3', 'Goal setting_4', 'Goal setting_5', 'Action planning_1', 'Action planning_2', 'Action planning_3', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Work_1', 'Work_4', 'Family and friends_1', 'Family and friends_2', 'Family and friends_3', 'Family and friends_4', 'Family and friends_5', 'Family and friends_6', 'Barrier support_1']

#["bt_pss"]>=6
BT_PSS_ADD=['Reassurance_3', 'Reassurance_4', 'Reassurance_9', 'Stay active_7', 'Stay active_9', 'Stay active_10', 'Stay active_11', 'Stay active_13', 'Mind-body connection_1', 'Mind-body connection_3', 'Mind-body connection_5', 'Mind-body connection_6', 'Mind-body connection_7', 'Mind-body connection_9', 'Mind-body connection_10', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_4', 'Encouragement to SM_5', 'Encouragement to SM_6', 'Encouragement to SM_7', 'Anxious_1', 'Anxious_2', 'Anxious_3', 'Attitude_1', 'Attitude_3', 'Attitude_4', 'Attitude_5', 'Attitude_6', 'Changing negative thoughts_1', 'Changing negative thoughts_2', 'Changing negative thoughts_3', 'Changing negative thoughts_4', 'Changing negative thoughts_5', 'Changing negative thoughts_6', 'Changing negative thoughts_7', 'Changing negative thoughts_9', 'Changing negative thoughts_10', 'Distraction_6', 'Stress_1', 'Stress_2', 'Stress_3', 'Thoughts_1', 'Thoughts_3', 'Thoughts_6', 'Thoughts_7', 'Me time_1', 'Me time_2', 'Goal setting_2', 'Goal setting_4', 'Goal setting_5', 'Action planning_1', 'Action planning_2', 'Action planning_3', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Relaxation_2', 'Relaxation_5', 'Family and friends_1', 'Family and friends_2', 'Family and friends_3', 'Family and friends_4', 'Family and friends_5', 'Family and friends_6']

#["bt_phq_2item"]>=1
BT_PHQ_ADD=['Stay active_4', 'Stay active_10', 'Mind-body connection_3', 'Mind-body connection_5', 'Mind-body connection_6', 'Mind-body connection_7', 'Mind-body connection_9', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_4', 'Encouragement to SM_5', 'Encouragement to SM_6', 'Encouragement to SM_7', 'Anxious_1', 'Anxious_2', 'Anxious_3', 'Attitude_3', 'Attitude_5', 'Changing negative thoughts_1', 'Changing negative thoughts_2', 'Changing negative thoughts_3', 'Changing negative thoughts_4', 'Changing negative thoughts_5', 'Changing negative thoughts_6', 'Changing negative thoughts_7', 'Changing negative thoughts_9', 'Changing negative thoughts_10', 'Distraction_1', 'Distraction_5', 'Distraction_6', 'Fear-avoidance_1', 'Thoughts_1', 'Thoughts_2', 'Thoughts_3', 'Depression_1', 'Anxiety_1', 'Problem solving_1', 'Problem solving_3', 'Relaxation_2', 'Relaxation_3', 'Relaxation_4', 'Relaxation_5', 'Family and friends_1', 'Family and friends_2', 'Family and friends_3', 'Family and friends_4', 'Family and friends_5', 'Family and friends_6']

#"lack_of_time" in questionnaire_updated["t_barriers"]
BARRIERS_TIME_ADD=['Barrier time_1', 'Barrier time_2', 'Daily activity_1', 'Daily activity_2', 'Daily activity_3', 'Daily activity_4', 'Daily activity_5', 'Goal setting_3', 'Action planning_1']

#"too_tired" in questionnaire_updated["t_barriers"]
BARRIERS_TIRED_ADD=['Barrier tiredness_1', 'Barrier tiredness_2']

#"lack_of_support" in questionnaire_updated["t_barriers"]
BARRIERS_SUPPORT_ADD=['Barrier support_1', 'Barrier family work_1', 'Daily activity_3', 'Daily activity_4', 'Family and friends_1', 'Family and friends_2', 'Family and friends_3', 'Family and friends_4', 'Family and friends_5', 'Family and friends_6']

#"family_work" in questionnaire_updated["t_barriers"]
BARRIERS_FAMILY_ADD=['Barrier family work_1', 'Barrier family work_2', 'Work_1', 'Work_2', 'Family and friends_1', 'Family and friends_3']

#"weather" in questionnaire_updated["t_barriers"]
BARRIERS_WEATHER_ADD=['Barrier weather_1', 'Barrier weather_2']

#"facilities" in questionnaire_updated["t_barriers"]
BARRIERS_FACILITIES_ADD=['Barrier facilities_1', 'Barrier facilities_2', 'Barrier facilities_2']

#sick leave status question
# SICK_LEAVE_FULLY_ADD

ACHIEVEMENT_ORDER=['SetGoalSetting',
 'SetSleepTool',
 'UseMindfulness',
 'QACompleted',
 'SessionCompleted',
 'EducationalCorrectQuiz1',
 'EducationalCorrectQuiz3',
 'EducationalCorrectQuiz7',
 'EducationalCorrectQuiz14',
 'EducationalCorrectQuiz25',
 'EducationalMaterialRead1',
 'EducationalMaterialRead3',
 'EducationalMaterialRead7',
 'EducationalMaterialRead14',
 'EducationalMaterialRead25',
 'EducationalMaterialRead40',
 'EducationalMaterialRead60',
 'EducationalMaterialRead80',
 'EducationalMaterialRead100',
 'DailyActivitiesCompleted1',
 'DailyActivitiesCompleted3',
 'DailyActivitiesCompleted7',
 'DailyActivitiesCompleted14',
 'DailyActivitiesCompleted25',
 'DailyActivitiesCompleted40',
 'DailyGoalSteps1',
 'DailyGoalSteps3',
 'DailyGoalSteps7',
 'DailyGoalSteps14',
 'DailyGoalSteps25',
 'DailyGoalSteps40',
 'DailyGoalSteps60',
 'DailyGoalSteps80',
 'DailyGoalSteps100',
 'FullCompletedWeekSteps',
 'RowCompletedSteps3',
 'RowCompletedSteps7',
 'RowCompletedSteps14',
 'RowCompletedSteps25',
 'RowCompletedSteps40',
 'DailyRecordSteps10',
 'DailyRecordSteps12',
 'DailyRecordSteps14',
 'DailyRecordSteps16',
 'DailyRecordSteps18',
 'DailyRecordSteps20',
 'TotalSteps50',
 'TotalSteps100',
 'TotalSteps200',
 'TotalSteps400',
 'TotalSteps600',
 'TotalSteps800',
 'TotalSteps1000',
 'Marathon',
 'AverageStepsWeek5',
 'AverageStepsWeek6',
 'AverageStepsWeek8',
 'AverageStepsWeek10',
 'AverageStepsWeek12',
 'ExerciseDaysCompleted1',
 'ExerciseDaysCompleted3',
 'ExerciseDaysCompleted7',
 'ExerciseDaysCompleted14',
 'ExerciseDaysCompleted25',
 'ExerciseDaysCompleted40',
 'ExerciseDaysCompleted60',
 'ExerciseDaysCompleted80',
 'ExerciseDaysCompleted100',
 'EducationalQuizAnswers',
 'TotalDistanceKm',
 'EducationalRead',
 'ExercisesCompleted']


FIRST_WEEK_EXERCISES=[
    "pain_02_03",
    "pain_05_04",
    "pain_02_01",
    "backneck_06_01",
    "glut_01_02",
    "pain_04_02",
    "flex_02_12",
    "core_06_01",
    "ab_04_01",
    "core_05_02",
    "flex_02_05",
    "glut_04_01"
]

FIRST_WEEK_EDUCATION=[
    "Reassurance_2",
    "Start exercise_5",
    "Encouragement to SM_1",
    "Distraction_6",
    "Goal setting_4",
    "Sleep_3",
    "Red_flags"
]


LS_MAPPING={
    "PainIntensityAver_average":"BT_pain_average",
    # "T_cpg_function",
    "Fear_fears":"T_tampa_fear",
    "WorkAbility_work":"BT_wai",
    # "T_sleep",
    "PSEQPre_SQ005":"BT_pseq_5",
    "PSEQPre_SQ009":"BT_pseq_9",
    "PSSPre_SQ002":"BT_pss_2",
	"PSSPre_SQ004":"BT_pss_4",
	"PSSPre_SQ005":"BT_pss_5",
    "PSSPre_SQ010":"BT_pss_10",
    # "PHQPre_SQ001":"BT_phq_1",
    "PHQPre_SQ002":"BT_phq_2",
    # "T_barriers",
    # "T_sickleave",
    "WorkSatisfaction":"jobsatisfaction_q01",
    "ConflWork1":"workconflicts_q01",
    "StrainOutWork2":"strainsaffect_q01",
    # myCBR Variables

	"Age":"Dem_age",
	"DemGender":"Dem_gender",
    "Height":"Dem_height",
	"Weight":"Dem_weight",
	"BMI":"Dem_bmi",
	"Family":"Family",
	"Education":"Education",
    "Employment":"Employment",
    "WorkCharacteristics":"Work_characteristics",
    # BT_pain_average
	"PainIntensityWors_worst":"Pain_worst",
    "PainDuration":"Pain_current",
	"PainSites":"Pain_sites",
	# BT_wai
	# T_cpg_function
	"Comorbidities":"Comorbidities",
    "EQ5DMobility":"EQ5D_mobility",
	"EQ5DSelfcare":"EQ5D_selfcare",
    "EQ5DActivity":"EQ5D_activity",
	"EQ5DPain":"EQ5D_pain",
	"EQ5DAnxiety":"EQ5D_anxiety",
	"EQ5DVAS":"EQ5D",
	"SleepDifficulty":"Sleep_difficulty",
    "SleepWakeup":"Sleep_wakeup",
    "SleepEnd":"Sleep_end",
    "SleepDay":"Sleep_day",
	"BIPQLife":"BIPQ_life",
	"BIPQPainContinuation":"BIPQ_pain_continuation",
	"BIPQControl":"BIPQ_control",
	"BIPQSelfmanagement":"BIPQ_selfmanagement",
	"BIPQSymptoms":"BIPQ_symptoms",
	"BIPQConcern":"BIPQ_concern",
	"BIPQUnderstanding":"BIPQ_understanding",
	"BIPQEmotion":"BIPQ_emotion",
	# T_sleep
	# T_tampa_fear
	"PainSelfEfficacy":"Pain_self_efficacy",
    "BTPSEQ2Item":"BT_PSEQ_2item",
    "PSSPre_SQ001":"PSS",
	"BTPSS":"BT_PSS",
	# "PHQPre_SQ001":"PHQ",
    "BTPHQ2Item":"BT_PHQ_2item",
	# T_barriers
	# F_GPE
}