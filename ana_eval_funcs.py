import shutil
from typing import Tuple
import os
import datetime
import time


#Used in binary operator evaluation. Given path to ecom file and vcom file, move them to the proper path they belong in. Operator is needed since CV-AND will not produce a .ecom file
def moveEcomVcomFilesToDirectory(ecom_output, vcom_output, directory, operator):
    if operator != 'CV-AND': # CV-AND will not produce a .ecom file
        shutil.move(ecom_output, os.path.join(directory, ecom_output)) #Move ecom & vcom from pwd to given directory
        ecom_output = os.path.join(directory, ecom_output)
        
    shutil.move(vcom_output, os.path.join(directory, vcom_output))
    vcom_output = os.path.join(directory, vcom_output)
    return ecom_output, vcom_output

#Given path of file to read (either ecom or vcom), return the numNodes, numCommunities, and numEdges.
def readResultsFromFile(file_to_read) -> Tuple[str, str, str]:
    read = open(file_to_read, 'r')
    for i, line in enumerate(read):
        if i == 3:
                numNodes = str(line)
        elif i == 5: 
            numCommunities = str(line)
        elif i == 7: 
            if file_to_read.endswith(".ecom"):
                numEdges = str(line)
            else:
                numEdges = "0\n"
        elif i > 7:
            break
    read.close()
    return numNodes, numEdges, numCommunities

#Given an ecom/vcom file, return the analysisname.
def getAnalysisName(filepath) -> str:
    with open(filepath) as file_path:
        for i, line in enumerate(file_path):
            if i == 1: #This line contains the analysis name
                analysisname = line.strip()
                return analysisname
            


#Used after calling c++ code. renames the file that is output by the c++ code and updates the variable holding that file's name.
def setFilePath(filepath, USERNAME) -> str:
    os.rename(filepath, USERNAME + "_" + filepath)  #updates name of file to include username 
    filepath = USERNAME + "_" + filepath #updates variable to new path 
    return filepath

#Used before calling c++ code. Checks if ecom files exist for both operands.
def checkEcomFilesExist(path_to_1, path_to_2, ana_log_file_object, ana_log_file) -> bool:
    ecom_1_exists = os.path.exists(path_to_1)
    ecom_2_exists = os.path.exists(path_to_2)

    if(ecom_1_exists == False or ecom_2_exists == False):
        ana_log_file_object.ana_msg_log_file(ana_log_file, "Analysis failed. Necessary ecom files do not exist. Tried calling CE-AND after CV-AND?\n")
        print("Analysis failed. Necessary ecom files do not exist. Tried calling CE-AND after CV-AND?\n")
        return False
    else:
        return True
    
#If analysis fails, we don't want to store any of the ecom,vcom files corresponding to that analysis. This deletes them.    
def delete_files(ana_hash_table):
    for value in ana_hash_table.values():
        ecom_file = value.get("path_to_ecom_file")
        vcom_file = value.get("path_to_vcom_file")
        if ecom_file and os.path.exists(ecom_file):
            os.remove(ecom_file)
        if vcom_file and os.path.exists(vcom_file):
            os.remove(vcom_file)
            
def moveFilesToOutputDirectory(filesToOutput, OUTPUT_DIRECTORY):
    for file in filesToOutput:
        shutil.copy(file, OUTPUT_DIRECTORY)
        
def getNumNodesFromNetFile(netFile):
    with open(netFile) as file:
        for i, line in enumerate(file):
            if i == 1: #This line contains the number of nodes in the layer.
                numNodes = line
                return numNodes
        
def ana_hash_table_entry(original_expression, OUTPUT_DIRECTORY, USERNAME, ana_config_file_name, analysis_name, path_to_map_file, time_analyzed):
    
    output = {
                "analysis_expression" : original_expression,
                "path_to_ecom_file" : os.path.join(OUTPUT_DIRECTORY, USERNAME + "_" + ana_config_file_name + "_" + analysis_name + ".ecom"),
                "path_to_vcom_file" : os.path.join(OUTPUT_DIRECTORY, USERNAME + "_" + ana_config_file_name + "_" + analysis_name + ".vcom"),
                "path_to_map_file" : path_to_map_file,
                "time_analyzed" : time_analyzed
            }
    return output


def evaluateCommDetectionAlgos(algo, INPUT_LAYER_PATH_FROM_DICT, tmp_directory, analysisname, ana_log_file_object, ana_log_file, USERNAME, layername, ana_config_file_name, applicationName, retrieveLayers, relative_output_directory, map_file_path, analysis_name_from_config, is_last_index, ana_hash_table, filesToOutput, OUTPUT_DIRECTORY, original_expression, subexpression):
    from ana_algo_funcs import community_detection
    start_time = time.time()
    comm_error = community_detection(algo, INPUT_LAYER_PATH_FROM_DICT, tmp_directory, analysisname, ana_log_file_object, ana_log_file, USERNAME, layername, ana_config_file_name)
    end_time = time.time()
    
    
    if comm_error == -1:
        delete_files(ana_hash_table)
        raise ValueError(6)
        # return 6
    
    time_elapsed = str(round(end_time - start_time, 4))
    output_path = os.path.join(tmp_directory, f"{USERNAME}_{ana_config_file_name}_{analysisname}")
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
    if(is_last_index):
        ecom_output = shutil.copyfile(ecom_output, os.path.join(tmp_directory, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".ecom") )
        vcom_output = shutil.copyfile(vcom_output, os.path.join(tmp_directory, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".vcom") )
        
        if os.path.isfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map")):
            path_to_map_file = shutil.copyfile(os.path.join(map_file_path, USERNAME + "_" + mapNameToCheck + "_" + layername + ".map") , os.path.join(map_file_path, USERNAME + "_" + ana_config_file_name + "_" + analysis_name_from_config + ".map"))
        else:
            path_to_map_file = None
        
        time_analyzed = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        ana_hash_table[analysis_name_from_config] = ana_hash_table_entry(original_expression, OUTPUT_DIRECTORY, USERNAME, ana_config_file_name, analysis_name_from_config, path_to_map_file, time_analyzed)
        print(f"{analysisname} time: {time_analyzed}")
        filesToOutput.append(ecom_output)
        filesToOutput.append(vcom_output)
    #If this is not the last operator in the stack, this should be stored using the convention. (Username_anaconfigfilename_analysisname.com)    
    else:
        time_analyzed = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        ana_hash_table[analysis_name_from_config] = ana_hash_table_entry(subexpression, OUTPUT_DIRECTORY, USERNAME, ana_config_file_name, analysisname, path_to_map_file, time_analyzed)
        print(f"{analysisname} time: {time_analyzed}")
        filesToOutput.append(ecom_output)
        filesToOutput.append(vcom_output)
    
    return output_path
    