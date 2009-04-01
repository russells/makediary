#!/usr/bin/python

# Transform sed1line.txt into the guts of sed-ref.tex.

import sys
import re

headline_re      = re.compile(r"""^([A-Z].*):$""")
explanation_re   = re.compile(r"""^ # (.*)$""")
sed_re           = re.compile(r"""^ ([a-z].*)$""")
sedhash_re       = re.compile(r"""(?P<sedtext>[^#]+)#(?P<commenttext>.*$)""")

explanation_text = ''
cmd_texts        = []

in_section = False


latex_escape_dict = {
    ' '    : '~',
    '\\'   : '\\bs{}',
    '^'    : '\\^{}',
    '$'    : '\\$',
    '#'    : '\\#',
    '&'    : '\\&',
    '{'    : '\\{',
    '}'    : '\\}',
    '~'    : '\\~{}',
    }


def latex_escape_nosp(text):
    text2 = ''
    for char in text:
        if char == ' ':
            text2 += ' '
        elif char in latex_escape_dict:
            text2 += latex_escape_dict[char]
        else:
            text2 += char
    return text2


def latex_escape(text):
    text2 = ''
    for char in text:
        if char in latex_escape_dict:
            text2 += latex_escape_dict[char]
        else:
            text2 += char
    return text2


def print_text():
    global cmd_texts
    global explanation_text
    #print "%% len(cmd_texts) == %d" % len(cmd_texts)
    if explanation_text.endswith('\\\\'):
        explanation_text = explanation_text.rstrip('\\\\')
        backslashes = '\\\\'
    else:
        backslashes = ''
    print '{\\ensuremath\\bullet} %s%s' % \
        (latex_escape_nosp(explanation_text), backslashes)
    if len(cmd_texts) == 1 and cmd_texts[0][1] == '':
        print '{\\hspace*{\\fill}~~\\texttt{%s}}\\hspace{0pt}\\par' % \
            latex_escape(cmd_texts[0][0])
    elif len(cmd_texts) > 0:
        print '\\par'
        for cmd_text in cmd_texts:
            print '-- %s\\hspace*{\\fill}~~\\texttt{%s}\\par' % \
                (latex_escape_nosp(cmd_text[1]),
                 latex_escape(cmd_text[0]))
    # This vspace is a value selected to make the layout correct, in that there
    # are no "paragraphs" split over pages.
    print "\\vskip 2.2pt"
    print
    explanation_text = ''
    cmd_texts = []


for line in sys.stdin:
    if line == "":
        continue
    headline_match = headline_re.search(line)
    if headline_match:
        if in_section:
            # Finish the previous section if we were in one.
            print_text()
            in_section = False
        head_line = headline_match.group(1)
        head = head_line[0] + head_line[1:].lower()
        #print >>sys.stderr, "Head line: %s" % head
        #print r"\vbox{\head{%s}" % head
        print r"\head{%s}" % head
        in_section = True
        explanation_text = ''
        continue
    if in_section:
        explanation_match = explanation_re.match(line)
        if explanation_match:
            # Find out if we're starting a new explanation.
            if len(cmd_texts) != 0:
                print_text()
            if explanation_text == '':
                explanation_text = explanation_match.group(1).strip()
            else:
                explanation_text = explanation_text + ' ' + explanation_match.group(1).strip()
            continue
        sed_match = sed_re.match(line)
        if sed_match:
            sedhash_match = sedhash_re.match(sed_match.group(1))
            if sedhash_match:
                cmd_text = [sedhash_match.group('sedtext').strip(),
                            sedhash_match.group('commenttext').strip()]
                cmd_texts.append(cmd_text)
            else:
                cmd_texts.append( (sed_match.group(1).strip(), '') )
            continue


if in_section and len(cmd_texts) > 0:
    print_text()
