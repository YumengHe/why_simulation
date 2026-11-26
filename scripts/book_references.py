"""Render per-page reference lists from book/references.bib.

Chapters cite a work with {{cite:key}} (or {{cite:key1,key2}}), where key is a
BibTeX key from book/references.bib. The builder replaces each marker with a
numbered link such as [1] and appends a References section listing the works
cited on that page, in order of first citation. Entries link to the paper or
project recorded in the bib file (url, eprint, or doi fields).

Parsing uses only the standard library and accepts the common BibTeX forms in
this book's file: braced or quoted values, bare words (month=July), LaTeX
accents such as Sch\"{o}nberger, and corporate authors in double braces.
Unknown citation keys and malformed keys fail the build with a clear message.
"""
from html import escape
from pathlib import Path
import re

SOURCE = Path(__file__).resolve().parents[1] / 'book'
MAX_AUTHORS = 4  # show all authors up to this count, otherwise first three + et al.

ACCENTS = {
    '"': {'a': 'ä', 'e': 'ë', 'i': 'ï', 'o': 'ö', 'u': 'ü', 'y': 'ÿ',
          'A': 'Ä', 'E': 'Ë', 'I': 'Ï', 'O': 'Ö', 'U': 'Ü'},
    "'": {'a': 'á', 'c': 'ć', 'e': 'é', 'i': 'í', 'n': 'ń', 'o': 'ó', 's': 'ś',
          'u': 'ú', 'y': 'ý', 'z': 'ź', 'A': 'Á', 'E': 'É', 'I': 'Í', 'O': 'Ó', 'U': 'Ú'},
    '`': {'a': 'à', 'e': 'è', 'i': 'ì', 'o': 'ò', 'u': 'ù',
          'A': 'À', 'E': 'È', 'I': 'Ì', 'O': 'Ò', 'U': 'Ù'},
    '^': {'a': 'â', 'e': 'ê', 'i': 'î', 'o': 'ô', 'u': 'û',
          'A': 'Â', 'E': 'Ê', 'I': 'Î', 'O': 'Ô', 'U': 'Û'},
    '~': {'a': 'ã', 'n': 'ñ', 'o': 'õ', 'A': 'Ã', 'N': 'Ñ', 'O': 'Õ'},
    'c': {'c': 'ç', 'C': 'Ç'},
    'v': {'c': 'č', 's': 'š', 'z': 'ž', 'C': 'Č', 'S': 'Š', 'Z': 'Ž'},
}


def latex_to_text(value):
    """Convert the LaTeX escapes used in the bib file to plain text."""
    for mark, letters in ACCENTS.items():
        for letter, result in letters.items():
            for pattern in (r'\%s{%s}' % (mark, letter), r'{\%s%s}' % (mark, letter), r'\%s%s' % (mark, letter)):
                value = value.replace(pattern, result)
    value = value.replace(r'\&', '&').replace('~', ' ').replace('--', '–')
    value = value.replace('{', '').replace('}', '')
    return ' '.join(value.split())


def _read_value(text, i):
    """Read one field value starting at text[i]; return (raw value, next index)."""
    while text[i].isspace():
        i += 1
    if text[i] == '{':
        depth, start = 1, i + 1
        i += 1
        while depth:
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
            i += 1
        return text[start:i - 1], i
    if text[i] == '"':
        depth, start = 0, i + 1
        i += 1
        while depth or text[i] != '"':
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
            i += 1
        return text[start:i], i + 1
    start = i
    while i < len(text) and text[i] not in ',}' and not text[i].isspace():
        i += 1
    return text[start:i], i


def load_bib(path):
    """Parse a BibTeX file into {key: {field: raw value, 'entry_type': type}}."""
    if not path.exists():
        return {}
    text = path.read_text()
    entries = {}
    for match in re.finditer(r'@(\w+)\s*\{', text):
        entry_type = match.group(1).lower()
        if entry_type in ('comment', 'preamble', 'string'):
            continue
        i = match.end()
        comma = text.index(',', i)
        key = text[i:comma].strip()
        if re.search(r'\s', key):
            raise ValueError(f'references.bib: key "{key}" contains whitespace; rename it (for example {key.replace(" ", "")!r}).')
        if key in entries:
            raise ValueError(f'references.bib: duplicate key "{key}".')
        fields = {'entry_type': entry_type}
        i = comma + 1
        while True:
            while i < len(text) and (text[i].isspace() or text[i] == ','):
                i += 1
            if i >= len(text) or text[i] == '}':
                break
            name = re.compile(r'[\w-]+').match(text, i)
            if not name:
                raise ValueError(f'references.bib: cannot read entry "{key}" near: {text[i:i + 40]!r}')
            i = name.end()
            while text[i].isspace():
                i += 1
            if text[i] != '=':
                raise ValueError(f'references.bib: expected "=" in entry "{key}" after field "{name.group(0)}".')
            value, i = _read_value(text, i + 1)
            fields[name.group(0).lower()] = value.strip()
        entries[key] = fields
    return entries


def ref_id(key):
    """A citation key as a safe HTML fragment identifier."""
    return 'ref-' + re.sub(r'[^A-Za-z0-9_-]', '-', key)


def format_authors(raw):
    """Format a BibTeX author field for display."""
    names, et_al = [], False
    for name in re.split(r'\s+and\s+', raw.strip()):
        if name.lower() == 'others':
            et_al = True
            continue
        if name.startswith('{') and name.endswith('}'):
            names.append(latex_to_text(name))  # corporate author: keep as written
            continue
        name = latex_to_text(name)
        if ',' in name:
            last, _, first = name.partition(',')
            name = f'{first.strip()} {last.strip()}'.strip()
        names.append(name)
    if len(names) > MAX_AUTHORS:
        names, et_al = names[:3], True
    joined = ', '.join(names)
    return f'{joined} et al.' if et_al else joined


def entry_links(fields):
    """Collect up to two labeled links for an entry: url, arXiv, or DOI."""
    links, seen = [], set()

    def add(label, href):
        if href and href not in seen:
            links.append((label, href))
            seen.add(href)

    url = fields.get('url', '')
    if url:
        if 'arxiv.org' in url:
            label = 'arXiv'
        elif 'github.com' in url:
            label = 'GitHub'
        elif 'doi.org' in url:
            label = 'DOI'
        else:
            label = 'link'
        add(label, url)
    if fields.get('eprint'):
        add('arXiv', f"https://arxiv.org/abs/{fields['eprint']}")
    if fields.get('doi') and not any('doi.org' in href for _, href in links):
        add('DOI', f"https://doi.org/{fields['doi']}")
    if not links:  # some entries only name the arXiv id inside journal/booktitle
        venue = fields.get('journal', '') + ' ' + fields.get('booktitle', '')
        found = re.search(r'arXiv:\s*(\d{4}\.\d{4,5})', venue)
        if found:
            add('arXiv', f'https://arxiv.org/abs/{found.group(1)}')
    return links[:2]


def format_entry(fields):
    """Format one bib entry as an HTML fragment (without the <li>)."""
    parts = []
    if fields.get('author'):
        authors = format_authors(fields['author'])
        parts.append(escape(authors if authors.endswith('.') else authors + '.'))
    if fields.get('title'):
        parts.append(f"<em>{escape(latex_to_text(fields['title']))}</em>.")
    venue = ''
    entry_type = fields['entry_type']
    if entry_type == 'book':
        venue = ', '.join(latex_to_text(fields[f]) for f in ('publisher', 'address') if fields.get(f))
    elif fields.get('booktitle'):
        venue = latex_to_text(fields['booktitle'])
    elif fields.get('journal'):
        venue = latex_to_text(fields['journal'])
        if fields.get('volume'):
            venue += f" {fields['volume']}"
            if fields.get('number'):
                venue += f"({fields['number']})"
            if fields.get('pages'):
                venue += f":{latex_to_text(fields['pages'])}"
    elif fields.get('howpublished'):
        venue = latex_to_text(fields['howpublished'])
    elif fields.get('eprint'):
        venue = f"arXiv preprint arXiv:{fields['eprint']}"
    tail = ', '.join(piece for piece in (venue, fields.get('year', '')) if piece)
    if tail:
        parts.append(escape(tail) + '.')
    if fields.get('note'):
        parts.append(escape(latex_to_text(fields['note'])) + '.')
    links = ' '.join(f'<a href="{escape(href, quote=True)}">{escape(label)}</a>' for label, href in entry_links(fields))
    if links:
        parts.append(links)
    return ' '.join(parts)


def expand_citations(content, bib, page):
    """Replace {{cite:...}} markers; return the content and cited keys in order."""
    cited = []

    def replace(match):
        numbers = []
        for key in (k.strip() for k in match.group(1).split(',')):
            if key not in bib:
                known = ', '.join(sorted(bib)) or '(references.bib is missing or empty)'
                raise ValueError(f'{page}: unknown citation key "{key}". Known keys: {known}')
            if key not in cited:
                cited.append(key)
            numbers.append(f'<a href="#{ref_id(key)}">{cited.index(key) + 1}</a>')
        return '<sup class="citation">[' + ', '.join(numbers) + ']</sup>'

    content = re.sub(r'\{\{cite:([^}]+)\}\}', replace, content)
    return content, cited


def references_section(cited, bib):
    """The References section appended to a page that cites at least one work."""
    items = ''.join(f'\n  <li id="{ref_id(key)}">{format_entry(bib[key])}</li>' for key in cited)
    return ('\n\n<section id="references" data-title="References">\n'
            '<h2>References</h2>\n'
            f'<ol class="reference-list">{items}\n</ol>\n'
            '</section>\n')


if __name__ == '__main__':
    bib = load_bib(SOURCE / 'references.bib')
    print(f'{len(bib)} entries parse cleanly:')
    for key, fields in bib.items():
        print(f'- [{key}] ' + re.sub(r'<[^>]+>', '', format_entry(fields)))
