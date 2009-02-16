// mst main
#include <mst.h>
#include <stdio.h> /* FILE, fopen, fprintf */

float get_packing_percent(int num_verts, int num_edges) {
    int min_edges = num_verts - 1;
    int num_edges_scaled = num_edges - min_edges;
    int num_edge_choices = num_verts*(num_verts-1)/2 - min_edges;
    if(num_edge_choices == 0)
        return 1.0f;
    else
        return ((float)num_edges_scaled) / num_edge_choices;
}

int main(int argc, char **argv) {
#ifdef _DEBUG_
    if(argc != 2) {
        fprintf(stderr, "usage: ./mst <inputfile>\n");
        return 0;
    }
#endif

#if ALG == BEST_ALG
    FILE *input = fopen(argv[1], "r");
    unsigned num_verts, num_edges;
    fscanf(input, "%d", &num_verts);
    fscanf(input, "%d", &num_edges);
    fclose(input);

    int density = num_edges / num_verts;
    float packing = get_packing_percent(num_verts, num_edges);
    if(density<100 && packing<=0.75f)
        kruskal(argv[1]);
    else
        prim_dense(argv[1]);
#elif ALG == KRUSKAL
    kruskal(argv[1]);
#elif ALG == PRIM_DENSE
    prim_dense(argv[1]);
#elif ALG == PRIM_BHEAP
#   error PRIM_BHEAP is not yet implemented
#elif ALG == KKT
#   error KKT is not yet implemented
#else
#   error Invalid ALG type
#endif
    return 0;
}
