import operator
import os
import networkx as nx
import igraph as ig
from copy import deepcopy
import shutil
from typing import Tuple
import time
from igraph import *

# *************************** CREATES NX GRAPH ****************************************************
def create_nx_Graph(Graphfile):
    # create the networkx graph function from networkx package as this is the input for louvain
    G = nx.Graph()
    edges = []

    with open(Graphfile) as file:
        for line in file:
            # Skip comments
            if not line.startswith('#'):
                value = line.split(",")
                # read lines that are for edges (Node1, Node2, Edge Weight)
                if len(value) >= 2:
                    edges.append((int(value[0]) - 1, int(value[1]) - 1))
                    try:
                        G.add_edge(value[0], value[1],
                                   weight=float(value[2].strip()))
                    except:
                        G.add_edge(value[0], value[1], weight=float(1.0))

    # G is the graph object in networkx package format. edges is a list of all the edges in the graph which we need when writing results for edges in communities
    return G, edges

# *************************** CREATES IG GRAPH ****************************************************
def create_ig_Graph(GraphFile):
    g = ig.Graph()

    # list containing all the edge weights in order since igraph add edge method doesnt take edgeweight
    edgeWeights = []
    edges = []

    with open(GraphFile) as file:
        # skip first line since it is usually graph name (DirectorGenre, ActorGenre, etc)
        next(file)
        # add as last vertex in graph since igraph reads nodes from 0
        g.add_vertices(int(file.readline()))

        for line in file:
            value = line.split(",")
            if len(value) >= 2:
                edges.append((int(value[0]) - 1, int(value[1]) - 1))
                # append edge weight to list
                try:
                    edgeWeights.append(float(value[2]))
                except:
                    edgeWeights.append(float(1.0))

    g.add_edges(edges)

    # g is the graph object in igraph package format. edges is a list of all the edges in the graph which we need when writing results for edges in communities
    # edgeWeights is a seperate list of edgeWeights with the same length as number of vertices of the graph that the community detection algorithm takes.
    return g, edges, edgeWeights

# *************************** LOUVAIN *************************************************************
def writeResultsLouvain(result, path, edges, analysisNAME, numNodes, userName, gen_configFile_name, ana_config_file_name):
    # Function to write results with Louvain result format
    
   
    
    vcom_file_path = os.path.join(path, userName + "_" + ana_config_file_name + "_" + analysisNAME + ".vcom")
    ecom_file_path = os.path.join(path, userName + "_" + ana_config_file_name + "_" + analysisNAME + ".ecom")
    
    numCommunities = max(result.values(), default=0) + 1
    
    # Check if the .vcom file exists
    with open(vcom_file_path, 'w') as f:
        headers = [
            "# Vertex Community File for Layer\n", f"{analysisNAME}\n",
            "# Number of Vertices\n", f"{numNodes}\n",
            "# Number of Total Communities\n", f"{numCommunities}\n",
            "# Vertex Community Allocation: vid,commID (in sorted order of vertex IDs)\n"
        ]
        f.writelines(headers)

        #Kevin - 6/15/24: Write vertices into vcom file even if they weren't assigned a community. They will be assigned new singleton communities.
        numSingletonCommunities = 0
        for node_id in range(1, int(numNodes) + 1):
            community_id = result.get(str(node_id), None)
            if community_id is not None:
                f.write('%s,%s\n' % (node_id, community_id + 1))
            else:
                numSingletonCommunities += 1
                f.write('%s,%s\n' % (node_id, str(numCommunities+numSingletonCommunities)))  
        
    with open(vcom_file_path, 'r') as f:
        lines = f.readlines()

    # Calculate the correct number of total communities
    totalCommunities = numCommunities + numSingletonCommunities

    # Update the line with the correct number of total communities
    lines[5] = f"{totalCommunities}\n"

    # Write the updated lines back to the file
    with open(vcom_file_path, 'w') as f:
        f.writelines(lines)

    # Check if the .ecom file exists
    # if not os.path.exists(ecom_file_path):
    # Write the .ecom file
    with open(ecom_file_path, 'w') as f2:
        
        # Filtering and creating of intra-community edges, where both vertices belong to the same comminity
        filtering_intra_community_edges = [(edge[0], edge[1], result[edge[0]]) for edge in edges if result[edge[0]] == result[edge[1]]]
        # Sort the edges first by v1id, then by v2id, and finally by community id (cid)
        sorted_edges = sorted(filtering_intra_community_edges, key=lambda edge: (int(edge[0]), int(edge[1]), int(edge[2])))

        headers = [
            "# Edge Community File for Layer\n", f"{analysisNAME}\n",
            "# Number of Vertices\n", f"{numNodes}\n",
            "# Number of Non-Singleton Communities\n", f"{numCommunities}\n",
            "# Number of Edges in Communities\n", f"{len(sorted_edges)}\n",
            "# Edge Community Allocation: v1,v2,commID (sorted by vid1, then vid2)\n"
        ]
        f2.writelines(headers)

        for edge in sorted_edges:
            if result[edge[0]] == result[edge[1]]:
                f2.write('%s,%s,%s\n' % (edge[0], edge[1], result[edge[0]] + 1))
        
# *************************** INFOMAP *************************************************************
def writeResultsInfomap(infomap, path, edges, analysisNAME, userName, gen_configFile_name, ana_config_file_name, numOfNodes):
    # Function to write results with infomap result format
    # result is in im.modules which we can iterate through like this
    # for node_id, module_id in infomap.modules: (here module_id is the same as community_id)
    # if not os.path.exists(path):
    #     os.makedirs(path)
    # infomap.write_clu(os.path.join(path+"/"+analysisNAME+".clu"))

    # WRITING ECOM FILE FOR INFOMAP ***************************************************************
    
    # prefix = f"{userName}_{ana_config_file_name + '_' if ana_config_file_name else ''}{analysisNAME}"
    # vcom_file_path = os.path.join(path, f"{prefix}.vcom")
    # ecom_file_path = os.path.join(path, f"{prefix}.ecom")
    vcom_file_path = os.path.join(path, userName+"_"+ana_config_file_name+"_"+analysisNAME + ".vcom")
    ecom_file_path = os.path.join(path, userName+"_"+ana_config_file_name+"_"+analysisNAME + ".ecom")
    
    currentCommunity = 0
    communityList = []

    # Preprocess community and node information
    node_to_community = {}
    communities = {}
    for node_id, module_id in infomap.modules:
        node_to_community[node_id] = module_id
        if module_id not in communities:
            communities[module_id] = []
        communities[module_id].append(node_id)

    numNodes = max(node_to_community.keys(), default=0)
    numCommunities = len(communities)
    
    # Check if the .vcom file exists
    # if not os.path.exists(vcom_file_path):
    # Write the .vcom file
    with open(vcom_file_path, 'w') as f:
        numCommunities = 0
        numNodes = 0
        for node_id, module_id in infomap.modules:
            if module_id > numCommunities:
                numCommunities = module_id
            if node_id > numNodes:
                numNodes = node_id
        headers = [
            "# Vertex Community File for Layer\n", f"{analysisNAME}\n",
            "# Number of Vertices\n", f"{numOfNodes}\n",
            "# Number of Total Communities\n", f"{numCommunities}\n",
            "# Vertex Community Allocation: vid,commID (in sorted order of vertex IDs)\n"
        ]
        f.writelines(headers)

        # for node_id, module_id in infomap.modules:
        #     if module_id != currentCommunity:
        #         communityList.append([])
        #         currentCommunity = module_id
        #     if len(communityList) > module_id - 1:
        #         communityList[module_id - 1].append(node_id)
        #     f.write('%s,%s\n' % (node_id, module_id))
        
        #Kevin - 6/15/24: Write vertices into vcom file even if they weren't assigned a community. They will be assigned new singleton communities.
        numSingletonCommunities = 0
        for node_id in range(1, int(numOfNodes) + 1):
            if node_id in node_to_community:
                module_id = node_to_community[node_id]
            else:
                numSingletonCommunities += 1
                module_id = numSingletonCommunities + numCommunities
            f.write('%s,%s\n' % (node_id, module_id))
            
            
    with open(vcom_file_path, 'r') as f:
        lines = f.readlines()

    # Calculate the correct number of total communities
    totalCommunities = numCommunities + numSingletonCommunities

    # Update the line with the correct number of total communities
    lines[5] = f"{totalCommunities}\n"
    
    # Write the updated lines back to the file
    with open(vcom_file_path, 'w') as f:
        f.writelines(lines)

    # WRITING ECOM FILE FOR INFOMAP ***************************************************************
    # Check if the .ecom file exists
    # if not os.path.exists(ecom_file_path):
    # Write the .ecom file
    communityBridgeEdges = deepcopy(edges)
    count = 0
    # t1 = time.time() - t0
    # t2 = time.time()
    # Extract community information
    communities = []
    for node_id, module_id in infomap.modules:
        while module_id >= len(communities):
            communities.append([])
        communities[module_id].append(node_id)

    # Count non-singleton communities
    numSingletonCommunities = 0
    for community in communities:
        if len(community) > 1:
            numSingletonCommunities += 1

    # Count edges in communities
    numCommunityEdges = 0
    
    for index, community in enumerate(communities):
        community_edges = set()
        for edge in edges:
            if edge[0] in community and edge[1] in community:
                community_edges.add((edge[0], edge[1]))
        numCommunityEdges += len(community_edges)
        
    # Sort edges by v1, then v2
    sorted_edges = sorted(edges, key=lambda x: (x[0], x[1]))

    # Write edges and the community they are in
    with open(ecom_file_path, 'w') as f2:
        numNodes = len(infomap.modules)
        numCommunities = len(communities)

        f2.write("# Edge Community File for Layer\n")
        f2.write(analysisNAME + "\n")
        f2.write("# Number of Vertices\n")
        f2.write(numOfNodes + "\n")
        f2.write("# Number of Non-Singleton Communities\n")
        f2.write(str(numSingletonCommunities + 1) + "\n")
        f2.write("# Number of Edges in Communities\n")
        f2.write(str(numCommunityEdges) + "\n")
        f2.write("# Edge Community Allocation: v1,v2,commID (sorted by vid1, then vid2)\n")

        for i, edge in enumerate(sorted_edges):
            for index, community in enumerate(communities):
                if edge[0] in community and edge[1] in community:
                    f2.write('%s,%s,%s\n' % (edge[0], edge[1], index))
                    communityBridgeEdges.pop(i - count)
                    count += 1

        # Write singleton communities
        for i, node in enumerate(range(1, numNodes + 1)):
            node_in_communities = False
            for community in communities:
                if node in community:
                    node_in_communities = True
                    break
            if not node_in_communities:
                f2.write('%s,%s,%s\n' % (node, node, numCommunities + i + 1))

        # Write the non-singleton node as a separate community
        f2.write('%s,%s,%s\n' % (numNodes, numNodes, numSingletonCommunities + 1))


# *************************** FASTGREEDY | WALKTRAP | LEADIGNEIGENVECTOR | MULTILEVEL **************************
def writeResults(result, path, edges, analysisNAME, algo, t, numNodes, userName, gen_configFile_name, ana_config_file_name):
    
    if ana_config_file_name != "":
        ana_config_file_name = ana_config_file_name

    vcom_file_path = os.path.join(path, userName+"_"+ana_config_file_name+"_"+analysisNAME + ".vcom")
    ecom_file_path = os.path.join(path, userName+"_"+ana_config_file_name+"_"+analysisNAME + ".ecom")

    numCommunities = len(result)

    # Check if the .vcom file exists
    # if not os.path.exists(vcom_file_path):
    # Write the .vcom file
    with open(os.path.join(path+"/"+userName+"_"+ana_config_file_name+"_"+analysisNAME+".vcom"), 'w') as f:
        f.write("# Vertex Community File for Layer\n")
        f.write(analysisNAME + "\n")
        f.write("# Number of Vertices\n")
        f.write(str(numNodes) + "\n")
        f.write("# Number of Total Communities\n")
        f.write(str(numCommunities) + "\n")
        f.write("# Vertex Community Allocation: vid,commID (in sorted order of vertex IDs)\n")
        # f.write("#Time taken "+t+"s\n")
        
        communityMapping = {}
        for index, community in enumerate(result):
            for node in community:
                communityMapping[node+1] = index +1
                #f.write('%s,%s\n' % (node+1, index+1))
        for node_id in range(1,numNodes+1):
            f.write('%s,%s\n' % (node_id, communityMapping[node_id]))
    
    # Check if the .ecom file exists
    # if not os.path.exists(ecom_file_path):
    # Write the .ecom file
    communityBridgeEdges = deepcopy(edges)
    count = 0
    # t1 = time.time() - t0
    # t2 = time.time()

    # calculate the # of edges in communities
    numCommunityEdges = 0
    for i, edge in enumerate(edges):
        for index, community in enumerate(result):
            if edge[0] in community and edge[1] in community:
                numCommunityEdges += 1

    with open(os.path.join(path+"/"+userName+"_"+ana_config_file_name+"_"+analysisNAME+".ecom"), 'w') as f:
        f.write("# Edge Community File for Layer\n")
        f.write(analysisNAME + "\n")
        f.write("# Number of Vertices\n")
        f.write(str(numNodes) + "\n")
        f.write("# Number of Non-Singleton Communities\n")
        f.write(str(numCommunities) + "\n")
        f.write("# Number of Edges in Communities\n")
        f.write(str(numCommunityEdges) + "\n")
        f.write("# Edge Community Allocation: v1,v2,commID (sorted by vid1, then vid2)\n")
        # f.write("#Time taken " + t + "s\n")
        for i, edge in enumerate(edges):
            for index, community in enumerate(result):
                if edge[0] in community and edge[1] in community:
                    f.write('%s,%s,%s\n' % (edge[0]+1, edge[1]+1, index + 1))
                    communityBridgeEdges.pop(i - count)
                    count += 1

def createVertexClusteringObjectLouvain(partition, graphLocation):

    # create a VertexClusteringObject for louvain dictionary since comparision format is a VCO
    igG, _, _ = create_ig_Graph(graphLocation)
    igG.add_vertex(0)

    membership = [None] * (igG.vcount())

    for node_id, community_id in partition.items():
        index = int(node_id)
        membership[index] = int(community_id)

    m = max(partition.values()) + 1

    # membership is a list which contains all community_IDs of the graph
    # example [0,0,0,1,1,1]
    # here nodes 0,1,2 are in community 0 and nodes 3,4,5 are in community 1 (vertices count of graph should match membership length)
    for val in range(len(membership)):
        if membership[val] is None:
            membership[val] = m
            m += 1

    # inbuilt igraph function to create a vertex_clustering_object with ig.graph and membership list as parameters
    return ig.VertexClustering(igG, membership=membership)

def createVertexClusteringObjectInfomap(im, graphLocation):

    # create a VertexClusteringObject for infomap object since comparision format is a VCO
    igG, _, _ = create_ig_Graph(graphLocation)
    igG.add_vertex(0)

    membership = [None] * (igG.vcount())
    m = 0

    for node_id, module_id in im.modules:
        if module_id - 1 > m:
            m = module_id - 1
        index = int(node_id)
        membership[index] = int(module_id - 1)

    # membership is a list which contains all community_IDs of the graph
    # example [0,0,0,1,1,1]
    # here nodes 0,1,2 are in community 0 and nodes 3,4,5 are in community 1 (vertices count of graph should match membership length)
    for val in range(len(membership)):
        if membership[val] is None:
            membership[val] = m
            m += 1

    # inbuilt igraph function to create a vertex_clustering_object with ig.graph and membership list as parameters
    return ig.VertexClustering(igG, membership=membership)

############################ ana_rpn.py ########################################

# #Used in binary operator evaluation. Given path to ecom file and vcom file, move them to the proper path they belong in. Operator is needed since CV-AND will not produce a .ecom file
# def moveEcomVcomFilesToDirectory(ecom_output, vcom_output, directory, operator):
#     if operator != 'CV-AND': # CV-AND will not produce a .ecom file
#         shutil.move(ecom_output, os.path.join(directory, ecom_output)) #Move ecom & vcom from pwd to given directory
#         ecom_output = os.path.join(directory, ecom_output)
        
#     shutil.move(vcom_output, os.path.join(directory, vcom_output))
#     vcom_output = os.path.join(directory, vcom_output)
#     return ecom_output, vcom_output

# #Given path of file to read (either ecom or vcom), return the numNodes, numCommunities, and numEdges.
# def readResultsFromFile(file_to_read) -> Tuple[str, str, str]:
#     read = open(file_to_read, 'r')
#     for i, line in enumerate(read):
#         if i == 3:
#                 numNodes = str(line)
#         elif i == 5: 
#             numCommunities = str(line)
#         elif i == 7: 
#             if file_to_read.endswith(".ecom"):
#                 numEdges = str(line)
#             else:
#                 numEdges = "0\n"
#         elif i > 7:
#             break
#     read.close()
#     return numNodes, numEdges, numCommunities

# #Given an ecom/vcom file, return the analysisname.
# def getAnalysisName(filepath) -> str:
#     with open(filepath) as file_path:
#         for i, line in enumerate(file_path):
#             if i == 1: #This line contains the analysis name
#                 analysisname = line.strip()
#                 return analysisname
            


# #Used after calling c++ code. renames the file that is output by the c++ code and updates the variable holding that file's name.
# def setFilePath(filepath, USERNAME) -> str:
#     os.rename(filepath, USERNAME + "_" + filepath)  #updates name of file to include username 
#     filepath = USERNAME + "_" + filepath #updates variable to new path 
#     return filepath

# #Used before calling c++ code. Checks if ecom files exist for both operands.
# def checkEcomFilesExist(path_to_1, path_to_2, ana_log_file_object, ana_log_file) -> bool:
#     ecom_1_exists = os.path.exists(path_to_1)
#     ecom_2_exists = os.path.exists(path_to_2)

#     if(ecom_1_exists == False or ecom_2_exists == False):
#         ana_log_file_object.ana_msg_log_file(ana_log_file, "Analysis failed. Necessary ecom files do not exist. Tried calling CE-AND after CV-AND?\n")
#         print("Analysis failed. Necessary ecom files do not exist. Tried calling CE-AND after CV-AND?\n")
#         return False
#     else:
#         return True
    
# #If analysis fails, we don't want to store any of the ecom,vcom files corresponding to that analysis. This deletes them.    
# def delete_files(ana_hash_table):
#     for value in ana_hash_table.values():
#         ecom_file = value.get("path_to_ecom_file")
#         vcom_file = value.get("path_to_vcom_file")
#         if ecom_file and os.path.exists(ecom_file):
#             os.remove(ecom_file)
#         if vcom_file and os.path.exists(vcom_file):
#             os.remove(vcom_file)
            
# def moveFilesToOutputDirectory(filesToOutput, OUTPUT_DIRECTORY):
#     for file in filesToOutput:
#         shutil.copy(file, OUTPUT_DIRECTORY)
        
# def getNumNodesFromNetFile(netFile):
#     with open(netFile) as file:
#         for i, line in enumerate(file):
#             if i == 1: #This line contains the number of nodes in the layer.
#                 numNodes = line
#                 #numNodes = int(numNodes)
#                 return numNodes
        