Der er ikke noget der hedder mindre tekst. Du kan kun få større tekst, og det er kun headlines og warnings og lignende der skal være større. Brødtekststørrelse er ikke noget man må røre ved normalt, fordi det fungerer dårligt på mobile/handikap-platforme. Man skal bruge andre metoder til at fremhæve/nedtone tekst.

Eksempel (med et custom `expand`-tag til formålet):
```
<article id="Trm">
<h1>Trm</h1>
<p>Terminalis / ”til”-kasus</p>
<expand>
<p>Terminalis hedder piffilerut på grønlandsk. Termen er stort set ukendt i andre sprogs grammatik. Den blev introduceret af Samuel Kleinschmidt i 1851-grammatikken og har således en meget lang tradition. I nyere tid er det dog især blandt udenlandske lingvister blevet almindeligt at anvende termen illativ, som er velkendt i mange sprog. Jeg mener dog, at dette er særdeles uheldigt, for terminalis har mange flere funktioner i grønlandsk end illativ har i fx dansk</p>
</expand>
</article>
```

Linking fra LG til docs er: `<a class="tip">Trm</a>` eller `<a class="tip" data-which="Trm">Terminalis</a>`

Alle sprog skal have samme ID'er. Så kan de bruges til at påpege hvor en oversættelse mangler. Men, i et enkelt sprog skal ID'er være unikke. Så det er fint at `dan` og `eng` begge har `Trm`, men `dan` må ikke have to `Trm`.
