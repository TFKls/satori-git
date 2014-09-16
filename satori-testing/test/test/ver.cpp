#include "ver.h"
#include <stdio.h>

struct Point {
  long long x, y, z;
};

Point Diff(const Point &a, const Point &b) {
  return Point({a.x - b.x, a.y - b.y, a.z - b.z});
}

long long Det(const Point &a, const Point &b, const Point &c) {
  long long result = 0;
  result += a.x * b.y * c.z;
  result -= a.z * b.y * c.x;
  result += a.z * b.x * c.y;
  result -= a.x * b.z * c.y;
  result += a.y * b.z * c.x;
  result -= a.y * b.x * c.z;
  return result;
}

Point m, p[50];
bool marked[50];

int main() {
  oi::Scanner in(stdin);
  int Z = in.readInt(1, 1e9);
  in.readEoln();
  while (Z--) {
    m.x = in.readInt(-1e4, 1e4);
    in.readSpace();
    m.y = in.readInt(-1e4, 1e4);
    in.readSpace();
    m.z = in.readInt(-1e4, 1e4);
    in.readEoln();
    int n = in.readInt(4, 50);
    in.readEoln();
    for (int i = 0; i < n; ++i) {
      p[i].x = in.readInt(-1e4, 1e4);
      in.readSpace();
      p[i].y = in.readInt(-1e4, 1e4);
      in.readSpace();
      p[i].z = in.readInt(-1e4, 1e4);
      in.readEoln();
    }
    for (int i = 0; i < n; ++i)
      marked[i] = false;
    for (int i = 0; i < n; ++i)
      for (int j = i + 1; j < n; ++j)
        for (int k = j + 1; k < n; ++k) {
          bool neg = false, pos = false;
          for (int l = 0; l < n; ++l) {
            long long temp = Det(Diff(p[i], p[l]), Diff(p[j], p[l]), Diff(p[k], p[l]));
            neg |= (temp < 0);
            pos |= (temp > 0);
          }
          if (!neg && !pos)
            in.error("wszystkie punkty w jednej plaszczyznie");
          if (neg && pos)
            continue;
          marked[i] = marked[j] = marked[k] = true;
          long long mucha = Det(Diff(p[i], m), Diff(p[j], m), Diff(p[k], m));
          if ((mucha < 0 && pos) || (mucha > 0 && neg))
            in.error("mucha jest na zewnatrz");
        }
    for (int i = 0; i < n; ++i)
      if (!marked[i])
        in.error("to nie jest wielokat wypukly");
  }
  in.readEof();
  printf("OK\n");
  return 0;
}
