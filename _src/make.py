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
			e.attrib['href'] = '/online/lg' + e.attrib['to']
			e.attrib.pop('to')
			if e.attrib['href'].endswith('#'):
				e.attrib['href'] += id.lower()
		elif e.tag == 'p':
			row['short'] += etree.tostring(e, encoding='UTF-8', method='html').decode(encoding='UTF-8')
		elif e.tag == 'expand':
			row['long'] += re.sub(r'</?expand>\n*', '', etree.tostring(e, encoding='UTF-8', method='html').decode(encoding='UTF-8'))
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
	<title>{title}</title>
</head>
<body>
'''
		for e in elems:
			if e.tag == 'article':
				id = handle_article(e)
				als = (e.attrib['id'] + ' ' + e.get('alias', default='')).strip().split(' ')
				for a in als:
					db.execute(f"INSERT INTO lookups (l_id, l_{lang}) VALUES (?, ?) ON CONFLICT DO UPDATE SET l_{lang} = ?", [a, id, id])
			html += re.sub(r'</?expand>\n*', '', etree.tostring(e, encoding='UTF-8', method='html').decode(encoding='UTF-8'))
		html += '''</body>
</html>
'''
		Path('index.html').write_text(html)
	os.chdir('..')
	return [name, title]

for lang in ['dan', 'eng', 'kal']:
	os.chdir(dir)
	if not os.path.exists(f'{lang}/_docs.html'):
		continue

	os.chdir(lang)
	html = Path(f'_docs.html').read_text()
	if ms := re.findall(r'(<include file="([^"]+)"\s*/>)', html):
		for m in ms:
			inc = ''
			files = glob.glob(m[1])
			for file in files:
				inc += Path(file).read_text()
			html = html.replace(m[0], inc)

	fns = re.findall(r'<lg-fn-def n="([^"]+)">(.*?)</lg-fn-def>', html)
	for fn in fns:
		h = hashlib.sha256(bytes(fn[1], 'UTF-8')).hexdigest()[0:8]
		html = re.sub(f'<lg-fn>{fn[0]}</lg-fn>', f'<lg-fn>{h}</lg-fn>', html, 1)
		html = re.sub(f'<lg-fn-def n="{fn[0]}">', f'<lg-fn-def n="{h}">', html, 1)

	parser = etree.HTMLParser()
	dom = etree.fromstring(html, parser)

	os.chdir(dir)
	os.makedirs(f'build/{lang}', exist_ok=True)

	body = dom.find('body')
	for ch in body.iterchildren('chapter'):
		os.chdir(dir + f'/build/{lang}')
		handle_chapter(ch)

con.commit()
