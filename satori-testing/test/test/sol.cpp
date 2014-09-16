#include <cstdio>
#include <algorithm>
#include <cmath>
#include <vector>
#include <cassert>

#define dprintf(...) fprintf(stderr,__VA_ARGS__)

using namespace std;

typedef long long LL;

const long double eps = 1e-12;

struct point
{
  int x, y, z;
  point(int _x, int _y, int _z) : x(_x), y(_y), z(_z) {};
};

void print(point a)
{
  dprintf("%d %d %d\n",a.x,a.y,a.z);
}

inline int signum(LL x)
{
  if (x==0) return 0;
  if (x>0) return 1;
  return -1;
}

LL det2(int a1, int a2, int b1, int b2)
{
  return a1*(LL)b2 - a2*(LL)b1;
}

point operator-(point a, point b)
{
  return point(a.x - b.x, a.y - b.y, a.z - b.z);
}

LL operator*(point a, point b)
{
  return a.x*(LL)b.x+a.y*(LL)b.y+a.z*(LL)b.z;
}

point operator^(point a, point b)
{
  return point(det2(a.y,a.z,b.y,b.z),-det2(a.x,a.z,b.x,b.z),det2(a.x,a.y,b.x,b.y));
}

LL det(point c, point a, point b)
{
  return c.x*det2(a.y,a.z,b.y,b.z)-c.y*det2(a.x,a.z,b.x,b.z)+c.z*det2(a.x,a.y,b.x,b.y);
}

long double vlen(point a)
{
  return sqrtl(a*a);
}

int main()
{
  int TT;
  scanf("%d",&TT);
  while(TT--)
  {
    int n;
    point f(0,0,0);
    scanf("%d%d%d",&f.x,&f.y,&f.z);
    scanf("%d",&n);
    vector<point> P;
    for(int i=0; i<n; i++)
    {
      int x,y,z;
      scanf("%d%d%d",&x,&y,&z);
      P.push_back(point(x,y,z));
    }
    bool outside = false;
    long double mindist = 1e18;
    for(int i=0; i<n; i++)
      for(int j=i+1; j<n; j++)
        for(int k=j+1; k<n; k++)
        {
          int s = 0;
          bool ok = true;
          for(int q=0; q<n; q++)
          {
            int t = signum(((P[j]-P[i])^(P[k]-P[i]))*(P[q]-P[i]));
            if (s*t==-1)
              ok = false;
            if (t!=0)
              s = t;
          }
          assert(s!=0);
          int t = signum(((P[j]-P[i])^(P[k]-P[i]))*(f-P[i]));
          if (ok && s*t==-1)
            outside = true;
//          dprintf("Good:\n");
//          print(P[i]);
//          print(P[j]);
//          print(P[k]);
          if (ok)
          {
            long double vol = labs(det(P[i]-f,P[j]-f,P[k]-f));
            long double area = vlen((P[j]-P[i])^(P[k]-P[i]));
            if (area>eps)
                mindist = min(mindist,vol/area);
          }
        }
    if (outside)
    {
      printf("Jest na zewnatrz, idioto!\n");
      return 1;
    }
    else
      printf("%.6Lf\n",mindist);
  }
}
