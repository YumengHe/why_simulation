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
    layout = (SOURCE / 'layout.html').read_text()
    chapter_scripts = sorted({name for chapter in config['chapters'] for name in chapter.get('scripts', [])})
    asset_version = sha256(b''.join((SOURCE / 'assets' / name).read_bytes() for name in ['book.css', 'book.js', 'articulation.js', 'frames.js'] + chapter_scripts)).hexdigest()[:12]
    chapters = []
    for chapter in config['chapters']:
        content = (SOURCE / chapter['source']).read_text()
        parser = ChapterParser()
        parser.feed(content)
        chapters.append({**chapter, 'content': content, 'sections': parser.sections})
    # Keep previously shared chapter-2 fragment links working after the split.
    legacy_routes = {}
    for legacy_page, group in config.get('legacy_fragment_groups', {}).items():
        legacy_routes[legacy_page] = {
            fragment: chapter['output']
            for chapter in chapters if chapter.get('group') == group and chapter['output'] != legacy_page
            for fragment in re.findall(r'\bid="([^"]+)"', chapter['content'])
            if fragment != 'chapter-start'
        }
    OUTPUT.mkdir(exist_ok=True)
    shutil.copytree(SOURCE / 'assets', OUTPUT / 'assets', dirs_exist_ok=True)
    navigation = '<ol class="chapter-list">'
    current_group = None
    for chapter in chapters:
        group = chapter.get('group')
        if group != current_group:
            if current_group:
                navigation += '</ol></li>'
            if group:
                group_config = config['groups'][group]
                navigation += f'<li class="chapter-group"><span class="chapter-group-title"><span class="nav-number">{escape(group_config["number"])}.</span>{escape(group_config["title"])}</span><ol class="chapter-children">'
            current_group = group
        number = f'<span class="nav-number">{escape(chapter["number"])}{"" if group else "."}</span>' if chapter.get('number') else ''
        navigation += f'<li><a class="chapter-link" href="{escape(chapter["output"])}#chapter-start">{number}{escape(chapter["title"])}</a>'
        if chapter.get('show_sections'):
            navigation += '<ol class="chapter-sections">'
            for section in chapter['sections']:
                if section['id'] == 'chapter-start':
                    continue
                label = section.get('heading', section['title'])
                navigation += f'<li><a class="section-link" href="{escape(chapter["output"])}#{escape(section["id"])}">{escape(label)}</a></li>'
            navigation += '</ol>'
        navigation += '</li>'
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
            pagination += f'<a href="{escape(prev["output"])}">← {escape(prev["title"])}</a>'
        if i+1 < len(chapters):
            following = chapters[i+1]
            pagination += f'<a href="{escape(following["output"])}">{escape(following["title"])} →</a>'
        replacements = {
            'page_title': escape(chapter['title']), 'book_title': escape(config['title']),
            'home_page': escape(chapters[0]['output']),
            'description': escape(chapter.get('description', chapter['title'])),
            'repository': escape(config['repository']), 'navigation': navigation.replace('href="'+escape(chapter['output'])+'#', 'href="#'),
            'content': chapter['content'], 'pagination': pagination, 'source': escape(chapter['source']),
            'asset_version': asset_version,
            'chapter_scripts': redirect_script + '\n'.join(f'  <script src="assets/{escape(name)}?v={asset_version}" defer></script>' for name in chapter.get('scripts', []))
        }
        html = layout
        for key, value in replacements.items():
            html = html.replace('{{'+key+'}}', value)
        (OUTPUT / chapter['output']).write_text(html)
        for section in chapter['sections']:
            search_index.append({'title': section['title'], 'url': chapter['output']+'#'+section['id'], 'text': ' '.join(' '.join(section['chunks']).split())})
    (OUTPUT / 'search-index.json').write_text(json.dumps(search_index, ensure_ascii=False, indent=2)+'\n')
    (OUTPUT / '.nojekyll').touch()
    print(f'Built {len(chapters)} page(s) into {OUTPUT}')


if __name__ == '__main__':
    build()
