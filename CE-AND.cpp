// April 18, 2018: Perform intersection of edges for the two layers.
// 								Followed by connected component analysis

// Feb 6, 2019: Updated reading of vertices from configuration file

// Nov 4, 2019: WOrks for Louvain community inputs

// Mar 17, 2020: Integrated to work for a SINGLE INPUT FORMAT, irrespective of community detection algorithm used

#include <iostream>
#include <fstream>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <math.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <map>

using namespace std;

typedef unsigned long long timestamp_t;

static timestamp_t
get_timestamp ()
{
	struct timeval now;
	gettimeofday (&now, NULL);
	return  now.tv_usec + (timestamp_t)now.tv_sec * 1000000;
}

int main()
{
	FILE *f = fopen("CE-AND.conf", "r"), *f1, *f2;
	char info1[500], info2[500], info[500], layerName[500];

	// number of vertices
	fgets(info1, 499, f);
	int numberOfVertices = atoi(fgets(info1, 499, f));	

	fgets(info1, 499, f);

	// maps the vertices to the AND community IDs
	map<int, int> vertexCommunityID;	
	map<int, int> :: iterator it;

	int i, newID, oldID;
	timestamp_t t1 = get_timestamp();

	// layer 1 edge communities
	fgets(info1, 499, f);
	info1[strlen(info1)-1] = '\0';
	f1 = fopen(info1, "r");
	// layer 1 name

//	info1[strlen(info1) - 16] = '\0';

	fgets(info1, 499, f1);
	fgets(info1, 499, f1);
	info1[strlen(info1)-1] = '\0';


	sprintf(layerName, "%s_CE-AND_", info1);	// ceAND layer Name

	// number of vertices, communities - not used
	for (i = 0; i < 4; i++)
		fgets(info1, 499, f1);

	// number of Community Edges for layer 1
	fgets(info1, 499, f1);
	int edge1 = atoi(fgets(info1, 499, f1));

	// Format Header
	fgets(info1, 499, f1);
	
	// *********

	// layer 2 edge communities
	fgets(info2, 499, f);
	info2[strlen(info2)-1] = '\0';
	f2 = fopen(info2, "r");
	// layer 2 name

//	info2[strlen(info2) - 16] = '\0';

	fgets(info2, 499, f2);
	fgets(info2, 499, f2);
	info2[strlen(info2)-1] = '\0';

	strcat(layerName, info2);	// ceAND layer Name

	// number of vertices, communities - not used
	for (i = 0; i < 4; i++)
		fgets(info2, 499, f2);

	// number of Community Edges for layer 2
	fgets(info2, 499, f2);
	int edge2 = atoi(fgets(info2, 499, f2));

	// Format Header
	fgets(info2, 499, f2);


	fclose(f); // closing config file

	// edge communities for ce-AND
	sprintf(info1, "%s_eCommTemp", layerName);
	f = fopen(info1, "w");

	char *temp1, *temp2;
	int a[2][2];

	// reading v1,v2,cID for layer 1
	fgets(info1, 499, f1);
	temp1 = strtok(info1, ",");
	a[0][0] = atoi(temp1);	// v1
	temp1 = strtok(NULL, ",");
	a[0][1] = atoi(temp1);	// v2

	// reading v1,v2,cID for layer 2	
	fgets(info2, 499, f2);
	temp2 = strtok(info2, ",");
	a[1][0] = atoi(temp2);
	temp2 = strtok(NULL, ",");
	a[1][1] = atoi(temp2);

	int ctr1 = 1, ctr2 = 1;

	int numberOfCommunityEdges = 0;
	int commCtr = 0;

  	while( ctr1 <= edge1 && ctr2 <= edge2 )
	{
		if ( (a[0][0] == a[1][0]) && (a[0][1] == a[1][1]))	// common edge found
		{
			++numberOfCommunityEdges;

			sprintf(info, "%d,%d\n", a[0][0], a[0][1]);
			fputs(info, f);

			// finding the community mapping of the vertices, which will be used to generate the edge community allocations
			if (vertexCommunityID.find(a[0][0]) == vertexCommunityID.end() && vertexCommunityID.find(a[0][1]) == vertexCommunityID.end()) // both not found, start new set
			{
				vertexCommunityID.insert(pair<int, int>(a[0][0], ++commCtr));	// insert v1 and v2 in the map
				vertexCommunityID.insert(pair<int, int>(a[0][1], commCtr));
			}
			else if (vertexCommunityID.find(a[0][0]) != vertexCommunityID.end() && vertexCommunityID.find(a[0][1]) == vertexCommunityID.end()) // only v1 found
			{
				vertexCommunityID.insert(pair<int, int>(a[0][1], vertexCommunityID.find(a[0][0])->second));	// insert v2 in the map with the community mapping of v1
			}
			else if (vertexCommunityID.find(a[0][0]) == vertexCommunityID.end() && vertexCommunityID.find(a[0][1]) != vertexCommunityID.end()) // only v2 found
			{
				vertexCommunityID.insert(pair<int, int>(a[0][0], vertexCommunityID.find(a[0][1])->second));	// insert v1 in the map with the community mapping of v2
			}
			else if ( (vertexCommunityID.find(a[0][0]) != vertexCommunityID.end() && vertexCommunityID.find(a[0][1]) != vertexCommunityID.end()) && (vertexCommunityID.find(a[0][0]) -> second != vertexCommunityID.find(a[0][1]) -> second) ) // both found but different ids => merge two sets
			{
				newID = vertexCommunityID.find(a[0][1])->second; // higher vertex's ID
				oldID = vertexCommunityID.find(a[0][0])->second;

				// traverse through the map and change
				for (it =  vertexCommunityID.begin(); it != vertexCommunityID.end(); ++it)
					if ( it -> second == oldID)
						it -> second = newID;
			}


			if (ctr1 < edge1)
			{
				fgets(info1, 499, f1);
				temp1 = strtok(info1, ",");
				a[0][0] = atoi(temp1);	// v1
				temp1 = strtok(NULL, ",");
				a[0][1] = atoi(temp1);	// v2
				ctr1++;
			}
			else
				ctr1++;

			if ( ctr2 < edge2 )
			{
				fgets(info2, 499, f2);
				temp2 = strtok(info2, ",");
				a[1][0] = atoi(temp2);
				temp2 = strtok(NULL, ",");
				a[1][1] = atoi(temp2);
				ctr2++;
			}
			else
				ctr2++;

		}
		else if ( (a[0][0] < a[1][0]) || (a[0][0] == a[1][0] && a[0][1] < a[1][1]) ) // edge in the layer 1 is not common
		{
			if (ctr1 < edge1)
			{
				fgets(info1, 499, f1);
				temp1 = strtok(info1, ",");
				a[0][0] = atoi(temp1);	// v1
				temp1 = strtok(NULL, ",");
				a[0][1] = atoi(temp1);	// v2
				ctr1++;
			}
			else
				ctr1++;


		}
		else if ( (a[0][0] > a[1][0]) || (a[0][0] == a[1][0] && a[0][1] > a[1][1]) )	// edge in layer 2 is not common
		{
			if ( ctr2 < edge2 )
			{
				fgets(info2, 499, f2);
				temp2 = strtok(info2, ",");
				a[1][0] = atoi(temp2);
				temp2 = strtok(NULL, ",");
				a[1][1] = atoi(temp2);
				ctr2++;
			}
			else
				ctr2++;
		}
		
	}

	fclose(f);

	fclose(f2);

	fclose(f1);

	// final mapping. removing the missing IDs
	map<int, int> finalIDmapping;
	int numberOfRecreatedCommunities = 0;

	// traverse through the map and update
	for (it =  vertexCommunityID.begin(); it != vertexCommunityID.end(); ++it)
		if (finalIDmapping.find(it->second) == finalIDmapping.end())
			finalIDmapping.insert(pair<int, int>(it->second, ++numberOfRecreatedCommunities));

	sprintf(info1, "%s_eCommTemp", layerName);
	f1 = fopen(info1, "r");


	// for finding disconnected components
	sprintf(info1, "%s.ecom", layerName);
	f2 = fopen(info1, "w");
	sprintf(info1, "%s", "# Edge Community Allocation: v1,v2,commID (sorted by vid1, then vid2)");
	fputs(info1, f2);

	fgets(info1, 499, f1);	
	while (!feof(f1))
	{
		info1[strlen(info1) - 1] = '\0';
		
		temp1 = strtok(info1, ",");
		a[0][0] = atoi(temp1); // v1	
		temp1 = strtok(NULL, ",");
		a[0][1] = atoi(temp1); // v2	

		sprintf(info1, "\n%d,%d,%d", a[0][0], a[0][1], finalIDmapping.find((vertexCommunityID.find(a[0][0]) -> second)) -> second);
		fputs(info1, f2);

		fgets(info1, 499, f1);	
	}

	fclose(f1);
	fclose(f2);




	sprintf(info1, "%s.vcom", layerName);
	f2 = fopen(info1, "w");

	int totalComm = numberOfRecreatedCommunities;
	for (i = 1; i <= numberOfVertices; i++)
	{
		if (finalIDmapping.find((vertexCommunityID.find(i) -> second)) -> second != 0)
			sprintf(info1, "%d,%d\n", i, (finalIDmapping.find((vertexCommunityID.find(i) -> second)) -> second));
		else
			sprintf(info1, "%d,%d\n", i, (++totalComm));

		fputs(info1, f2);
	}
	fclose(f2);

	timestamp_t t2 = get_timestamp();

		cout<<"\n Generation Time : "<<(t2 - t1)/1000000.0L<<" seconds";

	// add number of vertices and number of community edges in the beginning of the ecomm layer file
	sprintf(info1, "sed -i '1s/^/%s\\n%s\\n%s\\n%d\\n%s\\n%d\\n%s\\n%d\\n/' %s.ecom", "# Edge Community File for Layer", layerName, "# Number of Vertices", numberOfVertices, "# Number of Non-Singleton Communities", numberOfRecreatedCommunities, "# Number of Community Edges", numberOfCommunityEdges, layerName);
	system(info1);

	// add number of vertices and number of community edges in the beginning of the vcomm layer file
	sprintf(info1, "sed -i '1s/^/%s\\n%s\\n%s\\n%d\\n%s\\n%d\\n%s\\n/' %s.vcom", "# Vertex Community File for Layer", layerName, "# Number of Vertices", numberOfVertices, "# Number of Total Communities", totalComm, "# Vertex Community Allocation: vid,commID (in sorted order of vertex IDs)", layerName);
	system(info1);


	sprintf(info1, "rm %s_eCommTemp", layerName);
	system(info1);
	
return 0;
}
