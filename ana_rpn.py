from ana_Community_Detection_Algorithms import *
from ana_FileProcessing import *
from ana_algo_funcs import *
import datetime
from os import path
import time

import re
def infix_to_postfix( string ):

    operators = {
        'binary': set(['CE-AND', 'CV-AND', 'CE-OR', 'AND', 'OR']),
        'unary': set(['Louvain', 'Infomap', 'Fastgreedy', 'Walktrap', 'Multilevel', 'LeadingeiGenvector', 'NOT'])
    }

    #TODO: Operators: MWMT-WE MWMT-WH MWMT-WD etc.
    #                 CE-OR-e CE-OR-f

    Priority = {'NOT':1,'AND':2, 'OR':2, 'Louvain':3, 'Infomap':3, 'Fastgreedy':3, 'Walktrap':3, 'Multilevel':3, 'LeadingeiGenvector':3, 'CE-AND':4, 'CV-AND':4, 'CE-OR':4}
    #Lower number means higher priority

    stack, result = [], []

    tokens = re.findall(r'\w+-\w+|\w+|\(|\)', string)
    
    for token in tokens:
        if token not in operators['binary'] and token not in operators['unary'] and token != '(' and token != ')':
            if(tokens[tokens.index(token) + 1]  == '('):
                raise ValueError(f"Invalid operator \"{token}\". Typo?")
            result.append(token)
            last_token_type = 'operand'

        elif token == '(':
            stack.append('(')
            last_token_type = None

        elif token == ')':
            while stack and stack[-1]!= '(':
                s = stack.pop()
                result.append(s)
            stack.pop()
            last_token_type = 'operand'
        else:
            if token in operators['unary'] or token in operators['binary']:
                if (token == 'AND' or token == 'NOT' or token == 'OR') and stack[-1] in operators['unary'] and stack[-1] != 'NOT':
                    raise ValueError(f"Invalid expression. Check your use of operator \"{token}\"")
                while stack and stack[-1] != '(' and Priority[token]>=Priority[stack[-1]]:
                    s = stack.pop()
                    result.append(s)
                stack.append(token)
                if token in operators['unary']:
                    last_token_type = 'unary'
                else: 
                    last_token_type = 'binary'
            else:
                raise ValueError(f"Invalid token: {token}")

    while stack:
        s = stack.pop()
        result.append(s)

    if last_token_type == 'binary':
        raise ValueError("Invalid expression, last token is a binary operator without a valid operand.")
    
    
    return result

#Prints the converted postfix stack. Used for Debugging.
def printStack(exp):

    
    stack = infix_to_postfix(exp)
    print("initial expression:" , exp)
    print(f'final stack: { " ".join (stack)}')


"""
    Converts an analysis expression into postfix notation and evaluates the expression while storing results in the proper directory.

    :param analysis_expression: original analysis expression, in infix notation
    :param INPUT_LAYER_PATH_FROM_DICT: The path to the layer (.net file)
    :param OUTPUT_DIRECTORY: final and primitive results (not intermediate results) should be stored here
    :param ana_log_file_object: object for log file. used for writing to the log file
    :param ana_log_file: log file path
    :param USERNAME: username used for file naming
    :param ana_hash_table: final and primitive results (not intermediate results) should be stored here
    :param ana_config_file_name: the name of the ana config file
    :param analysis_name_from_config: the name of the analysis, specified by the user in the ana config file
    :param map_file_path: the path to the map file
    :param filesToOutput: this list stores the results that should be moved to the analysis_results folder. The paths to the results are kept here until we know the entire config file is successful, then they are all moved.
    :param retrieveLayers: boolean. This is true if we need to retrieve the layers on the fly while evaluating an expression. currently only used in All-Airlines.ana
"""
def postfix_evaluator(analysis_expression, gen_file_name_from_config, pathhh, INPUT_LAYER_PATH_FROM_DICT, OUTPUT_DIRECTORY, ana_log_file_object, ana_log_file, USERNAME, ana_hash_table, ana_config_file_name, analysis_name_from_config, map_file_path, filesToOutput, retrieveLayers): 
    import subprocess
    from ana_MainDriver import ana_get_INPUT_layer_path
    operators = {
        'binary': list(['CE-AND', 'CV-AND', 'CE-OR', 'AND']),
        'unary': list(['Louvain', 'Infomap', 'Fastgreedy', 'Walktrap', 'Multilevel', 'LeadingeiGenvector', 'NOT'])
    }
    original_expression = analysis_expression
    #Convert expression to postfix
    try:
        stack = infix_to_postfix(analysis_expression)
    except Exception as ex:
        ana_log_file_object.ana_msg_log_file(ana_log_file, f"Postfix conversion failed. More info: {ex}") 
        return 1
        
    evalStack = []
    tmp_directory = OUTPUT_DIRECTORY.rsplit('/', 2)[0] + "/tmp"
    relative_output_directory =  "../" +OUTPUT_DIRECTORY.rsplit('/', 3)[1] + "/" + OUTPUT_DIRECTORY.rsplit('/', 3)[2] + "/" + OUTPUT_DIRECTORY.rsplit('/', 3)[3]
    applicationName = OUTPUT_DIRECTORY.rsplit('/', 3)[2]
    relative_tmp_directory = "../"  + tmp_directory.rsplit('/', 3)[2] + "/" + tmp_directory.rsplit('/', 3)[3]
    #Evaluates postfix stack
    for index, token in enumerate(stack):
        if token not in operators['binary'] and token not in operators['unary']:
            evalStack.append(token) #Pushes layer onto evaluation stack, waits for Unary Operator.

        #Performs unary operation and stores results accordingly
        elif token in operators['unary']:
            layername = evalStack.pop()
            algo = token 
            analysisname = layername + "_" + algo.lower()
            if analysisname == analysis_name_from_config:
                print(f"An error occurred during {original_expression} analysis: Invalid ANALYSIS_NAME in analysis config file, can not be the same as expression")
                ana_log_file_object.ana_msg_log_file(ana_log_file, f"An error occurred during {original_expression} analysis: Invalid ANALYSIS_NAME in analysis config file, can not be the same as expression")
                #delete_files(ana_hash_table)
                return 5
            subexpression = algo + "(" + layername + ")" 
            try:
                
                
                if pathhh:
                    from ana_MainDriver import ana_get_INPUT_layer_path
                    INPUT_LAYER_PATH_FROM_DICT = ana_get_INPUT_layer_path(pathhh[gen_file_name_from_config], layername)
                    
                #This is used for config files where layers are used from multiple .net files. The input layers in this case are determined during each algo evaluation. currently only used in All-Airlines.ana 
                if retrieveLayers:
                    INPUT_LAYER_PATH_FROM_DICT = OUTPUT_DIRECTORY.rsplit('/', 1)[0] + "/layers_generated"
                    INPUT_LAYER_PATH_FROM_DICT = os.path.join(INPUT_LAYER_PATH_FROM_DICT, layername + ".net")
                        
                print('Performing', algo, "on layer", layername)
                
                #If algorithm is one of the 6 algos i.e. louvain, infomap etc. then output should be stored in the OUTPUT_DIRECTORY, else (i.e. if algo is NOT) they should be stored in tmp
                if algo in operators['unary'][:6]:
                    current_output_directory = OUTPUT_DIRECTORY
                    should_output_file = True
                else:
                    current_output_directory = tmp_directory
                    should_output_file = False
                

                #Calls algo and records time elapsed
                if algo in operators['unary'][:6]:
                    start_time = time.time()
                    comm_error = community_detection(algo , INPUT_LAYER_PATH_FROM_DICT, tmp_directory, analysisname, ana_log_file_object, ana_log_file, USERNAME, layername, ana_config_file_name)
                    end_time = time.time()
                    if comm_error == -1:
                        return 6
                    time_elapsed = str(round(end_time - start_time, 4))
                else:
                    pass
                    #TODO: Implement NOT code
                output_path = tmp_directory + "/" + USERNAME + "_" + ana_config_file_name + "_" + analysisname
                print("analysisname:",analysisname)
                # Retrieves results from ecom file.
                file_to_open = output_path + ".ecom"
                numNodes, numEdges, numCommunities = readResultsFromFile(file_to_open)
                
                ana_log_file_object.ana_msg_log_file(ana_log_file, "Information regarding the analyzed layer:\n\tDestination Folder: " + relative_output_directory + "\n\tGeneration time (in seconds): " + time_elapsed + "\n\tNumber of Nodes: " + str(numNodes) + "\tNumber of Edges: " + str(numEdges) + "\tNumber of Communities: " + str(numCommunities))

                #Adds results to dictionary if the result should be moved to the analysis results output directory and not kept in temp directory
                ecom_output = output_path  + ".ecom"
                vcom_output = output_path + ".vcom"
                
                #Kevin 7/6/24: If retrieveLayers is true, then the map file will not be named according to ana_config_file_name, rather it will be named under the application name.
                mapNameToCheck = applicationName if retrieveLayers else ana_config_file_name
                if os.path.isfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map")):
                    path_to_map_file = shutil.copyfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map") , os.path.join(map_file_path, USERNAME + "_" + ana_config_file_name + "_" + analysisname + ".map"))
                else:
                    path_to_map_file = None
                
                #If this is the last operator in the stack, this should be stored as the analysis_name_from_config
                if(index == len(stack) - 1):
                    ecom_output = shutil.copyfile(ecom_output, os.path.join(tmp_directory, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".ecom") )
                    vcom_output = shutil.copyfile(vcom_output, os.path.join(tmp_directory, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".vcom") )
                    
                    if os.path.isfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map")):
                        path_to_map_file = shutil.copyfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map") , os.path.join(map_file_path, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".map"))
                    else:
                        path_to_map_file = None
                    
                    time_analyzed = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    ana_hash_table[analysis_name_from_config] = {
                        "analysis_expression" : original_expression,
                        "path_to_ecom_file" : os.path.join(OUTPUT_DIRECTORY, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".ecom"),
                        "path_to_vcom_file" : os.path.join(OUTPUT_DIRECTORY, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".vcom"),
                        "path_to_map_file" : path_to_map_file,
                        "time_analyzed" : time_analyzed
                    }
                    print(f"{analysisname} time: {time_analyzed}")
                    filesToOutput.append(ecom_output)
                    filesToOutput.append(vcom_output)
                #If not the last operator in the stack, this should be stored using the convention. (Username_anaconfigfilename_analysisname.com)    
                elif should_output_file == True:
                    time_analyzed = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    ana_hash_table[analysisname] = {
                                "analysis_expression" : subexpression,
                                "path_to_ecom_file" : os.path.join(OUTPUT_DIRECTORY, USERNAME + "_" + ana_config_file_name + "_" + analysisname + ".ecom"),
                                "path_to_vcom_file" : os.path.join(OUTPUT_DIRECTORY, USERNAME + "_" + ana_config_file_name + "_" + analysisname + ".vcom"),
                                "path_to_map_file" : path_to_map_file,
                                "time_analyzed" : time_analyzed
                            }
                    print(f"{analysisname} time: {time_analyzed}")
                    filesToOutput.append(ecom_output)
                    filesToOutput.append(vcom_output)
                
                
                
                evalStack.append(output_path)
            except Exception as ex:
                print(ex)
                ana_log_file_object.ana_msg_log_file(ana_log_file, f"An error occurred during analysis: {analysisname}. More info: {ex}")
                #delete_files(ana_hash_table)
                return 2

        
        elif token in operators['binary']:
            try:
                operator = token 
                ecom_output = None
                vcom_output = None
                file = operator + ".conf"  
                operand1 = evalStack.pop() 
                operand2 = evalStack.pop() 

                #Creates the config file for the operator. Returns false if failed. Sets the path to both input files.
                success, path_to_1, path_to_2 = createConfigFile(operator, operand1, operand2, ana_log_file_object, ana_log_file, file, getNumNodesFromNetFile(INPUT_LAYER_PATH_FROM_DICT))
                if success == False:
                    #delete_files(ana_hash_table)
                    return 3

                #Retrieves analysisname from ecom/vcom file
                analysisname1 = getAnalysisName(path_to_1)
                analysisname2 = getAnalysisName(path_to_2)

                #analysis name format: layer1_operator_layer2
                analysisname = analysisname1 + "_" + operator + "_" + analysisname2 

                ana_log_file_object.ana_msg_log_file(ana_log_file, "Analysis on layer " + analysisname + " is initiated.")
                print("Analysis on layer " + analysisname + " is initiated.")

                start_time = time.time()
                returncode = subprocess.call(["./" + operator]) #calls c++ code for binary operator. returns 0 for successful evaluation.
                end_time = time.time()
                time_elapsed = str(round(end_time - start_time, 4))
                
                if returncode != 0: #Catch c++ code error
                    print(f"Error: {operator} failed. Error code: {returncode}")
                    ana_log_file_object.ana_msg_log_file(ana_log_file, f"Error: {operator} failed. Error code: {returncode}. Analysis is unsuccessful.")
                    #delete_files(ana_hash_table)
                    return 4
                print(f"--- {operator} COMPLETED ---\n\n")

                ecom_output = analysisname + ".ecom"
                vcom_output = analysisname + ".vcom"
                
                if operator != 'CV-AND': # CV-AND will not produce a .ecom file
                    ecom_output = setFilePath(ecom_output, USERNAME)               
                vcom_output = setFilePath(vcom_output, USERNAME)

                if operator == 'CE-AND':
                    file_to_read = ecom_output
                elif operator == 'CV-AND':
                    file_to_read = vcom_output
                numNodes, numEdges, numCommunities = readResultsFromFile(file_to_read) # Reads results from the proper file and sets variables



                analysisname = analysisname1 + "_" + operator + "_" + analysisname2

                mapNameToCheck = applicationName if retrieveLayers else ana_config_file_name
                if os.path.isfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map")):
                    path_to_map_file = shutil.copyfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map") , os.path.join(map_file_path, USERNAME + "_" + ana_config_file_name + "_" + analysisname + ".map"))
                else:
                    path_to_map_file = None

                #If this is a subexpression, store in the tmp directory. Else (this is the final result), rename the file result to analysis_name_from_config and store it
                if not (index == len(stack) - 1):
                    current_output_directory = tmp_directory
                    ecom_output, vcom_output = moveEcomVcomFilesToDirectory(ecom_output, vcom_output, current_output_directory, operator)
                    ana_log_file_object.ana_msg_log_file(ana_log_file, "Done.\nInformation regarding the analyzed layer:\n\tDestination Folder: " + relative_tmp_directory + "\n\tGeneration time (in seconds): " + time_elapsed + "\n\tNumber of Nodes: " + str(numNodes) + "\tNumber of Edges: " + str(numEdges) + "\tNumber of Communities: " + str(numCommunities))

                else:
                    current_output_directory = tmp_directory
                    if operator != 'CV-AND':
                        os.rename(ecom_output, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".ecom")
                        ecom_output = USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".ecom"
                        ecom_output = shutil.move(ecom_output, os.path.join(tmp_directory, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".ecom") )
                        filesToOutput.append(ecom_output)

                    os.rename(vcom_output, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".vcom")
                    vcom_output = USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".vcom"
                    vcom_output = shutil.move(vcom_output, os.path.join(tmp_directory, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".vcom") )
                    filesToOutput.append(vcom_output)
                    
                    if os.path.isfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map")):
                        path_to_map_file = shutil.copyfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map") , os.path.join(map_file_path, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".map"))
                    else:
                        path_to_map_file = None

                    time_analyzed = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    ana_hash_table[analysis_name_from_config] = {
                        "analysis_expression" : original_expression,
                        "path_to_ecom_file" : os.path.join(OUTPUT_DIRECTORY, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".ecom"),
                        "path_to_vcom_file" : os.path.join(OUTPUT_DIRECTORY, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".vcom"),
                        "path_to_map_file" : path_to_map_file,
                        "time_analyzed" : time_analyzed
                    }
                    print(f"{analysisname} time: {time_analyzed}")
                    ana_log_file_object.ana_msg_log_file(ana_log_file, "Done.\nInformation regarding the analyzed layer:\n\tDestination Folder: " + relative_output_directory + "\n\tGeneration time (in seconds): " + time_elapsed + "\n\tNumber of Nodes: " + str(numNodes) + "\tNumber of Edges: " + str(numEdges) + "\tNumber of Communities: " + str(numCommunities))

                    


                output_path = tmp_directory + "/" + USERNAME + "_" + analysisname
                evalStack.append(output_path)

            except Exception as ex:
                print(f"An error occurred during {token} analysis: {ex}")
                ana_log_file_object.ana_msg_log_file(ana_log_file, f"An error occurred during {token} analysis.")
                #delete_files(ana_hash_table)
                return 2
    print(f"Analysis on layer {analysisname} Successful.\n\n")
    

    return 0


if __name__ == '__main__':
    exp = '((Louvain(L1) CV-AND Louvain(NOT L2)) CE-AND (Louvain(L3) CE-OR Louvain(L4)))'

    exp = 'Loeuvain(different_time_period) CE-AND Louvain(different_time_period)'
    exp = 'Louvain(NOT layer1) CE-AND (Louvain(layer2 OR layer1) CV-AND Infomap(layer3 AND layer1))'

    printStack(exp)