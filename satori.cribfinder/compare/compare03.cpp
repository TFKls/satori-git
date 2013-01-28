#include <cstdio>
#include <cassert>
#include <vector>
#include <string>
#include <algorithm>
using namespace std;

#include "hun.cpp"

const int MAX_LEN = 200000;

/*Struct for elements*/
struct elem {
  int start, end;
  int blk_start, blk_end;

  vector<elem *> children;
};

void partition_rec(char *input, int start, int end, elem &e) {
  int cur_start = start;
  int cur_opening;
  int depth = 0;
  int rb_depth = 0;

  for (int i = start; i < end; ++i) {
    if (input[i] == '{') {
      ++depth;

      if (depth == 1)
        cur_opening = i;
    } else if (input[i] == '}') {
      --depth;

      if (depth == 0) {
        elem *e2 = new elem;
        e2->start = cur_start;
        e2->end = i + 1;
        e2->blk_start = cur_opening;
        e2->blk_end = i + 1;

        partition_rec(input, cur_opening + 1, i, *e2);
        e.children.push_back(e2);

        cur_start = i + 1;
      }
    } else if (input[i] == '(') {
      ++rb_depth;
    } else if (input[i] == ')') {
      --rb_depth;
    } else if (input[i] == ';' && depth == 0 && rb_depth == 0) {
      cur_start = i + 1;
    }
  }
}

string reconstruct_rec(char *input, elem &e, int min_block, vector<string> &parts) {
  string res;

  int copied_idx = e.start;

  for (int i = 0; i < e.children.size(); ++i) {
    res.append(&input[copied_idx], &input[e.children[i]->start]);

    res += reconstruct_rec(input, *e.children[i], min_block, parts);

    copied_idx = e.children[i]->end;

    delete e.children[i];
  }

  res.append(&input[copied_idx], &input[e.end]);

  if (res.size() >= min_block) {
    parts.push_back(res);
    return "b";
  } else {
    return res;
  }
}

void partition(char *input, int len, vector<string> &parts, int min_block) {
  elem *e = new elem;
  e->start = e->blk_start = 0;
  e->end = e->blk_end = len;

  partition_rec(input, 0, len, *e);
  string res = reconstruct_rec(input, *e, min_block, parts);

  delete e;

  if (res != "b")
    parts.push_back(res);
}

int edit_dist(string &a, string &b) {
  int la = a.size();
  int lb = b.size();

  static int tab[2][MAX_LEN + 1];

  for (int j = 0; j <= b.size(); ++j)
    tab[0][j] = j;

  for (int i = 1; i <= a.size(); ++i) {
    int cur = i % 2;
    int prev = 1 - cur;

    tab[cur][0] = i;

    for (int j = 1; j <= b.size(); ++j) {
      if (a[i - 1] == b[j - 1]) {
        tab[cur][j] = tab[prev][j - 1];
      } else {
        tab[cur][j] = min(min(tab[prev][j - 1], tab[prev][j]), tab[cur][j - 1]) + 1;
      }
    }
  }

  return tab[a.size() % 2][b.size()];
}


int main(int argc, char **argv) {
  //assert(argc >= 3 && argc <= 4);

  FILE *in1 = fopen(argv[1], "r");
  FILE *in2 = fopen(argv[2], "r");
  int min_block = 110;
  char input[MAX_LEN];

  //if (argc >= 4) {
    sscanf(argv[3], "%d", &min_block);
  //}

  int len1 = fread(input, 1, MAX_LEN, in1);
  vector<string> parts1;
  partition(input, len1, parts1, min_block);

  for (int i = 0; i < parts1.size(); ++i) {
//    printf("%s\n", parts1[i].c_str());
  }

  int len2 = fread(input, 1, MAX_LEN, in2);
  vector<string> parts2;
  partition(input, len2, parts2, min_block);

  fclose(in1);
  fclose(in2);

  int n = max(parts1.size(), parts2.size());

  for (int i = 0; i < 2 * n; ++i) {
    for (int j = 0; j < 2 * n; ++j) {
      if (i >= parts1.size()) {
        if (j >= parts2.size()) {
          hun::w[i][j] = 0;
        } else {
          hun::w[i][j] = parts2[j].size();
        }
      } else {
        if (j >= parts2.size()) {
          hun::w[i][j] = parts1[i].size();
        } else {
          hun::w[i][j] = edit_dist(parts1[i], parts2[j]);
        }
      }

      hun::w[i][j] = 2 * MAX_LEN - hun::w[i][j];
    }
  }

#if 0
  for (int j = 0; j < parts2.size(); ++j) {
    printf("%4d ", parts2[j].size());
  }
  printf("\n\n");

  for (int i = 0; i < parts1.size(); ++i) {
    for (int j = 0; j < parts2.size(); ++j) {
      printf("%4d ", edit_dist(parts1[i], parts2[j]));
    }
    printf("\n");
  }
#endif

  //printf("Edit distance: %d Block size: %d\n", 4 * n * MAX_LEN - hun::hungarian(2 * n), min_block);
	printf("%d\n", 4 * n * MAX_LEN - hun::hungarian(2 * n));

  return 0;
}


