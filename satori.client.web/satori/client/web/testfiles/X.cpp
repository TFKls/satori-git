#include <cstdio>

int main()
{
  char c;
  while ((c=getchar())!=' ' && c!='\n')
    putchar(c);
}