#!/usr/bin/awk -f

/^do-conversion/ {

    if (NF == 5) {
	inunit = $2;
	inunitname = $3;
	outunit = $4;
	outunitname = $5;
    } else if (NF == 3) {
	inunit = $2;
	inunitname = $2;
	outunit = $3;
	outunitname = $3;
    } else {
	print "strange do-conversion line: " $0 > "/dev/stderr";
	exit 3;
    }
    sline = sprintf("units '%s' '%s' | head -1 | awk '{print $2}'", inunit, outunit);
    printf "sline=" sline >"/dev/stderr";
    #conversion = system(sline);
    sline | getline conversion;
    print "conversion=" conversion >"/dev/stderr";

    printf("\\vskip 5pt\n");
    printf("\\begin{tabular}{|p{0.4\\columnwidth}p{0.1\\columnwidth}p{0.4\\columnwidth}}\n");
    printf("\\textbf{%s}& &\\textbf{%s}\\\\\n", inunitname, outunitname);
    for (i=1; i<=9; i++) {
	#printf("%8.4f&%d&%8.4f\\\\\n", $4*i, i, i/$4);
	s = sprintf("%g&%d&%g\\\\\n", i/conversion, i, i*conversion);
	s = gensub(/e\+0?([0-9]+)/, "$\\\\times10^{\\1}$", "g", s);
	s = gensub(/e-0?([0-9]+)/, "$\\\\times10^{-\\1}$", "g", s);
	printf("%s", s);
    }
    printf("\\end{tabular}\n\\par\n");

    next;

}

{
    print;
}
