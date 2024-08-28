// July 24, 2018: Perform intersection of communities based on vertices.
// 		Works only if the communities in the individual layers are self preserving. Then the communities are guaranteed to be self-preserving

// Mar 15, 2020: Works for a unified layer input format. Outputs
// Line(s) #: Meta information
// Line 1 to |V|: vertexID commID

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

	FILE *f = fopen("CV-AND.conf", "r"), *f1, *f2;
	char info[500], layerName[500], info1[500];

	// number of vertices
	fgets(info, 499, f);
	int numberOfVertices = atoi(fgets(info, 499, f));

	// maps the ids to the comunity numbers
	map<string, int> communityMapper;
	map<string, int> :: iterator it;


	int i;

	timestamp_t t1 = get_timestamp();

	fgets(info, 499, f);

	// layer 1 vertex communities
	fgets(info, 499, f);
	info[strlen(info)-1] = '\0';
	f1 = fopen(info, "r");
	// layer 1 name

//	info[strlen(info) - 18] = '\0';

	fgets(info, 499, f1);
	fgets(info, 499, f1);
	info[strlen(info)-1] = '\0';

	
	sprintf(layerName, "%s_CV-AND_", info);	// rAND layer Name

	
	// layer 2 vertex communities
	fgets(info, 499, f);
	info[strlen(info)-1] = '\0';
	f2 = fopen(info, "r");
	// layer 2 name

//	info[strlen(info) - 18] = '\0';

	fgets(info, 499, f2);
	fgets(info, 499, f2);
	info[strlen(info)-1] = '\0';

	strcat(layerName, info);	// rAND layer Name
	strcpy(info, layerName);
	strcat(info, ".vcom");	// rAND vertex Community file


	fclose(f); // closing config file

	f = fopen(info, "w");
//	sprintf(info, "# Communities for %s with %d number of vertices in each layer\n# node communityID - vertexBased\n", layerName, numberOfVertices);
//	fputs(info, f);

	char *temp1, *temp2;
	int a[2][2];

	int ctr = 1;

//cout<<"\ninitial: ("<<a[0][0]<<", "<<a[0][1]<<"), ("<<a[1][0]<<", "<<a[1][1]<<")";


	int numberOfCommunities = 0;

	for (i =0; i < 5; i++)
	{
		fgets(info, 499, f1);
		fgets(info, 499, f2);
	}

	while( ctr <= numberOfVertices )
	{

		// reading vID,cID for layer 1
		fgets(info, 499, f1);

		temp1 = strtok(info, ",");
		a[0][0] = atoi(temp1);	// vID
		temp1 = strtok(NULL, ",");
		a[0][1] = atoi(temp1);	// cID

		// reading vID,cID  for layer 2	
		fgets(info, 499, f2);

		//cout<<info2;
		temp2 = strtok(info, ",");
		a[1][0] = atoi(temp2);
		temp2 = strtok(NULL, ",");
		a[1][1] = atoi(temp2);

		// storing the mapping of commIDs
		sprintf(info, "%d.%d", a[0][1], a[1][1]);	// new Community ID
		it = communityMapper.find(info);
		if (it == communityMapper.end())	// if the current id is not present in the map, add a new id
		{
			++numberOfCommunities;
			communityMapper.insert(pair<string, int>(info, numberOfCommunities));
			sprintf(info, "%d,%d\n", a[0][0], numberOfCommunities);
		}
		else // if the current id is present in the map, extract already stored id
		{
			sprintf(info, "%d,%d\n", a[0][0], it -> second);
		}

		fputs(info, f);
		++ctr;
	}


	fclose(f);

	fclose(f2);

	fclose(f1);


	timestamp_t t2 = get_timestamp();


	// add meta information in the beginning of the layer file
	sprintf(info1, "sed -i '1s/^/%s\\n%s\\n%s\\n%d\\n%s\\n%d\\n%s\\n/' %s.vcom", "# Vertex Community File for Layer", layerName, "# Number of Vertices", numberOfVertices, "# Number of Total Communities", numberOfCommunities, "# Vertex Community Allocation: vid,commID (in sorted order of vertex IDs)", layerName);
	system(info1);


//	cout<<"\n Number of Communities (Singleton and Non-singleton): "<<numberOfCommunities;

	cout<<"\n Generation Time : "<<(t2 - t1)/1000000.0L<<" seconds";

	
	return 0;
}
