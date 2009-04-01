#!/usr/bin/awk -f

/^do-convert/ {

    if (NF == 3) {
	inunits = $2;
	inunits_name = "1 " inunits;
	outunits = $3;
	outunits_name = outunits;
    } else if (NF == 5) {
	inunits = $2;
	inunits_name = $3;
	outunits = $4;
	outunits_name = $5;
    } else {
	print "strange do-convert line: " $0 > "/dev/stderr";
	exit 3;
    }

    command = sprintf("units -t '%s' '%s'", inunits, outunits);
    print command > "/dev/stderr";
    command | getline factor;
    if (factor ~ /e\+0/) {
	sub(/e\+0/, "\\times10^{", factor);
	factor = factor "}";
    } else if (factor ~ /e\+/) {
	sub(/e\+/, "\\times10^{", factor);
	factor = factor "}";
    } else if (factor ~ /e-0/) {
	sub(/e-0/, "\\times10^{-", factor);
	factor = factor "}";
    } else if (factor ~ /e-/) {
	sub(/e-/, "\\times10^{-", factor);
	factor = factor "}";
    }
    #printf("\\conversion{1 %s}{%s %s}\n", inunits, unit, outunits);
    #printf("%s & $=$ & $%s$ & %s\\\\\n", inunits_name, factor, outunits_name);
    formatstart = "%s~~\\dotfill~~$%s$";
    formatend   = "%s\\par\n";
    if ($1 == "do-convert-nosp") {
	format = formatstart     formatend;
    } else {
	format = formatstart "~" formatend;
    }
    printf(format, inunits_name, factor, outunits_name);

    next;

}

{
    print;
}
