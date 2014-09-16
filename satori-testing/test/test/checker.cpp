/* checkerka, sprawdza absolute error */

#include "ver.h"
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <iomanip>
#include <fstream>

using namespace std;

void error(const char *msg)
{
	cerr << msg;
	exit(1);
}

typedef long double K;
const K eps = 2e-6;

int main(int argc, char **argv)
{
	ifstream input; input.open(argv[1]);
	ifstream hint; hint.open(argv[2]);
	ifstream output; output.open(argv[3]);
	int Z; input >> Z; // = input.readInt();
	bool wrong = false;
	while(Z--)
	{
		K trueResult; hint >> trueResult; //hint.readLDouble(minout, maxout);
		K checkedResult; output >> checkedResult; // = output.readLDouble(minout, maxout);
		//hint.skipWhitespaces();
		//output.skipWhitespaces();
		long double e = fabsl((trueResult - checkedResult));
		cerr << fixed << setprecision(7);
		if(e > eps) {
		    cerr << "ERROR: " << e << " got: " << checkedResult << " expected " << trueResult << endl; 
            wrong = true;
        }
	}

    if (wrong) error("wrong answer\n");
	//if(!output.isEOF())
	//	error("rubbish at the end of output");
	return 0;
}
