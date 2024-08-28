import os
from os import path
import pickle
import shutil
import pandas as pd
import time
import datetime
# CUSTOM IMPORTS
from ana_Community_Detection_Algorithms import *
from ana_FileProcessing import *
from ana_constants import *
from ana_log_file_generation import *
from ana_parser_class import *
from ana_algo_funcs import *
from ana_rpn import postfix_evaluator
from ana_dict_class import *

# global variable for unpickling
exporting_pickled_dict_path = ""

# global var for datetime
current_time = datetime.datetime.now()

# CREATING A dictionary that is written in .bin file in the system folder
# For each config file, we have 1 hash_tble where key is the "username_configfileName_extensionName" and value is the path to the .ecom and .vcom files
ana_hash_table = {}

######################################################################################################################################

"""
    Creates the name for the Hash table.
    
    :param username: The username of the user.
    :param ana_configfilename: The name of the configuration file.
    :param ext: The extension of the Hash table.
    :return: The name of the Hash table.
"""
def ana_hash_table_file_name(username, ana_configfilename,ext):
    if username == '' or username == None:
        config_file = ana_configfilename + ext
    else:
        config_file = username + '_' + ana_configfilename + ext
    return config_file


"""
    Creates the name for the log file.

    :param username: The username of the user.
    :param ana_configfilename: The name of the configuration file.
    :param config_file_ext: The extension of the configuration file.
    :param log_file_ext: The extension of the log file.
    :return: The name of the log file.
"""
def ana_log_file_naming(username, ana_configfilename, config_file_ext, log_file_ext):
    # if username == '' or username == None:
    log_file = ana_configfilename + config_file_ext + log_file_ext
    # else:
    #     log_file = username + '_' + ana_configfilename + config_file_ext + log_file_ext
    return log_file


"""
    Deletes all files from the tmp directory.

    :param tmp_folder: The path to the tmp directory.
    :return: None
"""
def ana_del_file_tmp_dir(tmp_folder):
    # delete files from the tmp directory
    for filename in os.listdir(tmp_folder):
        file_path = os.path.join(tmp_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            pass


"""
    Gets the path to the input graph file from the dictionary.

    :param path_to_pickle_dict: The path to the dictionary.
    :param matching_key: The key to match.
"""
def ana_get_INPUT_layer_path(path_to_pickle_dict, matching_key):
    # reading the pickle file
    loaded_pickel_hash_table = pickle.load(open(path_to_pickle_dict, "rb"))
    
    # creating a list of found paths
    path_to_layer_file = None
    
    # looping through the pickle file
    for key, value in loaded_pickel_hash_table.items():
        # key is the layer name and value is the binary object. 
        # To convert the binary object to actual one, we need to load the value using pickle 
        keytype = key.split(".")
        # read the intralayer keys in the following way
        if keytype[1] == "net" and matching_key in key:
            path_to_layer_file = pickle.loads(value)._LAYER_NAME
            return path_to_layer_file
    return None

"""
    Runs the analysis pipeline using the specified configuration file.

    :param MLN_USR: The path to the user directory.
    :param ana_configfilename: The path to the configuration file.
"""
################################################################ MAIN ################################################################
# Sent the Path to the MLN_USR, where you can output the files, as well as the ana_configfilename.
def main(MLN_USR, ana_configfilename):
    # with open("/root/MLNGIT/MLN_Analysis/src/bangkok_user/system/itlab-sample_100UKAccident-2014_gen.bin", 'rb') as f:
    #     data = pickle.load(f)
    #     from pprint import pprint
    #     pprint(data)
    #     quit()
    # try:
        # relpath finds the path room the given directory
        configFile_to_open = path.relpath(ana_configfilename)
        ana_MLN_USR_basename = os.path.basename(MLN_USR)
        # separates the ana_configfilename from the absolute path
        # change the config file name each time the user wants to use a new config file
        ana_config_file = os.path.basename(ana_configfilename)
        # config _file first portion :
        # IF southwest.ana THEN southwest is returned
        config_file_first_portion = ana_config_file.split(".")
        
        # creating a log file object
        ana_log_file_object = ana_LogObject()

        # join the system folder to the user directory
        system_folder = os.path.join(MLN_USR, ana_directory_name.system_files.value)
        #if the path for hash table does not exist, a system folder is created
        system_path_exist = os.path.isdir(system_folder)
        if system_path_exist==False:
            os.mkdir(system_folder)

        #join the log folder to the user directory
        ana_log_folder = os.path.join(MLN_USR,ana_directory_name.log_files.value )
        log_path_exist = os.path.isdir(ana_log_folder)
        #if the path for log files does not exist, a log folder is created
        if log_path_exist == False:
            os.mkdir(ana_log_folder)   

        tmp_folder = os.path.join(MLN_USR, ana_directory_name.tmp_files.value)
        tmp_path_exist = os.path.isdir(tmp_folder)
        #if the path for tmp files does not exist, a tmp folder is created
        if tmp_path_exist == False:
            os.mkdir(tmp_folder)

        with open(configFile_to_open, mode='r', encoding="utf8") as ana_config_file:
            #lines contain all the lines of config file in a list, each line is an element of the list
            lines = ana_config_file.readlines()

            INPUT_LAYER_PATH_FROM_DICT = ""

            OUTPUT_DIRECTORY = lines[0].split("=")[1]
            OUTPUT_DIRECTORY = MLN_USR + OUTPUT_DIRECTORY.replace("$MLN_USR", "")
            OUTPUT_DIRECTORY = OUTPUT_DIRECTORY.rstrip("\n")
            # if the path for output directory does not exist, a folder is created
            OUTPUT_DIRECTORY_path_exist = os.path.isdir(OUTPUT_DIRECTORY)
            if OUTPUT_DIRECTORY_path_exist==False:
                os.mkdir(os.path.join(MLN_USR, OUTPUT_DIRECTORY))
            if not os.path.isdir(OUTPUT_DIRECTORY):
                raise FileNotFoundError("==> Output directory not found.\n")

            USERNAME = lines[1].split("=")[1]
            USERNAME = USERNAME.rstrip("\n")

            # creating a hash table file name
            ana_hash_table_fileName = ana_hash_table_file_name(
                USERNAME, 
                config_file_first_portion[0], 
                ana_extension_layer_name.hash_table_file.value
            )
            # join hash table file with complete path
            ana_hash_table_config = os.path.join(system_folder, ana_hash_table_fileName)
            exporting_pickled_dict_path = ana_hash_table_config

            dictClassObject = ana_dict_class()

            # printing all the file headers
            print("OUTPUT_DIRECTORY : ", OUTPUT_DIRECTORY)
            print("USERNAME : ", USERNAME)
            # print("INPUT_LAYER_PATH_FROM_DICT : ", INPUT_LAYER_PATH_FROM_DICT)
            print("\n")

            ana_log_file_name = ana_log_file_naming(
                USERNAME,
                config_file_first_portion[0],
                ana_extension_layer_name.config_file.value,
                ana_extension_layer_name.log_file.value
            )
            # join log file with complete path
            ana_log_file = os.path.join(ana_log_folder, ana_log_file_name)
            
            layername = ""
            # initialize an empty dictionary to store the layers.
            layers = {}
            pathhh = {}
            gen_file_name_from_config = ""
            found_Dictionary = False
            map_file_path = MLN_USR + "/" + "primary_key_converter_for_inputfiles" + "/"
            filesToOutput = []

            #Gets the last modification time of the config file, and converts it into YYYYMMDDHHMMSS format.
            ana_config_file_getmtime = os.path.getmtime(configFile_to_open)
            datetime_object = datetime.datetime.fromtimestamp(ana_config_file_getmtime)
            ana_config_file_last_modified_time = datetime_object.strftime("%Y%m%d%H%M%S")
            
            #Retrieves the latest time this config file was successfully analyzed from the bin file, already in YYYYMMDDHHMMSS format. If the bin file doesn't exist, set the last analyzed time to 0 to force analysis.
            try:
                with open(os.path.join(system_folder, USERNAME+ "_"+ config_file_first_portion[0] + "_ana.bin"), 'rb') as file:
                    data = pickle.load(file)
                    latest_time = '0'
                    for value in data.values():
                        if value["time_analyzed"] > latest_time:
                            latest_time = value["time_analyzed"]
        
                    ana_last_analyzed_time = latest_time
            except (FileNotFoundError, EOFError):
                ana_last_analyzed_time = '0'
            
            #Retrieves the last time the layers were generated from the bin file, and converts to YYYYMMDDHHMMSS format. If bin file is not found, this means that layers have not been generated- this error will be handled later in the code.
            try:
                with open(os.path.join(system_folder, USERNAME+ "_"+ config_file_first_portion[0] + "_gen.bin"), 'rb') as file:
                    ser_data = file.read()
                    data = pickle.loads(ser_data)
                    key = next(iter(data.keys()))
                    
                    os.rename('ana_parser_class.py', 'parser_class.py')
                    gen_last_generated_time = pickle.loads(data[key])._SYSTEM_TIME
                    os.rename('parser_class.py', 'ana_parser_class.py')
                    
                    datetime_object = datetime.datetime.strptime(gen_last_generated_time, "%a %b %d %H:%M:%S %Y")
                    gen_last_generated_time = datetime_object.strftime("%Y%m%d%H%M%S")
                    
            except (FileNotFoundError, EOFError):
                gen_last_generated_time = '0'
            
            print(f"ana modified time: {ana_config_file_last_modified_time},\n ana analyzed time: {ana_last_analyzed_time},\n gen generated time:{gen_last_generated_time}")
            
            #Check if the analysis is more recent than the last layer generation and that the analysis is more recent than the last time the config file was modified. If so, no need to reanalyze.
            if (ana_last_analyzed_time > gen_last_generated_time and ana_last_analyzed_time > ana_config_file_last_modified_time):
                print(f"The config file has not been modified since the last analysis.")
                return_code = 7
                print("Not conducting analysis.")
                conduct_analysis = False
            else:
                print("Conducting analysis.")
                conduct_analysis = True
                
            # if (ana_last_analyzed_time > gen_last_generated_time) or (ana_config_file_last_modified_time > gen_last_generated_time):
            #     #If so, then check if the analysis is more recent than the last time the ana config file was modified.
            #     if ana_last_analyzed_time > ana_config_file_last_modified_time:
            #         print(f"The config file has not been modified since the last analysis.")
            #         #ana_log_file_object.ana_msg_log_file(ana_log_file, f"The config file has not been modified since the last analysis. Analysis results are up to date in the ../analysis_results folder.")
            #         return_code = 7
            #         print("Not conducting analysis.")
            #         conduct_analysis = False
            #     else: 
            #         print("Conducting analysis.")
            #         conduct_analysis = True
            # else:
            #     print("Conducting analysis.")
            #     conduct_analysis = True
                
            if conduct_analysis:
                # open a log file for the configuration file
                ana_log_file_object.ana_open_log_file_for_each_layer(ana_log_file)  
                for line in lines:
                    # create parser object
                    # ana_ParserObject = Parser()
                    if line.startswith('IMPORT'):
                        gen_file_name_from_config = line.split()[1].rstrip("\n")  # PRINTS "small-64Movies.gen" that is the name from IMPORT line in CONFIG file
                        layername = gen_file_name_from_config[:-len('.gen')]
                        ana_binary_pathname = '$MLN_USR/system/' + USERNAME + '_' + layername + '_gen' + '.bin' # currently the path is something like $MLN_USR/system/ira_accident_gen.bin
                        pathhh[gen_file_name_from_config] = MLN_USR + ana_binary_pathname.replace("$MLN_USR", "")   # dictionary path contains the path to the binary file  
                        
                        # check if the dictionary path exists
                        if not os.path.exists(pathhh[gen_file_name_from_config]):
                            found_Dictionary = False
                            ana_log_file_object.ana_msg_log_file(ana_log_file, f"No dictionary found. Please execute the {config_file_first_portion[0]}.gen to generate the layers before performing analysis.")
                            ana_log_file_object.ana_ending_msg_log_file_fail(ana_log_file)
                            ana_del_file_tmp_dir(tmp_folder)
                            print(f"No dictionary found. Please execute the {config_file_first_portion[0]}.gen to generate the layers before performing analysis.")
                            return_code = 6
                            break
                        
                        found_Dictionary = True
                        layers[gen_file_name_from_config] = gen_file_name_from_config[:-len('.gen')]
                        retrieveLayers = False
                        
                    if line.startswith("INPUT_DIRECTORY"):
                        INPUT_LAYER_PATH_FROM_DICT = None
                        retrieveLayers = True
                    
                    if line.startswith("ANALYSIS_NAME"):    
                        analysisNAME = line.split("=")[1].strip()
                        # setting the analysis name in the dictionary
                        dictClassObject.set_analysis_name(analysisNAME)
                    if line.startswith("ANALYSIS_EXPRESSION"):
                        analysisEXPRESSION = line.split("=")[1].strip()
                        
                        COMMUNITY_TYPE_ALGO = analysisEXPRESSION.split("(")[0]
                        # setting the analysis type in the dictionary
                        dictClassObject.set_analysis_type(COMMUNITY_TYPE_ALGO)
                        
                        layer_name = analysisEXPRESSION.split("(")[1]
                        LAYER_NAME = layer_name.split(")")[0]
                        # store the path that matches the layer name 
                        if found_Dictionary:
                            try:
                                os.rename('ana_parser_class.py', 'parser_class.py')
                                INPUT_LAYER_PATH_FROM_DICT = ana_get_INPUT_layer_path(pathhh[gen_file_name_from_config], LAYER_NAME)                         
                                os.rename('parser_class.py', 'ana_parser_class.py')
                                

                            except Exception as e:
                                print(f"An error occurred while reading pickle file: {str(e)} \n")
                                ana_log_file_object.ana_msg_log_file(ana_log_file, f"An error occurred while reading pickle file: {str(e)} \n")
                        # printing the details of variables
                        print("ANALYSIS_NAME : ", analysisNAME)

                        return_code = postfix_evaluator(analysisEXPRESSION, gen_file_name_from_config, pathhh, INPUT_LAYER_PATH_FROM_DICT, OUTPUT_DIRECTORY, ana_log_file_object, ana_log_file, USERNAME, ana_hash_table, config_file_first_portion[0], analysisNAME, map_file_path, filesToOutput, retrieveLayers)
                        """
                        Return Codes:
                        0 - Success
                        1 - Postfix Conversion Failed
                        2 - Error occurred during analysis - generic
                        3 - Ecom files do not exist (CE-AND called after CV-AND)
                        4 - Error during c++ (binary operator) code call
                        5 - ANALYSIS_NAME in config file is the same as the expression/subexpression
                        6 - No dictionary found.
                        7 - Results are already up to date.
                        """
                            
                        if return_code == 0:
                            print("Evaluation success.")
                            ana_log_file_object.ana_ending_msg_log_file_success(ana_log_file)
                            #Dumps results into the pickle file
                            pickle_directory = OUTPUT_DIRECTORY.rsplit('/', 2)[0] + "/system"
                            pickle_directory = pickle_directory + "/" + USERNAME + "_" + config_file_first_portion[0] + "_ana.bin"
                            with open(pickle_directory, "wb") as df:
                                pickle.dump(ana_hash_table, df)    
                        elif return_code == 7:
                            pass              
                        else:
                            print(f"Evaluation fail. Error code {return_code}")
                            ana_log_file_object.ana_ending_msg_log_file_fail(ana_log_file)
                            break
        #Asantra (06/07): Moved return_code outside the if_else block. returns a value in any scenario - success or failure
        if return_code == 0: 
            if filesToOutput:
                ana_log_file_object.ana_msg_log_file(ana_log_file, f"Attempting to move files to analysis_results directory...")
                moveFilesToOutputDirectory(filesToOutput, OUTPUT_DIRECTORY)
                ana_log_file_object.ana_msg_log_file(ana_log_file, f"Successfully moved files...")
        #ana_del_file_tmp_dir(tmp_folder)
        return return_code
        #print(filesToOutput)
        #print(OUTPUT_DIRECTORY)
        #from pprint import pprint
        #pprint(ana_hash_table)
        
