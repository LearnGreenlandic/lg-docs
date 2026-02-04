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

def to_html(e):
	return etree.tostring(e, encoding='UTF-8', method='html').decode(encoding='UTF-8')

def handle_article(a):
	global db
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
	db.execute("INSERT INTO articles (a_title, a_ref, a_ref_url, a_short, a_long) VALUES (:title, :ref, :ref_url, :short, :long)", row)
	return db.lastrowid

def handle_chapter(ch):
	global lang, db
	name = title = ch.attrib['name']
	os.makedirs(title, exist_ok=True)
	os.chdir(title)

	elems = []
	for e in ch:
		if e.tag == 'chapter':
			nest = handle_chapter(e)
			a = etree.Element('a', href=nest[0]+'/')
			a.text = nest[1]
			elems.append(a)
			elems.append(etree.Element('br'))
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
					db.execute(f"INSERT INTO lookups (l_id, l_{lang}) VALUES (?, ?) ON CONFLICT DO UPDATE SET l_{lang} = ?", [a, id, id])
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

	os.chdir(lang)
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
	for ch in body.iterchildren('chapter'):
		os.chdir(dir + f'/build/{lang}')
		handle_chapter(ch)

con.commit()
