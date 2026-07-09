#ifndef GRAPH_LAYOUT_H
#define GRAPH_LAYOUT_H

typedef struct {
    int   id;
    char  label[32];
    float x;
    float y;
} Node;

void compute_layout(Node *nodes, int count, float radius);
void print_layout(Node *nodes, int count);

#endif
