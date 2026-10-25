#!/usr/bin/env python3
"""Build the self-contained, non-deployed desktop design review package."""
import argparse
from collections import Counter
from html import escape
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import posixpath
import re
import shutil
from urllib.parse import urlsplit,unquote

from markdown_it import MarkdownIt

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
GUIDES={
    'docs/design/desktop-brief.md':'brief.html',
    'docs/design/identity.md':'identity.html',
    'docs/design/implementation-plan.md':'implementation.html',
    'docs/design/verification.md':'verification.html',
    'docs/story.md':'story.html',
    'docs/design.md':'design.html',
    'docs/recipes/terminal.md':'terminal.html',
}
FONT_FAMILY={'inter.woff2':'ReviewInter','noto.woff2':'ReviewNoto','meslo.woff2':'ReviewMeslo','jetbrains.woff2':'ReviewJetBrains'}


def variables(candidate, ansi=None):
    values={k.replace('_','-'):v for k,v in candidate['colors'].items()}
    values['ui']=FONT_FAMILY[candidate['ui_asset']]+',ReviewHan,sans-serif'
    values['mono']=FONT_FAMILY[candidate['mono_asset']]+',ReviewHan,monospace'
    if ansi:
        values.update({f'ansi-{index}':color for index,color in enumerate(ansi)})
    return ';'.join('--'+k+':'+v for k,v in values.items())


def link(source,target):
    url=urlsplit(target)
    if url.scheme or url.netloc or target.startswith('#'):return target
    resolved=posixpath.normpath(posixpath.join(posixpath.dirname(source),url.path))
    if resolved in GUIDES:return GUIDES[resolved]+('#'+url.fragment if url.fragment else '')
    if resolved=='design/identity.json':return 'data/identity.json'
    if resolved=='design/capabilities.json':return 'data/capabilities.json'
    if resolved=='data/identity.json':return 'data/identity.json'
    if resolved=='assets/identity.css':return 'identity.css'
    if resolved=='examples/kitty/neutral-slate.conf':return 'neutral-slate.conf'
    if resolved.startswith('docs/'):
        return 'https://github.com/byebyebryan/niri-plus/blob/main/'+resolved
    raise ValueError(f'{source}: unmapped link {target}')


def guide(source):
    md=MarkdownIt('commonmark',{'html':False}).enable('table')
    tokens=md.parse((REPO/source).read_text());counts=Counter()
    for i,token in enumerate(tokens):
        if token.type=='heading_open':
            slug=re.sub('[^a-z0-9]+','-',tokens[i+1].content.lower()).strip('-');counts[slug]+=1
            token.attrSet('id',slug if counts[slug]==1 else f'{slug}-{counts[slug]}')
        for child in token.children or []:
            if child.type=='link_open':child.attrSet('href',link(source,child.attrGet('href')))
    md.renderer.rules['table_open']=lambda *_:'<div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable design reference table"><table>\n'
    md.renderer.rules['table_close']=lambda *_:'</table></div>\n'
    body=md.renderer.render(tokens,md.options,{})
    title=(REPO/source).read_text().splitlines()[0].removeprefix('# ')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} — Niri Plus design</title><link rel="stylesheet" href="review.css"></head><body><a class="skip" href="#main">Skip to content</a><header class="report-header"><div class="page-width header-row"><a class="wordmark" href="index.html">niri<span>+</span><small>DESKTOP DESIGN REVIEW</small></a><nav aria-label="Design navigation"><a href="index.html">Visual review</a><a href="brief.html">Brief</a><a href="identity.html">Identity</a><a href="implementation.html">Implementation</a></nav></div></header><main class="guide" id="main" tabindex="-1"><p class="kicker">Design proposal · not deployed</p>{body}<p><a href="index.html">← Back to the visual review</a></p></main></body></html>'''


class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.links=[];self.h1=0;self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='h1':self.h1+=1
        if attrs.get('id'):self.ids.append(attrs['id'])
        for key in ['href','src']:
            if attrs.get(key):self.links.append(attrs[key])
        if tag=='img' and not attrs.get('alt'):raise ValueError('missing image alternative')


def build(output):
    output=output.absolute()
    if output.is_symlink() or output.resolve().is_relative_to(REPO):raise ValueError('review output must be outside the checkout')
    if output.exists() and any(output.iterdir()):raise ValueError('review output must be empty')
    identity=json.loads((ROOT/'identity.json').read_text());capabilities=json.loads((ROOT/'capabilities.json').read_text())
    selected_candidate=identity['selected_candidate']
    assert identity['status']=='selected' and selected_candidate in {candidate['id'] for candidate in identity['candidates']}
    assert identity['theme_scope']['supported_target_count']==1 and len(capabilities['items'])==22
    output.mkdir(parents=True,exist_ok=True);shutil.copytree(ROOT/'assets',output/'assets')
    (output/'data').mkdir()
    import runpy
    builder=runpy.run_path(str(REPO/'scripts/build.py'))
    selected_identity=builder['working_identity']()
    (output/'identity.css').write_text(builder['identity_css'](selected_identity))
    (output/'neutral-slate.conf').write_text(builder['kitty_fragment'](selected_identity))
    for name in ['identity.json','capabilities.json']:shutil.copyfile(ROOT/name,output/'data'/name)
    cards=[];buttons=[]
    for c in identity['candidates']:
        selected=c['id']==selected_candidate
        swatches=''.join(f'<i style="background:{c["colors"][key]}"></i>' for key in ['canvas','surface','raised','accent','warning','error','success'])
        cards.append(f'''<article class="candidate-card{' selected' if selected else ''}"><div class="mini-desktop themed" style="{variables(c)}"><div class="mini-window">CHROME<p>Read something.<br>Make something.</p><span class="mini-accent"></span></div><div class="mini-window">~/projects<br>❯ niri validate<br><em>✓ config is valid</em><span class="mini-accent"></span></div></div><div class="palette-strip" aria-label="Candidate palette">{swatches}</div><h3>{escape(c['name'])}</h3>{'<span class="recommendation-badge">Selected identity</span>' if selected else '<span class="recommendation-badge">Design history</span>'}<p>{escape(c['summary'])}</p><div class="candidate-meta">{escape(c['ui_font'])}<br>{escape(c['mono_font'])}</div></article>''')
        buttons.append(f'<button type="button" data-candidate-button="{c["id"]}" aria-pressed="{str(selected).lower()}">{escape(c["name"])}</button>')
    caps=[]
    for item in capabilities['items']:
        rows=''.join(f'<p><strong>{label}</strong>{escape(item[key])}</p>' for key,label in [('owner','Owner'),('current_path','Current path'),('reference_path','Proposed reference path'),('implementation_gap','Work to make explicit'),('hardware_variation','Variation'),('acceptance','Acceptance task')])
        caps.append(f'<details class="capability" id="cap-{item["id"]}"><summary><small>{escape(item["area"])}<span class="status-pill {item["status"]}">{escape(item["status"])}</span></small><strong>{escape(item["task"])}</strong></summary><div class="capability-body">{rows}</div></details>')
    preferred=next(c for c in identity['candidates'] if c['id']==selected_candidate)
    tokens=''.join(f'<div class="token"><div class="token-swatch" style="background:{value}" aria-hidden="true"></div><strong>{role}</strong><code>{value}</code></div>' for role,value in preferred['colors'].items())
    selected_style=variables(preferred,identity['terminal']['ansi'])
    html=(ROOT/'board/index.html').read_text()
    for key,value in {'CANDIDATE_CARDS':''.join(cards),'CANDIDATE_BUTTONS':''.join(buttons),'DASHBOARD':(ROOT/'board/dashboard.html').read_text(),'CAPABILITIES':''.join(caps),'TOKEN_GRID':tokens,'SELECTED_ID':selected_candidate,'SELECTED_STYLE':selected_style,'DATA':json.dumps({'identity':identity,'capabilities':capabilities},ensure_ascii=False).replace('</',r'<\/')}.items():html=html.replace('@@'+key+'@@',value)
    if '@@' in html:raise ValueError('unresolved review template slot')
    (output/'index.html').write_text(html)
    for name in ['review.css','review.js']:shutil.copyfile(ROOT/'board'/name,output/name)
    shutil.copyfile(REPO/'site/favicon.svg',output/'favicon.svg')
    for source,target in GUIDES.items():(output/target).write_text(guide(source))
    pages={p.name:Page(p.read_text()) for p in output.glob('*.html')}
    for name,page in pages.items():
        if page.h1!=1 or len(page.ids)!=len(set(page.ids)):raise ValueError(f'{name}: invalid headings or duplicate ids')
        for target in page.links:
            url=urlsplit(target)
            if url.scheme or url.netloc:continue
            dest=unquote(url.path) or name
            if not (output/dest).is_file():raise ValueError(f'{name}: missing {target}')
            if url.fragment and dest in pages and url.fragment not in pages[dest].ids:raise ValueError(f'{name}: missing anchor {target}')
    manifest={'status':'selected design; native adoption pending','selected_candidate':selected_candidate,'files':[]}
    for p in sorted(output.rglob('*')):
        if p.is_file():manifest['files'].append({'path':p.relative_to(output).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    (output/'review-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'pages':len(pages),'capabilities':len(capabilities['items']),'candidates':len(identity['candidates']),'files':len(manifest['files'])+1,'bytes':sum(p['bytes'] for p in manifest['files'])}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();build(args.output)
