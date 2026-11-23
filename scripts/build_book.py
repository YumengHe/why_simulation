#!/usr/bin/env python3
"""Build a portable static webbook with Python's standard library."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from hashlib import sha256
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'book'
OUTPUT = ROOT / 'docs'


class ChapterParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections = []
        self.current = None
        self.in_heading = False
        self.heading = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'header' and attrs.get('id') == 'chapter-start':
            self.current = {'id': 'chapter-start', 'title': '', 'chunks': []}
            self.sections.append(self.current)
        if tag == 'section' and 'data-title' in attrs:
            self.current = {'id': attrs['id'], 'title': attrs['data-title'], 'chunks': []}
            self.sections.append(self.current)
        if tag in ('h1', 'h2'):
            self.in_heading = True
            self.heading = []

    def handle_endtag(self, tag):
        if tag in ('h1', 'h2') and self.current:
            self.current['heading'] = ' '.join(''.join(self.heading).split())
            if not self.current['title']:
                self.current['title'] = self.current['heading']
            self.in_heading = False

    def handle_data(self, data):
        if self.current:
            self.current['chunks'].append(data)
        if self.in_heading:
            self.heading.append(data)


def build():
    config = json.loads((SOURCE / 'book.json').read_text())
    highlight_additions = config.get('review_highlight_additions', False)
    layout = (SOURCE / 'layout.html').read_text()
    chapter_scripts = sorted({name for chapter in config['chapters'] for name in chapter.get('scripts', [])})
    asset_version = sha256(b''.join((SOURCE / 'assets' / name).read_bytes() for name in ['book.css', 'book.js', 'articulation.js', 'frames.js'] + chapter_scripts)).hexdigest()[:12]
    chapters = []
    for chapter in config['chapters']:
        content = (SOURCE / chapter['source']).read_text()
        if '{{citation_bibtex}}' in content:
            citation = (SOURCE / 'citation.bib').read_text().strip()
            content = content.replace('{{citation_bibtex}}', escape(citation))
        parser = ChapterParser()
        parser.feed(content)
        chapters.append({**chapter, 'content': content, 'sections': parser.sections})
    # Preserve shared fragment URLs when sections move between pages.
    legacy_routes = {}
    for legacy_page, group in config.get('legacy_fragment_groups', {}).items():
        legacy_routes[legacy_page] = {
            fragment: chapter['output']
            for chapter in chapters if chapter.get('group') == group and chapter['output'] != legacy_page
            for fragment in re.findall(r'\bid="([^"]+)"', chapter['content'])
            if fragment != 'chapter-start'
        }
    output_fragments = {
        chapter['output']: set(re.findall(r'\bid="([^"]+)"', chapter['content']))
        for chapter in chapters
    }
    for legacy_page, routes in config.get('legacy_fragment_redirects', {}).items():
        if legacy_page not in output_fragments:
            continue
        for fragment, target in routes.items():
            if target not in output_fragments:
                continue
            if target == legacy_page or fragment == 'chapter-start':
                raise ValueError(f'Invalid fragment redirect: {legacy_page}#{fragment}')
            if fragment not in output_fragments[target]:
                raise ValueError(f'Missing redirect target: {target}#{fragment}')
            legacy_routes.setdefault(legacy_page, {})[fragment] = target
    OUTPUT.mkdir(exist_ok=True)
    shutil.copytree(SOURCE / 'assets', OUTPUT / 'assets', dirs_exist_ok=True)
    shutil.copyfile(SOURCE / 'citation.bib', OUTPUT / 'citation.bib')
    navigation = '<ol class="chapter-list">'
    current_group = None
    current_subgroup = None
    for chapter in chapters:
        group = chapter.get('group')
        if group != current_group:
            if current_subgroup:
                navigation += '</ol></li>'
                current_subgroup = None
            if current_group:
                navigation += '</ol></li>'
            if group:
                group_config = config['groups'][group]
                group_review = ' draft-addition' if group_config.get('review_added') else ''
                navigation += f'<li class="chapter-group"><span class="chapter-group-title{group_review}"><span class="nav-number">{escape(group_config["number"])}.</span>{escape(group_config["title"])}</span><ol class="chapter-children">'
            current_group = group
        subgroup = chapter.get('subgroup')
        if subgroup != current_subgroup:
            if current_subgroup:
                navigation += '</ol></li>'
            if subgroup:
                subgroup_title = config['groups'][group]['subgroups'][subgroup]
                navigation += f'<li class="chapter-subgroup"><span class="chapter-subgroup-title">{escape(subgroup_title)}</span><ol class="chapter-subpages">'
            current_subgroup = subgroup
        number = f'<span class="nav-number">{escape(chapter["number"])}{"" if group else "."}</span>' if chapter.get('number') else ''
        chapter_review = ' draft-addition' if chapter.get('review_added') else ''
        navigation += f'<li><a class="chapter-link{chapter_review}" href="{escape(chapter["output"])}#chapter-start">{number}{escape(chapter["title"])}</a>'
        if chapter.get('show_sections'):
            navigation += '<ol class="chapter-sections">'
            for section in chapter['sections']:
                if section['id'] == 'chapter-start':
                    continue
                label = section.get('heading', section['title'])
                navigation += f'<li><a class="section-link" href="{escape(chapter["output"])}#{escape(section["id"])}">{escape(label)}</a></li>'
            navigation += '</ol>'
        navigation += '</li>'
    if current_subgroup:
        navigation += '</ol></li>'
    if current_group:
        navigation += '</ol></li>'
    navigation += '</ol>'
    search_index = []
    for i, chapter in enumerate(chapters):
        redirect_script = ''
        if chapter['output'] in legacy_routes:
            routes = json.dumps(legacy_routes[chapter['output']], ensure_ascii=False)
            redirect_script = '<script>(() => { const routes = '+routes+'; function redirect() { const hash = location.hash.slice(1); if (routes[hash]) location.replace(routes[hash]+location.hash); } redirect(); addEventListener("hashchange", redirect); })();</script>\n'
        pagination = ''
        if i > 0:
            prev = chapters[i-1]
            pagination += f'<a class="page-previous" rel="prev" href="{escape(prev["output"])}">← {escape(prev["title"])}</a>'
        if i+1 < len(chapters):
            following = chapters[i+1]
            pagination += f'<a class="page-next" rel="next" href="{escape(following["output"])}">{escape(following["title"])} →</a>'
        replacements = {
            'page_title': escape(chapter['title']), 'book_title': escape(config['title']),
            'home_page': escape(chapters[0]['output']),
            'description': escape(chapter.get('description', chapter['title'])),
            'repository': escape(config['repository']), 'navigation': navigation.replace('href="'+escape(chapter['output'])+'#', 'href="#'),
            'content': chapter['content'], 'pagination': pagination, 'source': escape(chapter['source']),
            'asset_version': asset_version,
            'review_additions': 'true' if highlight_additions else 'false',
            'chapter_scripts': redirect_script + '\n'.join(f'  <script src="assets/{escape(name)}?v={asset_version}" defer></script>' for name in chapter.get('scripts', []))
        }
        html = layout
        for key, value in replacements.items():
            html = html.replace('{{'+key+'}}', value)
        (OUTPUT / chapter['output']).write_text(html)
        for section in chapter['sections']:
            search_index.append({'title': section['title'], 'url': chapter['output']+'#'+section['id'], 'text': ' '.join(' '.join(section['chunks']).split())})
    # Root URLs open the overview. Historical index.html section bookmarks
    # still reach the articulation lesson that formerly occupied index.html.
    home = chapters[0]['output']
    old_ids = sorted(output_fragments.get('articulated-objects.html', set()) - {'chapter-start'})
    root_redirect = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>'+escape(config['title'])+'</title>'
    root_redirect += '<script>const oldSections = '+json.dumps(old_ids)+'; const target = oldSections.includes(location.hash.slice(1)) ? "articulated-objects.html" : '+json.dumps(home)+'; location.replace(target + location.search + location.hash);</script>'
    root_redirect += '<meta http-equiv="refresh" content="0;url='+escape(home)+'"></head><body><a href="'+escape(home)+'">Open the overview</a></body></html>'
    (OUTPUT / 'index.html').write_text(root_redirect+'\n')
    (OUTPUT / 'search-index.json').write_text(json.dumps(search_index, ensure_ascii=False, indent=2)+'\n')
    (OUTPUT / '.nojekyll').touch()
    print(f'Built {len(chapters)} page(s) into {OUTPUT}')


if __name__ == '__main__':
    build()
