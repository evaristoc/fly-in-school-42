#include <math.h>
#include <stdio.h>
#include "libgraph.h"

/*
 * Simple circular layout for a directed graph.
 * Nodes are placed evenly on a circle of given radius.
 * This function is exported and callable from Python via ctypes.
 * TODO: error handling relevant!!
 */
void compute_layout(Node *nodes, int count, float radius)
{
    for (int i = 0; i < count; i++)
    {
        float angle = (2.0f * M_PI * i) / count;
        nodes[i].x = radius * cosf(angle);
        nodes[i].y = radius * sinf(angle);
    }
}

/* Optional: print layout to stdout for quick debugging */
void print_layout(Node *nodes, int count)
{
    for (int i = 0; i < count; i++)
    {
        printf("Node %d (%s): x=%.3f y=%.3f\n",
               nodes[i].id, nodes[i].label, nodes[i].x, nodes[i].y);
    }
}
