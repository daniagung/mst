#ifndef ADJ_MATRIX_H
#define ADJ_MATRIX_H

#define FLOAT_NEG_1 0xbf800000
#define FLOAT_MAX   0x7f7fffff
#define AM_NO_EDGE  FLOAT_NEG_1

/**
 * Returns the index of an edge in an adjacency matrix between edge u,v
 */
int AM_INDEX(int num_verts, int u, int v);

/* index of edge u, v in an adjacency matrix; u <= v must hold (u,v in range [0,n-1]) */
#define AM_INDEX_FAST_NO_ADJ(num_verts, u, v) ((u) * (num_verts) + (v))

/* index of edge u, v in an adjacency matrix; u <= v must hold (u,v in range [1,n]) */
#define AM_INDEX_FAST(num_verts, u, v) AM_INDEX_FAST_NO_ADJ(num_verts, ((u)-1), ((v)-1))

/* weight of edge u, v in an adjacency matrix; u <= v must hold (u,v in range [0,n-1]) */
#define AM_WEIGHT_FAST_NO_ADJ(G, num_verts, u, v) ((G)[AM_INDEX_FAST_NO_ADJ(num_verts, u, v)])

/* weight of edge u, v in an adjacency matrix; u <= v must hold (u,v in range [1,n]) */
#define AM_WEIGHT_FAST(G, num_verts, u, v) AM_WEIGHT_FAST_NO_ADJ(G, num_verts, ((u)-1), ((v)-1))

#endif /* ADJ_MATRIX_H */