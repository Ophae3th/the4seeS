## Design choices

### The dilemma
The primary technical challenge of this exercise is the efficient regex processing of a very large string, read over the network, as exemplified by "Part II" of the project description. I developed the initial design in stream processing terms, to minimize memory demands. For HTTP interaction, I selected the `requests` library due to its convenient interfaces, and its streaming support. I also selected the python `xml.sax` library due to its incremental parsing implementation. While I do not expect NCBI XML sources to be very large in terms of number of nodes, the need to process sequence data as it comes in, before the whole document has been received, makes incremental parsing important. The canonical way to process streams in Python is with "generators." Inspired by some of [Dave Beazley](http://www.dabeaz.com/)'s work on generators and coroutines in Python, I applied these tools in a pipe-filter architecture. The program is thus able to handle a request of the kind in Part II, writing output continuously to stdout and the CSV file...

#### But

Performance (even tractability) on certain inputs is only part of what matters. At least as important in many cases is correctness. And there is a basic problem in trying to apply python regexes to a stream. Python regexes include features such as backtracking, lookahead and lookbehind. If we do not have the entire string available, these patterns will not match the full string correctly, unless the string can be dynamically loaded from storage/network based on some access protocol. As awesome as that sounds to try to implement, I considered that beyond our scope here.

I contemplated trying to check the regex pattern for certain features and perhaps warn the user, but further, I implemented regex application to stream chunks, which introduces possible error at chunk boundaries, where a match might occur but for the artificial chunk boundaries. The chunk size is configurable, but the fact is that regexes are fundamentally broken in a stream context where the stream is not seekable in a way controlled by the regex evaluation.

And so I implemented a mode in which the entire sequence is in fact loaded in memory, and the regex searched against it. I made this mode the default, so that streaming mode must be accessed with a `--stream` option, assuming that correctness is more important than performance by default. I was able to leverage the same output stream handling code, so this added little complexity to the program overall.

### Other considerations

The program is structured as a library exposing a high-level interface to querying NCBI data, and a command-line script to handle input and invoke the library appropriately. I work with a very large legacy codebase in which the notion of "script" is hopelessly entangled with core algorithms, leading to all kinds of badness. Experience has taught me how important it is to distinguish interface code such as command-line handling from a core API, represented by well-designed classes or functions, even in small programs. While the package structure is borderline overengineering here, small programs become large programs, directly or through systems integration.

## Program usage

This package can be installed with `pip` or another method making use of the included setup.py script.

Expected compatibility with any python v2.7 release on any Linux-like system, though other versions may work. Only tested against python v2.7.9 on Mac OSX.

Command line usage information can be displayed using the `--help` option:

    $ python genbank-query.py --help
    usage: genbank-query.py [-h] -d DATABASE -i ID -r REGEXP -o OUTPUT_FILE
                            [-tr TAG_REGEXP] [--stream]
                            [--stream-chunk-size STREAM_CHUNK_SIZE]
    
    optional arguments:
      -h, --help            show this help message and exit
      -d DATABASE, --database DATABASE
                            Name of an NCBI database.
      -i ID, --id ID        ID of a sequence record within the specified database.
      -r REGEXP, --regexp REGEXP
                            A regular expression string with which to search the
                            sequence.
      -o OUTPUT_FILE, --output-file OUTPUT_FILE
                            Name of CSV file to be output.
      -tr TAG_REGEXP, --tag-regexp TAG_REGEXP
      --stream              Process the sequence on the fly rather than retrieving
                            all at once. USE WITH CAUTION - not guaranteed to
                            match every sequence for every regexp.
      --stream-chunk-size STREAM_CHUNK_SIZE
                            The size of the sequence to be matched by the regexp
                            at a time when in streaming mode. For regexes which
                            may match large sequences, set this to a high value.
                            To avoid match problems at chunk boundaries, you may
                            need to run more than once with non-aligned chunk
                            sizes and compute the set difference to locate certain
                            matches.

## Etc

This username and repository name were selected from choices presented by `pwgen`, in case you were wondering.
