from ana_Community_Detection_Algorithms import *
from ana_FileProcessing import getNumNodesFromNetFile

def anaLouvainAlgo(INPUT_layer_path_from_dict, outputDirectory, analysisNAME, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name):
    # Read and process input file to create Graph
    Graph, edges = create_nx_Graph(INPUT_layer_path_from_dict)
    # Louvain function
    result, time, numNodes, numEdges, numCommunities = louvain(Graph)

    # Write Louvain results
    writeResultsLouvain(result, outputDirectory, Graph.edges(), analysisNAME, getNumNodesFromNetFile(INPUT_layer_path_from_dict).strip(), userName_from_ana_config_file, gen_configFile_name, ana_config_file_name)
    print("--- LOUVAIN COMPLETED ---\n")
    return numNodes, numEdges, numCommunities

def anaInfomapAlgo(INPUT_layer_path_from_dict, outputDirectory, analysisNAME, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name):
    # Read and process input file to infomap
    im_result, edges, time = infomapAlgo(INPUT_layer_path_from_dict)
    numNodes = im_result.num_nodes
    numEdges =  len(edges)
    numCommunities = im_result.num_top_modules
    numNodes = getNumNodesFromNetFile(INPUT_layer_path_from_dict).strip()
    # Write Infomap results to .vcom and .ecom files
    writeResultsInfomap(im_result, outputDirectory, edges, analysisNAME, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name, numNodes)
    print("--- INFOMAP COMPLETED ---\n")
    return numNodes, numEdges, numCommunities

def anaWalktrapAlgo(INPUT_layer_path_from_dict, outputDirectory, analysisNAME, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name):
    # Send graph location to function and returns ig graph
    Graph, edges, edgeWeights = create_ig_Graph(INPUT_layer_path_from_dict)
    numNodes = Graph.vcount()
    numEdges = len(edges)
    # WALKTRAP function
    result, time, numCommunities = walktrap(Graph, edgeWeights)
    writeResults(result, outputDirectory, edges, analysisNAME, "Walktrap", time, numNodes, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name)
    print("--- WALKTRAP COMPLETED ---\n")
    return numNodes, numEdges, numCommunities

def anaFastgreedyAlgo(INPUT_layer_path_from_dict, outputDirectory, analysisNAME, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name):
    # Send graph location to function and returns ig graph
    Graph, edges, edgeWeights = create_ig_Graph(INPUT_layer_path_from_dict)
    numNodes = Graph.vcount()
    numEdges = len(edges)
    # FASTGREEDY function
    result, time, numCommunities = fastgreedy(Graph, edgeWeights)
    writeResults(result, outputDirectory, edges, analysisNAME, "FastGreedy", time, numNodes, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name)
    print("--- FASTGREEDY COMPLETED ---\n")
    return numNodes, numEdges, numCommunities

def anaLeadingeigenvectorAlgo(INPUT_layer_path_from_dict, outputDirectory, analysisNAME, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name):
    # Send graph location to function and returns ig graph
    Graph, edges, edgeWeights = create_ig_Graph(INPUT_layer_path_from_dict)
    numNodes = Graph.vcount()
    # LEADING EIGEN VECTOR function
    result, time = leadingeigenvector(Graph, edgeWeights)
    # calculating edges and no. of comms
    numEdges = len(edges)
    numCommunities = len(result)
    # writing results to file
    writeResults(result, outputDirectory, edges, analysisNAME, "LeadingEigenVector", time, numNodes, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name)
    print("--- LEADING EIGEN VECTOR COMPLETED ---\n")
    return numNodes, numEdges, numCommunities

def anaMultilevelAlgo(INPUT_layer_path_from_dict, outputDirectory, analysisNAME, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name):
    # Send graph location to function and returns ig graph
    Graph, edges, edgeWeights = create_ig_Graph(INPUT_layer_path_from_dict)
    numNodes = Graph.vcount()
    # MULTILEVEL function
    result, time = multilevel(Graph, edgeWeights)
    # calculating edges and no. of comms
    numEdges = len(edges)
    numCommunities = len(result)
    writeResults(result, outputDirectory, edges, analysisNAME, "Multilevel", time, numNodes, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name)
    # append the result of louvain algorithm to the resultsList for comparision function later
    # resultsList.append([result, time])
    print("--- MULTILEVEL COMPLETED ---\n")
    return numNodes, numEdges, numCommunities

# dictionary to store the algorithm's functions to call
algorithmFunctionsDict = {
    "louvain": anaLouvainAlgo,
    "infomap": anaInfomapAlgo,
    "walktrap": anaWalktrapAlgo,
    "fastgreedy": anaFastgreedyAlgo,
    "leadingeigenvector": anaLeadingeigenvectorAlgo,
    "multilevel": anaMultilevelAlgo
}

"""
    Detects communities in the input graph using the specified community detection algorithm.

    :param community_type_algo: The community detection algorithm to use.
    :param INPUT_layer_path_from_dict: The path to the input graph file.
    :param output_directory: The directory to write the output files to.
    :param analysis_name: The name of the analysis.
    :param ana_log_file_object: The log file object.
    :param log_file: The path to the log file.
    :return: The number of nodes, edges, and communities in the input graph.
"""
def community_detection(COMMUNITY_TYPE_ALGO, INPUT_layer_path_from_dict, outputDirectory, analysisNAME, ana_log_file_object, log_file, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name):
    try:
        # the msg indicates that analysis is initialized.
        ana_log_file_object.ana_msg_log_file(log_file,"Analysis on layer " +  analysisNAME + " is Initiated.")

        # check if the input file exists
        if not os.path.exists(INPUT_layer_path_from_dict):
            ana_log_file_object.ana_msg_log_file(log_file, f"Imported generated layers do not exist. Please execute the {ana_config_file_name}.gen to generate the layers before performing analysis.\n")
            return -1
        
        # calling the algos from the dictionary
        currentAlgo = algorithmFunctionsDict[COMMUNITY_TYPE_ALGO.lower()]
        try:
            numNodes, numEdges, numCommunities = currentAlgo(INPUT_layer_path_from_dict, outputDirectory, analysisNAME, userName_from_ana_config_file, gen_configFile_name, ana_config_file_name)
            ana_log_file_object.ana_msg_log_file(log_file, "Done.")
        except Exception as e:
            ana_log_file_object.ana_msg_log_file(log_file, f"An ERROR occurred during {COMMUNITY_TYPE_ALGO} analysis.")
            print(f"An error occurred during {COMMUNITY_TYPE_ALGO} analysis: {str(e)} \n")
    except Exception as e:  # Replace with actual exception type if you have one
        print(f"An error occurred during {COMMUNITY_TYPE_ALGO} analysis: {str(e)} \n")
        ana_log_file_object.ana_msg_log_file(log_file, f"An ERROR occurred during {COMMUNITY_TYPE_ALGO} analysis.")

#Given config file name, write the proper config file information with proper formatting.            
def writeConfigFileContents(file, numNodes, path1, path2) -> None:
    conf = open(file, 'w')
    conf.write("# Number of vertices\n" + str(numNodes) + "# Edge community file names\n" + path1 + "\n" + path2 + "\n") #Creates config file
    conf.close()

def ceANDConfig(operator, operand1, operand2, ana_log_file_object, ana_log_file, file, numNodes):
    path_to_1 = operand1 + ".ecom"
    path_to_2 = operand2 + ".ecom"
    files_exist = checkEcomFilesExist(path_to_1, path_to_2, ana_log_file_object, ana_log_file) 
    if(files_exist == False):
        return False, None, None                             
    writeConfigFileContents(file, numNodes, path_to_1, path_to_2)
    return True, path_to_1, path_to_2

def cvANDConfig(operator, operand1, operand2, ana_log_file_object, ana_log_file, file, numNodes):
    path_to_1 = operand1 + ".vcom"
    path_to_2 = operand2 + ".vcom"
    writeConfigFileContents(file, numNodes, path_to_1, path_to_2)
    return True, path_to_1, path_to_2

def ceORConfig(operator, operand1, operand2, ana_log_file_object, ana_log_file, file, numNodes):
    pass

anaOperatorConfigDict = {
    "CE-AND": ceANDConfig,
    "CV-AND": cvANDConfig,
    "CE-OR" : ceORConfig,
}


def createConfigFile(operator, operand1, operand2, ana_log_file_object, ana_log_file, file, numNodes):
    currentOperator = anaOperatorConfigDict[operator]
    val, path_to_1, path_to_2 = currentOperator(operator, operand1, operand2, ana_log_file_object, ana_log_file, file, numNodes)
    return val, path_to_1, path_to_2
    