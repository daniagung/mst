#!/usr/bin/env python

from optparse import OptionParser
import sys

def gen_random_edge_lengths(num_verts, num_edges, min_edge_len, max_edge_len, precision):
    print "gen_random_edge_lengths: m=%d n=%d min=%.1f max=%.1f prec=%d" % (num_verts, num_edges, 
                                                                            min_edge_len, max_edge_len, precision)
    # min_edge_len is EXCLUSIVE (e.g., it may be 0.0)

def gen_random_vertex_positions(num_verts, num_edges, num_dims, min_pos, max_pos, precision):
    print "gen_random_vertex_positions: m=%d n=%d d=%d min=%.1f max=%.1f prec=%d" % (num_verts, num_edges, 
                                                                                     num_dims, min_pos, max_pos, precision)

def main():
    usage = "usage: %prog [options] NUM_VERTICES\nGenerates a connected graph with no self-loops or parallel edges."
    parser = OptionParser(usage)
    parser.add_option("-n", "--num-edges",
                      help="number of edges to put in the graph [default: complete graph]")
    parser.add_option("-p", "--precision",
                      type="int", default=1,
                      help="number of decimal points to specify for edge weights [default: %default]")
    parser.add_option("-e", "--edge-weight-range",
                      metavar="MIN,MAX", 
                      help="range of edge weights (min exclusive, max inclusive) [default: [0.1,100000]]")
    parser.add_option("-v", "--vertex-pos-range",
                      metavar="DIM,MIN,MAX",
                      help="dimensionality of vertex positions and the range of each dimension (min inclusive, max inclusive) [not used by default; mutually exclusive with -e]")
    parser.add_option("-s", "--style",
                      help="how to place edges [default: random with no self-loops or parallel edges]")

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error("missing NUM_VERTICES")
    elif len(args) > 1:
        parser.error("too many arguments")

    try:
        num_verts = int(args[0])
    except ValueError:
        parser.error("NUM_VERTICES must be an integer")

    try:
        sne = options.num_edges
        if sne == 'c' or sne == 'complete' or sne is None:
            num_edges = num_verts * num_verts
        else:
            num_edges = int(sne)
            if num_edges > num_verts * num_verts:
                parser.error("-n may not be larger than NUM_VERTICES squared")
    except ValueError:
        parser.error("-n must either be an integer or 'complete'")

    if options.precision <= 0:
        parser.error("-p must be at least 1")
    elif options.precision > 15:
        parser.error("-p must be no more than 15 (doubles cannot accurately represent more than this)")

    if options.style is not None:
        parser.error("option -s is not yet supported")

    if options.edge_weight_range and options.vertex_pos_range:
        parser.error("option -e and -v are mutually exclusive")

    # see if the user wants edge weights computed from vertex positions
    if options.vertex_pos_range:
        (d, m1, m2) = options.vertex_pos_range.split(',', 3)
        try:
            (num_dims, min_pos, max_pos) = (int(d), float(m1), float(m2))
        except ValueError:
            parser.error("option -v requires its arguments to be in the form int,float,float")

        if num_dims < 0:
            parser.error("option -v requires dimensionality to be a strictly positive integer")

        gen_random_vertex_positions(num_verts, num_edges, num_dims, min_pos, max_pos, options.precision)
        return

    # default: randomly choose edge weights in some range
    if options.edge_weight_range:
        (m1, m2) = options.edge_weight_range.split(',', 2)
        try:
            (min_pos, max_pos) = (float(m1), float(m2))
        except ValueError:
            parser.error("option -e requires its arguments to be in the form float,float")

        if min_pos < 0.0:
            parser.error("option -e requires minimum edge length (exclusive) to be >= 0.0")
        if min_pos > max_pos:
            parser.error("option -e requires the minimum edge length < maximum edge length")
    else:
        # use defaults which describes the maximum range for the assignment
        min_pos = 0.1
        max_pos = 100000

    gen_random_edge_lengths(num_verts, num_edges, min_pos, max_pos, options.precision)

if __name__ == "__main__":
    sys.exit(main())
