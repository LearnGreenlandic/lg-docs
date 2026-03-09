#!/usr/bin/env python3
import copy
import glob
import os
import regex as re
import subprocess
import hashlib
from pathlib import Path
import shutil
import sqlite3
from lxml import etree

dir = os.path.dirname(__file__) + '/..'
os.chdir(dir)

subprocess.run(['rm', '-rf', 'build'])
os.makedirs('build')
shutil.copy(dir+'/_src/.htaccess', 'build/.htaccess')
subprocess.run(['sqlite3', 'build/docs.sqlite', '-init', '_src/schema.sql'], input='')

con = sqlite3.connect('build/docs.sqlite')
db = con.cursor()

g = {
	'db': db,
	'lang': '',
	'l10n': {},
	}

def tr(str):
	global g
	if not str in g['l10n']:
		return str
	return g['l10n'][str]

def esc_html(str):
	str = re.sub(r'&', '&amp;', str)
	str = re.sub(r'<', '&lt;', str)
	str = re.sub(r'>', '&gt;', str)
	str = re.sub(r'"', '&quot;', str)
	str = re.sub(r"'", '&apos;', str)
	return str

def to_html(e):
	return etree.tostring(e, encoding='UTF-8', method='html').decode(encoding='UTF-8')

def handle_article(a):
	global g
	id = a.attrib['id']
	row = {
		'title': id,
		'ref': '',
		'ref_url': '',
		'short': '',
		'long': '',
	}

	# Ensure tags are in a certain order
	na = []
	for e in a:
		if e.tag == 'h1':
			na.append(e)
	for e in a:
		if e.tag == 'ref':
			na.append(e)
	for e in a:
		if e.tag != 'h1' and e.tag != 'ref':
			na.append(e)
	a[:] = na

	for e in a:
		if e.tag == 'h1':
			pe = copy.deepcopy(e)
			fns = pe.findall('lg-fn')
			for fn in fns:
				pe.remove(fn)
			row['title'] = etree.tostring(pe, encoding='UTF-8', method='text').strip()
		elif e.tag == 'ref':
			row['ref'] = e.text
			row['ref_url'] = e.attrib['to'].strip()
			e.tag = 'a'
			e.attrib['href'] = 'https://learngreenlandic.com/online/lg' + e.attrib['to']
			e.attrib.pop('to')
			if e.attrib['href'].endswith('#'):
				e.attrib['href'] += id.lower()
		elif e.tag == 'p':
			row['short'] += to_html(e)
		elif e.tag == 'expand':
			row['long'] += re.sub(r'</?expand>\n*', '', to_html(e))
	g['db'].execute("INSERT INTO articles (a_title, a_ref, a_ref_url, a_short, a_long) VALUES (:title, :ref, :ref_url, :short, :long)", row)
	return g['db'].lastrowid

def handle_chapter(ch):
	global g
	name = title = ch.attrib['name']
	os.makedirs(title, exist_ok=True)
	os.chdir(title)

	has_toc = False

	elems = []
	for e in ch:
		if e.tag == 'toc':
			has_toc = True
	for e in ch:
		if e.tag == 'h1' and not has_toc:
			toc = e.makeelement('toc')
			e.addnext(toc)
			has_toc = True

	for e in ch:
		if e.tag == 'chapter':
			nest = handle_chapter(e)
			a = e.makeelement('a', href=nest[0]+'/')
			a.text = nest[1]
			elems.append(a)
			elems.append(e.makeelement('br'))
			continue
		elif e.tag == 'h1':
			title = e.text
		elems.append(e)

	if elems:
		html = f'''<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
	<title>{title}</title>

	<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11/font/bootstrap-icons.css">
	<link rel="stylesheet" href="https://learngreenlandic.com/online/static/bootswatch.darkly.css">

	<script src="https://cdn.jsdelivr.net/npm/jquery@3.7/dist/jquery.min.js"></script>
	<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3/dist/js/bootstrap.bundle.min.js"></script>

	<link href="https://fonts.bunny.net/css?family=Noto+Sans&display=swap" rel="stylesheet">
	<link href="https://learngreenlandic.com/online/static/lg.css" rel="stylesheet">
	<script src="https://learngreenlandic.com/online/static/lg.js"></script>
</head>
<body data-theme="darkly">
<div class="container">
'''
		for e in elems:
			if e.tag == 'article':
				id = handle_article(e)
				als = (e.attrib['id'] + ';' + e.get('alias', default='')).strip().split(';')
				for a in als:
					a = a.strip()
					if not len(a):
						continue
					g['db'].execute(f"INSERT INTO lookups (l_id, l_{g['lang']}) VALUES (?, ?) ON CONFLICT DO UPDATE SET l_{g['lang']} = ?", [a, id, id])

		toc = []
		for e in elems:
			if e.tag == 'toc':
				c = e
				while c.tag != 'chapter':
					c = c.getparent()

				seen_toc = False
				for h in c.iterdescendants(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'toc']):
					if h.tag == 'toc':
						seen_toc = True
						continue
					if not seen_toc:
						continue

					if not 'id' in h.attrib:
						h.attrib['id'] = '_' + h.tag + '_' + str(len(toc))
					nh = copy.deepcopy(h)

					fns = h.findall('lg-fn')
					for fn in fns:
						h.remove(fn)
					id = h.attrib['id']
					if h.getparent().tag == 'article':
						id = h.getparent().attrib['id']
					toc.append([str(etree.tostring(h, encoding='UTF-8', method='text'), encoding='UTF-8').strip(), h.tag, id])

					h.clear()
					h.attrib['class'] = 'lg-heading lg-heading-' + h.tag
					h.tag = 'div'
					h.append(nh)
					nh = h.makeelement('a')
					nh.attrib['class'] = 'lg-heading-toc'
					nh.attrib['href'] = '#_toc'
					nh.text = '^'
					h.append(nh)

				e.tag = 'nav'
				e.attrib['id'] = '_toc'
				ul = e.makeelement('ul')
				ul.attrib['class'] = 'lg-toc'
				e.append(ul)
				for t in toc:
					li = ul.makeelement('li')
					li.attrib['class'] = 'lg-toc-' + t[1]
					a = li.makeelement('a')
					a.text = t[0]
					a.attrib['href'] = '#' + t[2]
					li.append(a)
					ul.append(li)

			html += re.sub(r'</?expand>\n*', '', to_html(e))
		html += '''</div>
</body>
</html>
'''
		Path('index.html').write_text(html)
	os.chdir('..')
	return [name, title]

def handle_include(fn):
	p = Path(fn).absolute()
	os.chdir(p.parent)
	html = p.read_text()
	if ms := re.findall(r'(<include file="([^"]+)"\s*/>)', html):
		for m in ms:
			inc = ''
			files = glob.glob(m[1])
			for file in files:
				inc += handle_include(file)
				os.chdir(p.parent)
			html = html.replace(m[0], inc)
	return html

for lang in ['dan', 'eng', 'kal']:
	os.chdir(dir)
	if not os.path.exists(f'{lang}/_docs.html'):
		continue

	g['lang'] = lang

	os.chdir(lang)
	if os.path.exists('l10n.tsv'):
		tsv = Path('l10n.tsv').read_text().strip().splitlines()
		for t in tsv:
			t = re.sub(r'#.*', '', t).strip()
			if t == '':
				continue
			t = t.split('\t')
			g['l10n'][t[0].strip()] = t[1].strip()
	html = handle_include('_docs.html')

	fns = re.findall(r'<lg-fn-def n="([^"]+)">(.*?)</lg-fn-def>', html)
	for fn in fns:
		h = hashlib.sha256(bytes(fn[1], 'UTF-8')).hexdigest()[0:8]
		html = html.replace(f'<lg-fn>{fn[0]}</lg-fn>', f'<lg-fn>{h}</lg-fn>', 1)
		html = html.replace(f'<lg-fn-def n="{fn[0]}">', f'<lg-fn-def n="{h}">', 1)

	parser = etree.HTMLParser()
	dom = etree.fromstring(html, parser)

	os.chdir(dir)
	os.makedirs(f'build/{lang}', exist_ok=True)

	body = dom.find('body')

	index = []
	for h in body.iterdescendants(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
		index.append(h)
		if not 'id' in h.attrib:
			h.attrib['id'] = '_' + h.tag + '_' + str(len(index))
		p = []
		for c in h.iterancestors('chapter'):
			p.append(c.attrib['name'])
		p.reverse()
		h.attrib['data-path'] = '/'.join(p)

	index = []
	for h in body.iterdescendants(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
		id = h.attrib['id']
		for c in h.iterancestors('article'):
			id = c.attrib['id']
			break
		index.append([str(etree.tostring(h, encoding='UTF-8', method='text'), encoding='UTF-8').strip(), h.attrib['data-path'], id])
		del(h.attrib['data-path'])
	index.sort(key=lambda x: x[0])

	for ch in body.iterchildren('chapter'):
		os.chdir(dir + f'/build/{lang}')
		handle_chapter(ch)

	title = tr('HDR_INDEX')
	html = f'''<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
	<title>{title}</title>

	<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11/font/bootstrap-icons.css">
	<link rel="stylesheet" href="https://learngreenlandic.com/online/static/bootswatch.darkly.css">

	<script src="https://cdn.jsdelivr.net/npm/jquery@3.7/dist/jquery.min.js"></script>
	<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3/dist/js/bootstrap.bundle.min.js"></script>

	<link href="https://fonts.bunny.net/css?family=Noto+Sans&display=swap" rel="stylesheet">
	<link href="https://learngreenlandic.com/online/static/lg.css" rel="stylesheet">
	<script src="https://learngreenlandic.com/online/static/lg.js"></script>
</head>
<body data-theme="darkly">
<div class="container">
<h1>{title}</h1>
'''
	last = ''
	for i in index:
		if last != i[0][0]:
			last = i[0][0]
			html += '<hr>\n'
			html += f'<h2>{last}</h2>\n'
		html += '<a href="./' + esc_html(i[1]) + '/#' + esc_html(i[2]) + '">' + esc_html(i[0]) + '</a><br>\n'
	html += '''</div>
</body>
</html>
'''
	Path('_index.html').write_text(html)

con.commit()
