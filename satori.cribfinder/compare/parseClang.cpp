#include <cstdio>
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <cassert>
#include <cstring>
#include <algorithm>
#include <climits>
#include <vector>
#include <string>
#include <set>
#include <dlfcn.h>
#include "Index.h"
//int i;

CXChildVisitResult visitor(CXCursor node, CXCursor parent, CXClientData children){
    if(clang_equalCursors(node,clang_getNullCursor())){
	return CXChildVisit_Break;
    }
    else {
    	//((CXCursor*)children)[i] = child;
	//++i;
	//printf("%c", char(node.kind % 48 + 65));
	clang_getCursorLocation(node);
	if(node.kind != 100){
	printf("%d %s %s\n", node.kind , clang_getCString(clang_getCursorSpelling(node)), clang_getCString(clang_getCursorDisplayName(node))); }
	if(clang_isPreprocessing(node.kind)) return CXChildVisit_Continue;
	return CXChildVisit_Recurse;
    }
}



void find_typerefs(CXCursor node, int level){

    printf("%d %s %s %d\n", node.kind , clang_getCString(clang_getCursorSpelling(node)), clang_getCString(clang_getCursorDisplayName(node)), level);
    CXCursor children[1000];
    clang_visitChildren(node, visitor, children);
    //for(CXCursor c in node.get_children())
     //   find_typerefs(c, level+1)
}


CXTranslationUnit parse(CXIndex CIdx, const char *source_filename){//, const char * const *command_line_args, int num_command_line_args, struct CXUnsavedFile *unsaved_files, unsigned num_unsaved_files, unsigned options){
        
	const char * const *cla;
	CXUnsavedFile *cxf;
        CXTranslationUnit ptr = clang_parseTranslationUnit(CIdx, source_filename, cla, 0, cxf, 0, 0);

        return ptr;

}

using namespace std;

int main(int argc, char **argv){
	std::ifstream file(argv[1], std::ios::in|std::ios::binary|std::ios::ate);
	std::size_t size = file.tellg();
	file.close();
	CXIndex index = clang_createIndex(1, 0);
	CXTranslationUnit tu = parse(index, argv[1]);//argument sciezka do pliku
	CXFile files = clang_getFile(tu, argv[1]);
   	CXSourceLocation bl = clang_getLocationForOffset(tu, files, 0);
    	CXSourceLocation el = clang_getLocationForOffset(tu, files, size);
    	CXToken * tokens;
    	unsigned num_tokens;
    	clang_tokenize(tu, clang_getRange(bl, el), &tokens, &num_tokens);
	for(int i = 0; i < num_tokens; ++i){
		//printf("%s ", clang_getTokenSpelling(tu,tokens[i]));
		 switch (clang_getTokenKind(tokens[i]))
		 {
		    case CXToken_Punctuation:
				printf("%s", clang_getCString(clang_getTokenSpelling(tu,tokens[i])));
				break;
		    case CXToken_Keyword:{
			std::string ident = clang_getCString(clang_getTokenSpelling(tu,tokens[i]));
			//printf("$ %s $", ident.c_str());
			if (ident == "for" || ident == "do" || ident == "while") {
			    putchar('f'); //Put 'l' if loop;
			  } else if (ident == "return" || ident == "break" || ident == "continue" || ident == "throw") {
			    putchar('c'); //Put 'c' if program flow is changing;
			  } else if (ident == "int" || ident == "long" || ident == "short" || ident == "char" ||
			      ident == "float" || ident == "double" || ident == "signed" || ident == "unsigned") {
			    putchar('t'); //Put 't' if type;
			  } else if (ident == "class" || ident == "struct" || ident == "union") {
			    putchar('o'); //Put 'o' if complex structure;
			  } else if (ident == "if" || ident == "else") {
			    putchar('n'); //Put 'n' if conditional statement;
			  } else if (ident == "unsigned" || ident == "signed" || ident == "const" || ident == "static" || ident == "volatile") {
			    putchar('v');
			  } else {  
			    putchar('z'); //Put 'z' when something else;
			  }
			break;
			}
		    case CXToken_Identifier:
			printf("i");
			break;
		    case CXToken_Literal:{
			std::string ident = clang_getCString(clang_getTokenSpelling(tu,tokens[i]));
			
			//printf("$ %s $", ident.c_str());
			if(ident.at(0) == '\"')   putchar('\"');
			else if (ident[0] == '\'')   putchar('\'');
			else putchar('0');
			break;
			}
		    case CXToken_Comment:
			//printf("");
			break;
		 }
		//printf("\n");
	}
	printf("\n");
	//find_typerefs(clang_getTranslationUnitCursor(tu), 0);
		
}
