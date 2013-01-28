// Hungarian algorithm

#include <cstdio>
#include <algorithm>
#include <queue>

namespace hun {
  const int MAX_NODES = 5000;
  typedef int value_type;
  const value_type INF = (int) 2e9;

  value_type w[MAX_NODES][MAX_NODES];
  int matched_m[MAX_NODES];
  int matched_f[MAX_NODES];
  value_type slack_f[MAX_NODES];
  int f2m[MAX_NODES];
  value_type l_m[MAX_NODES];
  value_type l_f[MAX_NODES];
  int vis_m[MAX_NODES];
  int vis_f[MAX_NODES];
  int slacker[MAX_NODES];
  int prev_m[MAX_NODES];
  int prev_f[MAX_NODES];

  value_type hungarian(int n) {
    for (int i = 0; i < n; ++i) {
      l_m[i] = 0;
      l_f[i] = 0;
      
      for (int j = 0; j < n; ++j) {
        l_f[i] = std::max(l_f[i], w[j][i]);
      }

      matched_m[i] = matched_f[i] = 0;
    }

    for (int cur_male = 0; cur_male < n; ++cur_male) {
      if (matched_m[cur_male])
        continue;

      for (int i = 0; i < n; ++i) {
        slack_f[i] = INF;
        vis_f[i] = 0;
        vis_m[i] = 0;
      }

      std::deque<int> Q;

      Q.push_back(cur_male);
      int found_unmatched_female = 0;
      int unmatched_female;
      prev_m[cur_male] = -1;

      while (!found_unmatched_female) {
        if (!Q.empty()) {
          int cur = Q.front();
          Q.pop_front();
          vis_m[cur] = 1;

          /* Update slack */
          for (int i = 0; i < n; ++i) {
            if (!vis_f[i]) {
              value_type slack_cand = l_m[cur] + l_f[i] - w[cur][i];

              if (slack_cand < slack_f[i]) {
                slack_f[i] = slack_cand;
                slacker[i] = cur;
              }

              if (slack_f[i] == 0) {
                vis_f[i] = 1;
                prev_f[i] = cur;
                if (matched_f[i]) {
                  Q.push_back(f2m[i]);
                  prev_m[f2m[i]] = i;
                  vis_m[f2m[i]] = 1;
                } else {
                  /* Unmatched female! */
                  found_unmatched_female = 1;
                  unmatched_female = i;
                  break;
                }
              }
            }
          }
        } else {
          /* We need to change the vertex weights */
          value_type min_slack = INF;

          for (int i = 0; i < n; ++i) {
            if (!vis_f[i])
              min_slack = std::min(min_slack, slack_f[i]);
          }

          for (int i = 0; i < n; ++i) {
            if (vis_f[i])
              l_f[i] += min_slack;
            if (vis_m[i])
              l_m[i] -= min_slack;
          }

          for (int i = 0; i < n; ++i) {
            if (!vis_f[i]) {
              slack_f[i] -= min_slack;

              if (slack_f[i] == 0) {
                vis_f[i] = 1;
                prev_f[i] = slacker[i];
                if (matched_f[i]) {
                  Q.push_back(f2m[i]);
                  prev_m[f2m[i]] = i;
                  vis_m[f2m[i]] = 1;
                } else {
                  /* Unmatched female! */
                  found_unmatched_female = 1;
                  unmatched_female = i;
                  break;
                }
              }
            }
          }
        }
      }

      /* Apply alternating path */
      matched_f[unmatched_female] = 1;
      int cur = unmatched_female;

      while (cur != -1) {
        f2m[cur] = prev_f[cur];
        cur = prev_m[prev_f[cur]];
      }
    }

    value_type res = 0;

    for (int i = 0; i < n; ++i)
      res = std::max(-INF, std::min(INF, res + l_f[i] + l_m[i]));

    return res;
  }
};
