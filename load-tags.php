#!/usr/bin/env php
<?php

if (!empty($_SERVER['REMOTE_ADDR'])) {
	die('Not for remote use.');
}

$l10n = [];
$keys = [];

$gdocs = [
	'https://docs.google.com/spreadsheets/d/1ISQ2KyXqSw-YlnNqSw7DrMM1oB7elI-izAV6Nuu1WWo/export?exportFormat=csv',
	];
$csv = fopen('php://memory', 'w+b');
foreach ($gdocs as $gd) {
	fwrite($csv, file_get_contents($gd));
	fwrite($csv, "\n");
}
fseek($csv, 0);

$iso = fgetcsv($csv);

$suf = '';
if (!empty($argv[1])) {
	$suf = '-'.$argv[1];
}

while ($l = fgetcsv($csv)) {
	if (preg_match('~[\s\pZ]~u', $l[0]) || empty($l[1])) {
		continue;
	}
	if (array_key_exists($l[0], $keys)) {
		fprintf(STDERR, "Duplicate key %s\n", $l[0]);
		//break;
	}
	$keys[$l[0]] = $l[0];

	for ($i=1 ; $i<4 ; ++$i) {
		$t = trim($l[$i] ?? '');
		$l10n[$iso[$i]][$l[0]] = $t;
	}
}

for ($i=1 ; $i<4 ; ++$i) {
	$out = <<<XHTML
<chapter name="tags">
<!--
Tags @ Google Docs: https://docs.google.com/spreadsheets/d/1ISQ2KyXqSw-YlnNqSw7DrMM1oB7elI-izAV6Nuu1WWo
-->

XHTML;
	$sect = false;
	foreach ($keys as $k) {
		$t = $l10n[$iso[$i]][$k];
		if (preg_match('~^HDR_.*?_([^_]+)$~u', $k, $m)) {
			if ($sect) {
				$out .= <<<XHTML
</chapter>


XHTML;
			}
			$sect = true;
			$s_k = strtolower($m[1]);
			$out .= <<<XHTML
<chapter name="{$s_k}">
<h1>{$t}</h1>


XHTML;
		}
		else if (!empty($t)) {
			$s_k = htmlspecialchars($k);
			$out .= <<<XHTML
<article id="{$k}">
<h1>{$s_k}</h1>
<p>{$t}</p>
</article>


XHTML;
		}
	}
	if ($sect) {
		$out .= <<<XHTML

</chapter>

XHTML;
	}
	$out .= <<<XHTML

</chapter>

XHTML;
	file_put_contents($iso[$i].'/tags.html', $out);
}
