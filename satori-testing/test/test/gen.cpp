#include <algorithm>
#include <cassert>
#include <cmath>
#include <complex>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <iostream>
#include <list>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <stack>
#include <string>
#include <vector>
using namespace std;

typedef long long LL;
typedef long double LD;
typedef vector<int> VI;
typedef pair<int,int> PII;

#define REP(i,n) for(int i=0;i<(n);++i)
#define SIZE(c) ((int)((c).size()))
#define FOR(i,a,b) for (int i=(a); i<(b); ++i)
#define FOREACH(i,x) for (__typeof((x).begin()) i=(x).begin(); i!=(x).end(); ++i)
#define FORD(i,a,b) for (int i=((int)(a))-1; i>=(b); --i)

#define pb push_back
#define mp make_pair
#define st first
#define nd second
// GEOMETRIA - podstawowe struktury i operatory

// Bartosz Walczak

typedef long long K;
const K EPS = 1;

struct xy { // punkt w 2D
    K x, y;
    xy(K xi, K yi):x(xi), y(yi) {}
    xy() {}
    K norm() const { return x*x+y*y; } // kwadrat(!) normy euklidesowej
};

inline xy operator+(const xy&a, const xy&b) { return xy(a.x+b.x, a.y+b.y); }
inline xy operator-(const xy&a, const xy&b) { return xy(a.x-b.x, a.y-b.y); }
inline xy operator*(const xy&a, K f) { return xy(a.x*f, a.y*f); }
inline xy operator/(const xy&a, K f) { return xy(a.x/f, a.y/f); }
inline xy cross(const xy&a) { return xy(-a.y, a.x); } // obrot o 90 stopni
inline K operator*(const xy&a, const xy&b) { return a.x*b.x+a.y*b.y; }
inline K det(const xy&a, const xy&b) { return a.x*b.y-b.x*a.y; }

struct xyz { // punkt w 3D
    K x, y, z;
    xyz(K xi, K yi, K zi):x(xi), y(yi), z(zi) {}
    xyz() {}
    K norm() const { return x*x+y*y+z*z; } // kwadrat(!) normy euklidesowej
};

xyz normal;

inline xyz operator+(const xyz&a, const xyz&b)
  { return xyz(a.x+b.x, a.y+b.y, a.z+b.z); }
inline xyz operator-(const xyz&a, const xyz&b)
  { return xyz(a.x-b.x, a.y-b.y, a.z-b.z); }
inline xyz operator*(const xyz&a, K f) { return xyz(a.x*f, a.y*f, a.z*f); }
inline xyz operator/(const xyz&a, K f) { return xyz(a.x/f, a.y/f, a.z/f); }
// Iloczyn wektorowy. Uwaga: odwrotnie argumenty: cross(a,b)=bxa
inline xyz cross(const xyz&a, const xyz&b=normal)
  { return xyz(b.y*a.z-a.y*b.z, b.z*a.x-a.z*b.x, b.x*a.y-a.x*b.y); }
inline K operator*(const xyz&a, const xyz&b)
  { return a.x*b.x+a.y*b.y+a.z*b.z; }
inline K det(const xyz&a, const xyz&b, const xyz&c=normal)
  { return cross(a,b)*c; }

/* GEOMETRIA 2D. Dziala rowniez na dowolnej plaszczyznie w 3D. Wtedy normal
   jest unormowanym (tzn. |normal|=1) wektorem normalnym do plaszczyzny.
   Funkcje oznaczone (*) wymagaja przystosowania do 3D.                       */

// Bartosz Walczak

typedef xy P; // w wersji na plaszczyznie w 3D zmienic na:  typedef xyz P;

// Kat skierowany pomiedzy dwoma wektorami. Zalozenie: a,b!=0
K angle(const P&a, const P&b) { return atan2(det(a,b), a*b); }
// Obrot wektora o kat skierowany
P rot(const P&a, K phi) { return a*cos(phi)+cross(a)*sin(phi); }

/* Wzajemna orientacja 3 wektorow
   >0 - counterclockwise, <0 - clockwise, ==0 - 2 wektory sie pokrywaja       */
int orient(const P&a, const P&b, const P&c) {
    K d1=det(a,b), d2=det(b,c), d3=det(c,a);
    return (d1>=EPS)-(d1<=-EPS)+(d2>=EPS)-(d2<=-EPS)+(d3>=EPS)-(d3<=-EPS);
}



struct line { // prosta {v: n*v=c} (n - wektor normalny)
    P n; K c;
    line(const P&ni, K ci):n(ni), c(ci) {}
    line() {}
};

// Czy punkt lezy na prostej?
bool on_line(const P&a, const line &p) { return fabs(p.n*a-p.c)<EPS; }
// Prosta przechodzaca przez 2 punkty ccw. Zalozenie: a!=b
line span(const P&a, const P&b) { return line(cross(b-a), det(b,a)); }
// Symetralna odcinka. Zalozenie: a!=b
line median(const P&a, const P&b) { return line(b-a, (b-a)*(b+a)*0.5); }
// Przeciecie 2 prostych
P intersection(const line &p, const line &q) {
    K d=det(p.n,q.n);
    if (fabs(d)<EPS) throw "rownolegle";
    return cross(p.n*q.c-q.n*p.c)/d;
}
// Prosta rownolegla przechodzaca przez punkt
line parallel(const P&a, const line &p) { return line(p.n, p.n*a); }
// Prosta prostopadla przechodzaca przez punkt
line perp(const P&a, const line &p) { return line(cross(p.n), det(p.n,a)); }
// Odleglosc punktu od prostej
K dist(const P&a, const line &p) { return fabs(p.n*a-p.c)/sqrt(p.n.norm()); }

// PRZECINANIE ODCINKOW

// Bartosz Walczak

struct segment { P a, b; }; // odcinek domkniety

// Punkt p lezy na prostej zawierajacej s. Czy lezy na odcinku s?
bool on_segment(const P&p, const segment &s) // (*)
  { return min(s.a.x, s.b.x)<p.x+EPS && p.x<max(s.a.x, s.b.x)+EPS &&
           min(s.a.y, s.b.y)<p.y+EPS && p.y<max(s.a.y, s.b.y)+EPS; }
// Czy dwa odcinki maja wspolny punkt?
bool intersect(const segment &s1, const segment &s2) {
    K d1 = det(s2.b-s2.a, s1.a-s2.a), d2 = det(s2.b-s2.a, s1.b-s2.a),
      d3 = det(s1.b-s1.a, s2.a-s1.a), d4 = det(s1.b-s1.a, s2.b-s1.a);
    return (d1>=EPS && d2<=-EPS || d1<=-EPS && d2>=EPS) &&
           (d3>=EPS && d4<=-EPS || d3<=-EPS && d4>=EPS) ||
           fabs(d1)<EPS && on_segment(s1.a, s2) ||
           fabs(d2)<EPS && on_segment(s1.b, s2) ||
           fabs(d3)<EPS && on_segment(s2.a, s1) ||
           fabs(d4)<EPS && on_segment(s2.b, s1);
}

/* PRECYZYJNY PORZADEK KATOWY
      IN: e - wektor rozdzielajacy (wlacznie ccw), a,b - wektory
      OUT: <0 jesli a<b; >0 jesli a>b; 0 jesli a==b
   Uwaga: Dostosowany do obliczen na typach calkowitoliczbowych.
          Przy typach zmiennopozycyjnych lepiej wyliczyc katy explicite       */

// Arkadiusz Pawlik

int anglecmp(const P&e, const P&a, const P&b) {
    int ret=0;
    K v1 = e.x*a.y-e.y*a.x;
    if (v1<0) ret=1;
    else if (v1>0 || e.x*a.x+e.y*a.y>0) ret=-1;
    K v2 = b.x*e.y-b.y*e.x;
    if (v2>0) --ret;
    else if (v2<0 || b.x*e.x+b.y*e.y>0) ++ret;
    return ret + (a.x*b.y-a.y*b.x<0) - (a.x*b.y-a.y*b.x>0);
}


/* NAJMNIEJSZE KOLO zawierajace wszystkie punkty O(n)
   OUT: C - srodek kola, R - kwadrat(!) promienia
   Uwaga! Przed wywolaniem warto zrobic random_shuffle                        */

// Arkadiusz Pawlik

void minidisc2(const P *begin, const P *end, P &C,
               K &R, const P &p1, const P &p2) {
    R = (p1-p2).norm()*0.25; C = (p1+p2)*0.5;
    FOR(i,0,end-begin) if ((C-begin[i]).norm() > R) {
        line U = median(p2, begin[i]);
        line V = median(p1, begin[i]);
        C = intersection(U, V); // Uwaga na wyjatki!
        R = max((C-p1).norm(), max((C-p2).norm(), (C-begin[i]).norm()));
    }
}
void minidisc1(const P *begin, const P *end, P &C, K &R, const P &p1) {
    R = (p1-begin[0]).norm()*0.25; C = (p1+begin[0])*0.5;
    FOR(i,1,end-begin) if ((C-begin[i]).norm() > R)
      minidisc2(begin, begin+i, C, R, p1, begin[i]);
}
void minidisc(const P *begin, const P *end, P &C, K &R) {
    if (end-begin==0) { C=xy(0,0); R=0; }
    else if (end-begin==1) { C=*begin, R=0; }
    else {
        R = (begin[0]-begin[1]).norm()*0.25;
        C = (begin[0]+begin[1])*0.5;
        FOR(i,2,end-begin) if ((C-begin[i]).norm() > R)
          minidisc1(begin, begin+i, C, R, begin[i]);
    }
}


// GEOMETRIA OKREGOW W 2D

// Bartosz Walczak

struct circle { // okrag w 2D
    P c; K r; // srodek, promien
    circle(const P&ci, K ri=0):c(ci), r(ri) {}
    circle() {}
    K length() const { return 2*M_PI*r; } // dlugosc
    K area() const { return M_PI*r*r; } // pole kola
};

// Czy punkt lezy na okregu?
bool on_circle(const P&a, const circle &c)
  { return fabs((a-c.c).norm()-c.r*c.r)<EPS; }
// Czy kolo/punkt lezy wewnatrz lub na brzegu kola?
bool operator<(const circle&a, const circle&b)
  { return b.r+EPS>a.r && (a.c-b.c).norm()<(b.r-a.r)*(b.r-a.r)+EPS; }
// Srodek okragu opisanego na trojkacie
circle circumcircle(P a, P b, P c) {
    if ((a-b).norm() > (c-b).norm()) swap(a, c);
    if ((b-c).norm() > (a-c).norm()) swap(a, b);
    if (fabs(det(b-a, c-b))<EPS) throw "zdegenerowany";
    P v=intersection(median(a, b), median(b, c));
    return circle(v, sqrt((a-v).norm()));
}
// Przeciecie okregu i prostej. Zwraca liczbe punktow
int intersection(const circle &c, const line &p, P I[]/*OUT*/) {
    K d=p.n.norm(), a=(p.n*c.c-p.c)/d;
    P u=c.c-p.n*a; a*=a; K r=c.r*c.r/d;
    if (a>=r+EPS) return 0;
    if (a>r-EPS) { I[0]=u; return 1; }
    K h=sqrt(r-a);
    I[0]=u+cross(p.n)*h; I[1]=u-cross(p.n)*h; return 2;
}
// Przeciecie dwoch okregow. Zwraca liczbe punktow. Zalozenie: c1.c!=c2.c
int intersection(const circle &c1, const circle &c2, P I[]/*OUT*/) {
    K d=(c2.c-c1.c).norm(), r1=c1.r*c1.r/d, r2=c2.r*c2.r/d;
    P u=c1.c*((r2-r1+1)*0.5)+c2.c*((r1-r2+1)*0.5);
    if (r1>r2) swap(r1,r2);
    K a=(r1-r2+1)*0.5; a*=a;
    if (a>=r1+EPS) return 0;
    if (a>r1-EPS) { I[0]=u; return 1; }
    P v=cross(c2.c-c1.c); K h=sqrt(r1-a);
    I[0]=u+v*h; I[1]=u-v*h; return 2;
}

// GEOMETRIA 3D

// Bartosz Walczak

// Kat pomiedzy dwoma wektorami. Zawsze >=0. Zalozenie: a,b!=0
K angle3(const xyz &a, const xyz &b)
  { return atan2(sqrt(cross(b,a).norm()), a*b); }

struct plane { // plaszczyzna {v: n*v=c} (n - wektor normalny)
    xyz n; K c;
    plane(const xyz &ni, K ci):n(ni), c(ci) {}
    plane() {}
};


// Czy punkt lezy na plaszczyznie?
bool on_plane(const xyz &a, const plane &p) { return fabs(p.n*a-p.c)<EPS; }
// Plaszczyzna rozpieta przez 3 punkty ccw. Zalozenie: a,b,c niezalezne
plane span3(const xyz &a, const xyz &b, const xyz &c)
  { xyz n=cross(c-a,b-a); return plane(n, n*a); }
// Plaszczyzna symetralna odcinka. Zalozenie: a!=b
plane median3(const xyz &a, const xyz &b)
  { return plane(b-a, (b-a)*(b+a)*0.5); }
// Plaszczyzna rownolegla przechodzaca przez punkt
plane parallel3(const xyz &a, const plane &p) { return plane(p.n, p.n*a); }
// Odleglosc punktu od plaszczyzny
K dist3(const xyz &a, const plane &p)
  { return fabs(p.n*a-p.c)/sqrt(p.n.norm()); }

struct line3 { // prosta {v: cross(v,u)=w} (u - wektor kierunku)
    xyz u, w;
    line3(const xyz &ui, const xyz &wi):u(ui), w(wi) {}
    line3() {}
};

// Czy punkt lezy na prostej?
bool on_line3(const xyz &a, const line3 &p)
  { return (cross(a,p.u)-p.w).norm()<EPS; }
// Prosta rozpieta przez 2 punkty. Zalozenie: a!=b
line3 span3(const xyz &a, const xyz &b)
  { return line3(b-a, cross(a,b-a)); }
// Plaszczyzna rozpieta przez prosta i punkt ccw. Zalozenie: cross(a,p.u)!=p.w
plane span3(const line3 &p, const xyz &a)
  { return plane(cross(a,p.u)-p.w, p.w*a); }
// Prosta przeciecia dwoch plaszczyzn
line3 intersection3(const plane &p, const plane &q) {
    xyz u=cross(q.n,p.n);
    if (u.norm()<EPS) throw "rownolegle";
    return line3(u, q.n*p.c-p.n*q.c);
}
// Punkt przeciecia plaszczyzny i prostej
xyz intersection3(const plane &p, const line3 &q) {
    K d=q.u*p.n;
    if (fabs(d)<EPS) throw "rownolegle";
    return (q.u*p.c+cross(p.n,q.w))/d;
}
// Prosta prostopadla do plaszczyzny przechodzaca przez punkt
line3 perp3(const xyz &a, const plane &p) { return line3(p.n, cross(a,p.n)); }
// Plaszczyzna prostopadla do prostej przechodzaca przez punkt
plane perp3(const xyz &a, const line3 &p) { return plane(p.u, p.u*a); }
// Odleglosc punktu od prostej
K dist3(const xyz &a, const line3 &p)
  { return sqrt((cross(a,p.u)-p.w).norm())/sqrt(p.u.norm()); }
// Odleglosc 2 prostych od siebie. Zalozenie: cross(q.u,p.u)!=0 (niestabilne
K dist3(const line3 &p, const line3 &q)    // przy bliskim 0)
  { return fabs(p.u*q.w+q.u*p.w)/sqrt(cross(q.u,p.u).norm()); }

// GEOMETRIA SFER W 3D

// Bartosz Walczak

struct sphere {
    xyz c; K r; // srodek, promien
    sphere(const xyz &ci, K ri=0):c(ci), r(ri) {}
    sphere() {}
    K area() const { return 4*M_PI*r*r; } // pole powierzchni
    K volume() const { return 4*M_PI*r*r*r/3; } // objetosc kuli
};









// Czy punkt lezy na sferze?
bool on_sphere(const xyz &a, const sphere &s)
  { return fabs((a-s.c).norm()-s.r*s.r)<EPS; }
// Czy sfera/punkt lezy wewnatrz lub na brzegu kuli?
bool in_sphere(const sphere &a, const sphere &b)
  { return b.r+EPS>a.r && (a.c-b.c).norm()<(b.r-a.r)*(b.r-a.r)+EPS; }
// Przeciecie sfery i prostej. Zwraca liczbe punktow przeciecia
int intersection3(const sphere &s, const line3 &p, xyz I[]/*OUT*/) {
    K d=p.u.norm(), a=(cross(s.c,p.u)-p.w).norm()/(d*d), r=s.r*s.r/d;
    if (a>=r+EPS) return 0;
    xyz u=(p.u*(p.u*s.c)+cross(p.u,p.w))/d;
    if (a>r-EPS) { I[0]=u; return 1; }
    K h=sqrt(r-a);
    I[0]=u+p.u*h; I[1]=u-p.u*h; return 2;
}
/* Przeciecie sfery i plaszczyzny. Zwraca true, jesli sie przecinaja. Wtedy u,r
   sa odp. srodkiem i promieniem okregu przeciecia. Zalozenie: s1.c!=s2.c     */
bool intersection3(const sphere &s, const plane &p, xyz &u, K &r) {
    K d=p.n.norm(), a=(p.n*s.c-p.c)/d;
    u=s.c-p.n*a; a*=a; K r1=s.r*s.r/d;
    if (a>=r1+EPS) return false;
    r=a>r1-EPS ? 0 : sqrt(r1-a)*sqrt(d); return true;
}
/* Przeciecie dwoch sfer. Zwraca true, jesli sie przecinaja. Wtedy u,r sa
   odp. srodkiem i promieniem okregu przeciecia. Zalozenie: s1.c!=s2.c        */
bool intersection3(const sphere &s1, const sphere &s2, xyz &u, K &r) {
    K d=(s2.c-s1.c).norm(), r1=s1.r*s1.r/d, r2=s2.r*s2.r/d;
    u=s1.c*((r2-r1+1)*0.5)+s2.c*((r1-r2+1)*0.5);
    if (r1>r2) swap(r1,r2);
    K a=(r1-r2+1)*0.5; a*=a;
    if (a>=r1+EPS) return false;
    r=a>r1-EPS ? 0 : sqrt(r1-a)*sqrt(d); return true;
}

// GEOMETRIA NA SFERZE

// Bartosz Walczak

// Odleglosc dwoch punktow na sferze
K distS(const xyz &a, const xyz &b)
  { return atan2(sqrt(cross(b,a).norm()), a*b); }

struct circleS { // okrag na sferze
    xyz c; K r; // srodek, promien katowy
    circleS(const xyz &ci, K ri):c(ci), r(ri) {}
    circleS() {}
    K area() const { return 2*M_PI*(1-cos(r)); } // pole kola
};

// Okrag rozpiety przez 3 punkty. Zalozenie: punkty sa parami rozne
circleS spanS(xyz a, xyz b, xyz c) {
    int tmp=1;
    if ((a-b).norm() > (c-b).norm()) { swap(a, c); tmp=-tmp; }
    if ((b-c).norm() > (a-c).norm()) { swap(a, b); tmp=-tmp; }
    xyz v=cross(c-b,b-a); v=v*(tmp/sqrt(v.norm()));
    return circleS(v, distS(a,v));
}
// Przeciecie 2 okregow na sferze. Zalozenie: cross(c2.c,c1.c)!=0
int intersectionS(const circleS &c1, const circleS &c2, xyz I[]/*OUT*/) {
    xyz n=cross(c2.c,c1.c), w=c2.c*cos(c1.r)-c1.c*cos(c2.r);
    K d=n.norm(), a=w.norm()/d;
    if (a>=1+EPS) return 0;
    xyz u=cross(n,w)/d;
    if (a>1-EPS) { I[0]=u; return 1; }
    K h=sqrt(1-a)/sqrt(d);
    I[0]=u+n*h; I[1]=u-n*h; return 2;
}
/* WYPUKLA OTOCZKA 3D w dwoch wersjach: O(n^2) i O(n log(n)) randomizowana
   O(n^2) jest szybsza przy rownomiernie rozlozonych punktach
   Uwaga: Konstruuje wypukla otoczke tylko jezeli punkty nie sa koplanarne    */

// Bartosz Walczak

const int MAXN = 300; // maksymalna liczba punktow

struct tri;

struct edge { // krawedz
    tri *t; int i; // wskaznik na druga sciane, indeks krawedzi na tej scianie
    edge(tri *ti, int ii):t(ti), i(ii) {}
    edge() {}
};

struct tri { // trojkatna sciana
    xyz *v[3], normal; // wierzcholki, normalna skierowana na zewnatrz
    edge e[3];         // krawedzie numerowane przeciwlegle do wierzcholkow
/* Wersja O(n log(n)):
    list<pair<int, list<tri*>::iterator> > L;                                 */
    bool mark;
    tri **self;
    void compute_normal() { normal=cross(*v[1]-*v[0], *v[2]-*v[0]); }
    bool visible(const xyz &p) const { return (p-*v[0])*normal>=EPS; }
};

inline edge *rev(edge *e) { return e->t->e+e->i; }
inline edge *next(edge *e) { return e->t->e+(e->i+1)%3; }

int n;             // IN: liczba punktow
xyz pts[MAXN];     // IN: punkty
int tc;            // OUT: liczba scian
tri *tris[3*MAXN]; // OUT: wskazniki na kolejne sciany
tri buf[3*MAXN];   // bufor zawierajacy sciany (niekoniecznie po kolei!)

tri *get_tri() {
    tris[tc]->mark=false;
    tris[tc]->self = tris+tc;
    return tris[tc++];
}
void put_tri(tri *t) {
    tris[--tc]->self = t->self;
    swap(tris[tc], *t->self);
}

/* Wersja O(n log(n)):
list<tri*> vis[MAXN];
int mark[MAXN];

void add_point(tri *t, int i) {
    if (t->visible(pts[i])) t->L.PB(MP(i, vis[i].insert(vis[i].end(), t)));
}                                                                             */

const int tri_adj[4][3] = { 1, 2, 3, 0, 3, 2, 0, 1, 3, 0, 2, 1 };
const int tri_rev[4][3] = { 0, 0, 0, 0, 2, 1, 1, 2, 1, 2, 2, 1 };

int compute_3dhull() { // zwraca wymiar
    int dim=0;
    FOR(i,1,n) if ((pts[i]-pts[0]).norm()>=EPS)
      { swap(pts[i],pts[1]); ++dim; break; }
    if (dim==0) return 0;
    FOR(i,2,n) if (cross(pts[1]-pts[0], pts[i]-pts[0]).norm()>=EPS)
      { swap(pts[i],pts[2]); ++dim; break; }
    if (dim==1) return 1;
    FOR(i,3,n) if (fabs(det(pts[1]-pts[0], pts[2]-pts[0], pts[i]-pts[0]))>=EPS)
      { swap(pts[i],pts[3]); ++dim; break; }
    if (dim==2) return 2;
    if (det(pts[1]-pts[0], pts[2]-pts[0], pts[3]-pts[0])<0) swap(pts[2],pts[3]);
    FOR(i,0,3*n) tris[i] = buf+i;
    tc=0;
    FOR(i,0,4) {
        tri *t=get_tri();
        FOR(j,0,3) {
            t->v[j]=pts+tri_adj[i][j];
            t->e[j]=edge(buf+tri_adj[i][j], tri_rev[i][j]);
        }
        t->compute_normal();
/* Wersja O(n log(n)):
        FOR(j,4,n) add_point(t, j);                                           */
    }
/* Wersja O(n log(n)):
    fill_n(mark, n, 0);
    int id=1;                                                                 */
    FOR(i,4,n) {
        edge *first, *cur;
// Wersja O(n^2):
        FOR(j,0,tc) tris[j]->mark=tris[j]->visible(pts[i]);
        FOR(j,0,tc) if (tris[j]->mark) FOR(k,0,3) if (!tris[j]->e[k].t->mark)
          { first=cur=tris[j]->e+k; goto label; }
/* Wersja O(n log(n)):
        FORE(j,vis[i]) (*j)->mark=true;
        FORE(j,vis[i]) FOR(k,0,3) if (!(*j)->e[k].t->mark)
          { first=cur=(*j)->e+k; goto label; }                                */
        continue;
label:  int ti=tc;
        do {
            tri *t1=cur->t, *t2=get_tri(); int i1=cur->i;
            t2->v[0]=pts+i; t2->v[1]=t1->v[(i1+2)%3]; t2->v[2]=t1->v[(i1+1)%3];
            t2->compute_normal();
            t2->e[0]=*cur;
            cur=rev(cur);
/* Wersja O(n log(n)):
            FORE(j,t1->L) { add_point(t2, j->FI); mark[j->FI]=id; }
            FORE(j,cur->t->L) if (mark[j->FI]!=id) add_point(t2, j->FI);
            ++id;                                                             */
            do cur=next(cur); while (cur->t->mark);
            t1->e[i1]=edge(t2, 0);
        } while (cur!=first);
        tri *last=tris[tc-1];
        for (; ti<tc; ++ti) {
            last->e[1]=edge(tris[ti], 2);
            tris[ti]->e[2]=edge(last, 1);
            last=tris[ti];
        }
// Wersja O(n^2):
        FOR(j,0,tc) if (tris[j]->mark) put_tri(tris[j--]);
/* Wersja O(n log(n)):
        FORE(j,vis[i]) put_tri(*j);
        FORD(j,ti,tc) {
            FORE(k,tris[j]->L) vis[k->FI].erase(k->SE);
            tris[j]->L.clear();
        }                                                                     */
    }
    return 3;
}

bool operator<(xyz p, xyz q)
{
  return (p.x<q.x) || (p.x==q.x && p.y<q.y) || (p.x==q.x && p.y==q.y && p.z<q.z);
}

bool operator==(xyz p, xyz q)
{
  return p.x==q.x && p.y==q.y && p.z==q.z;
}

int main()
{
  int seed,TT,range,N;
  scanf("%d%d%d%d",&seed,&TT,&N,&range);
  srand(seed);
  printf("%d\n",TT);
  while(TT--)
  {
    vector<xyz> res;
    int k;
    do
    {
    res.clear();
    n = MAXN;
    for(int i=0; i<n; i++)
    {
      pts[i].x = random()%(2*range+1)-range;
      pts[i].y = random()%(2*range+1)-range;
      pts[i].z = random()%(2*range+1)-range;
    }
    sort(pts,pts+n);
    compute_3dhull();
//    printf("%d\n",tc);
    for(int i=0; i<tc; i++)
      for(int q=0; q<3; q++)
        res.push_back(*(tris[i]->v[q]));
    sort(res.begin(),res.end());
    res.erase(unique(res.begin(),res.end()),res.end());
    random_shuffle(pts,pts+n);
    bool found = false;
    k = random()%res.size();
    for(int i=0; i<n; i++)
      if (lower_bound(res.begin(),res.end(),pts[i])==upper_bound(res.begin(),res.end(),pts[i]))
      {
        k = i;
        found = true;
        break;
      }
    } while(res.size()>N);
    random_shuffle(res.begin(),res.end());
    printf("%Ld %Ld %Ld\n",pts[k].x,pts[k].y,pts[k].z);
    printf("%u\n",res.size());
    for(int i = 0; i<res.size(); i++)
      printf("%Ld %Ld %Ld\n",res[i].x,res[i].y,res[i].z);
//    printf("\n");
  }
}
