import re

class ana_dict_class:
    # constructor
    def __init__(self,
                 ANALYSIS_NAME: str = None,
                 ANALYSIS_TYPE: str = None,
                 ANALYSIS_NODES_NUM: str = None,
                 ANALYSIS_EDGES_NUM: str = None,
                 ANALYSIS_COMMUNITIES_NUM: str = None,
                 ):
        self.__ANALYSIS_NAME = ANALYSIS_NAME
        self.__ANALYSIS_TYPE = ANALYSIS_TYPE
        self.__ANALYSIS_NODES_NUM = ANALYSIS_NODES_NUM
        self.__ANALYSIS_EDGES_NUM = ANALYSIS_EDGES_NUM
        self.__ANALYSIS_COMMUNITIES_NUM = ANALYSIS_COMMUNITIES_NUM
        
    # getters
    def get_analysis_name(self):
        return self.__ANALYSIS_NAME
    
    def get_analysis_type(self):
        return self.__ANALYSIS_TYPE
    
    def get_analysis_nodes_num(self):
        return self.__ANALYSIS_NODES_NUM
    
    def get_analysis_edges_num(self):
        return self.__ANALYSIS_EDGES_NUM
    
    def get_analysis_communities_num(self):
        return self.__ANALYSIS_COMMUNITIES_NUM
    
    # setters
    def set_analysis_name(self, ANALYSIS_NAME: str):
        self.__ANALYSIS_NAME = ANALYSIS_NAME
        
    def set_analysis_type(self, ANALYSIS_TYPE: str):    
        self.__ANALYSIS_TYPE = ANALYSIS_TYPE    
        
    def set_analysis_nodes_num(self, ANALYSIS_NODES_NUM: str):
        self.__ANALYSIS_NODES_NUM = ANALYSIS_NODES_NUM
        
    def set_analysis_edges_num(self, ANALYSIS_EDGES_NUM: str):  
        self.__ANALYSIS_EDGES_NUM = ANALYSIS_EDGES_NUM
        
    def set_analysis_communities_num(self, ANALYSIS_COMMUNITIES_NUM: str):
        self.__ANALYSIS_COMMUNITIES_NUM = ANALYSIS_COMMUNITIES_NUM
        