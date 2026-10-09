# S1.1 Das KISZ-Wiki als Rückgrat ohne Overhead

## 1. Header

- Level: component
- ID: S1.1
- Meta: ../../plan.md
- Open for Hanno Müller before the talk: ob der Nextcloud-Ordner korrigiert ist (Sprechernotiz Folie 7; sonst den Halbsatz "und ich habe den Ordner korrigiert" weglassen); Zahlen (rund 140 Seiten, rund 8.000 Tokens) neu zählen; Verweis auf die Wiki-Vorlage (Issue #2; Folie 12 und X6) fügt Hanno Müller selbst ein, sobald sie nach der Sicherheitsprüfung veröffentlicht ist (meta plan, Abschnitt 8). Achtung: `make_slides.py` überschreibt das Deck; den Verweis deshalb auch hier in Folie 12 und X6 eintragen oder nach dem letzten Lauf des Skripts von Hand einfügen.
- Status log:
  - 2026-10-09 created from interface version 1
  - 2026-10-09 audience, S1.1, plan review: complete
  - 2026-10-09 presenter, S1.1, full: complete (estimate 22,0 of 20 min before cuts)
  - 2026-10-09 review findings folded in: Folie 4 mit drei Wegen (von Hand, RAG, LLM-Wiki) statt RAG als Pflegeweg; "freigeben" für Änderungen, Prüfstempel in den Anhang; Seitenzahl einheitlich rund 140; Folie 6 sagt den Unterschied zu RAG in einem Satz; Folie 7 ohne Slack und To-dos (die kommen auf Folie 9), Datumsbeispiel als Fund beim Einlesen; Folie 8 mit echtem Befund der Durchsicht vom 2026-10-09; Folie 9 sagt, was automatisch läuft und was auf Zuruf; Folie 10 sagt, dass wir Claude nutzen; Folie 12 mit zwei Fragepaaren statt vier Einzelfragen; Klickfolge Folie 2 in vier Schritten; Kürzungen des Presenters 1 bis 5 übernommen
  - 2026-10-09 interface check: meta version 2 (change C1), copy updated
  - 2026-10-09 changes by Hanno Müller: keine Zahlen für Arbeitszeit und Änderungen pro Woche; Fotos geliefert; Karpathy-Gist; Liste der Umsetzungen aus der Community als Anhang X7; Anfrage an die Öffentlichkeitsarbeit war auf Zuruf (Wiki-Seite des Forums)
  - 2026-10-09 confirmed by Hanno Müller ("Start creating the slides")
  - 2026-10-09 creator, S1.1: complete (llm-wiki_intro.pptx, 20 slides: 12 plus divider "Anhang" plus X1 to X7; make_figures.py, make_slides.py)
  - 2026-10-09 audience, S1.1, material review: complete
  - 2026-10-09 presenter, S1.1, full plus light boundary check to S1.2: complete (estimate 20,5 of 20 min; change requests CR1 to CR4)
  - 2026-10-09 fixes F1 to F12 written into this plan, awaiting confirmation by Hanno Müller before the next creator run
  - 2026-10-09 portraits downscaled to 500 px (david.png stays 192 px); deck rebuilt with the unchanged make_slides.py, 9,8 MB to 4,6 MB, content unchanged

## 2. Interface (read-only copy)

| Field | Value |
|---|---|
| ID, type | S1.1, Input (slides) |
| Minutes | 20 |
| Goals served | G1, G2, G3, G4; führt die vier Fragen und die Faustregel für G5 ein |
| Entry state | Die Teilnehmenden kennen RAG als Idee (Thema des Forums), kennen das KI-Servicezentrum Berlin-Brandenburg (KISZ) höchstens dem Namen nach und sein Wiki gar nicht. Sie haben nichts geöffnet. |
| Exit state | Die Teilnehmenden kennen die Aufgaben des KISZ neben dem Engineering, die drei Schichten und den Pflegekreislauf des Wikis, in dem Menschen nur Quellen geben und freigeben, und zwei Abläufe, die das Wiki anstößt. Sie können RAG und LLM-Wiki unterscheiden und haben die vier Fragen mit Faustregel gesehen. Die letzte Folie übergibt an die Live-Demo. |
| Assets | Fotos der Engineers als Kreise, Kopf in der Mitte: `components/S1.1-input/assets/team/{hanno,felix,mario,paras,david,jill}.png` (Rohfotos in `tmp/`, nicht versioniert; david.png nur 192 px); Diagramme nach figures-bw (drei Schichten, Pflegekreislauf, Vergleich Wiki und RAG); Tabelle Entscheidungscheck aus Abschnitt 3; Zahlen aus kisz-context, Stand 2026-10-09, vor dem Talk neu zählen |
| File | `03_workshop/261102-llm-wiki/llm-wiki_intro.pptx`, das ganze Deck (Titel, Inhalt, Anhang) |
| Version | 2 |

## 3. Structure

### Slides (deck section)

Overview. Minutes nach Faustregel (1,5 bis 2 min pro Inhaltsfolie); Summe 20,0 von 20 min. Kürzung im Ernstfall: Folie 5 (Karpathy nur einen Halbsatz), dann Folie 9 (nur zwei Zeilen sprechen).

| # | Roam beat | Title | Min | Goals | Checkpoint |
|---|---|---|---|---|---|
| 1 | destination | Das KISZ-Wiki: Wissen verdichten statt suchen | 0,5 | n/a | none |
| 2 | destination | Sechs Engineers, viele Aufgaben | 2 | n/a | Kennen Sie das aus Ihrem Team? |
| 3 | route | Ein System, das uns kennt | 1,5 | n/a | Ist klar, wohin wir gehen? |
| 4 | route | Wie pflegen wir das Rückgrat ohne Overhead? | 2 | G1 | Handzeichen |
| 5 | first step | Das KISZ-Wiki: drei Schichten | 2 | G2 | Wer schreibt, wer gibt frei? |
| 6 | next steps | So beantwortet die KI eine Frage | 1,5 | G2 | Wer hat entschieden, welche Seite gelesen wird? |
| 7 | next steps | Wie Neues hineinkommt | 2 | G3 | Welcher Schritt bleibt bei uns? |
| 8 | next steps | Wie das Wiki aktuell bleibt | 1,5 | G3 | Wer entscheidet, was stimmt? |
| 9 | next steps | Was das Wiki auslöst | 1,5 | G4 | rhetorisch |
| 10 | almost there | Warum kein RAG? | 2 | G1 | Was müsste passieren, damit das nicht mehr reicht? |
| 11 | almost there | Wo RAG gewinnt | 1,5 | G1, G5 | Wo steht Ihr Team: eher bei 140 oder bei 2.800 Seiten? (rhetorisch) |

Antworten aus dem Raum nur auf Folie 4 (Handzeichen), 5 und 10; alle anderen Checkpoints sind rhetorisch, sonst kosten sie rund 2 min (Presenter).
| 12 | arrived | Wiki oder RAG? Vier Fragen | 2 | G5 | Können Sie die vier Fragen für Ihr Team beantworten? |

#### Slide 1: Das KISZ-Wiki: Wissen verdichten statt suchen

- Roam beat: destination
- Main idea: Thema und Antwort stehen auf der ersten Folie.
- Sub-ideas: Untertitel nennt die These; Sprecher und Anlass.
- On-slide text:
  - Titel: Das KISZ-Wiki: Wissen verdichten statt suchen
  - Untertitel: Warum wir für das Wissen unseres Teams kein RAG nutzen
  - Hanno Müller, KI-Servicezentrum Berlin-Brandenburg
  - RAG-Forum, 2. November 2026
- Speaker note: Ich erzähle Ihnen heute in einem RAG-Forum, warum wir für das Wissen unseres eigenen Teams kein RAG nutzen, sondern ein Wiki, das eine KI schreibt und wir freigeben. Am Ende kennen Sie vier Fragen, mit denen Sie das für Ihr eigenes Team entscheiden können.
- Visual: Titellayout des AISC-Templates (Light).
- Checkpoint: none

#### Slide 2: Sechs Engineers, viele Aufgaben

- Roam beat: destination
- Main idea: Neben der Kernarbeit liegen viele Aufgaben, die alle Informationen aus dem Team brauchen.
- Sub-ideas: Kernaufgabe zuerst; die Folie füllt sich in zwei Schüben; am Ende steht die Frage.
- On-slide text (Klickfolge):
  - Start: sechs runde Porträts in einer Reihe (Hanno, Felix, Mario, Paras, David, Jill), Titel "Sechs Engineers am KISZ"
  - Klick 1: PoCs bauen, Blueprints ableiten
  - Klick 2: Protokolle schreiben; Veranstaltungen organisieren; Workshops geben
  - Klick 3: Lehre; Vorträge auf Einladung; Beratung in Sprechstunden
  - Klick 4: Wie schaffen wir das nebenbei, während wir Engineering machen?
- Speaker note: Das sind die sechs Engineers des KI-Servicezentrums. [Klick] Unsere wichtigste Aufgabe ist, mit Partnern Prototypen zu bauen, sogenannte Proofs of Concept, und daraus Blueprints abzuleiten, also Vorlagen, die andere wiederverwenden können. [Klick] Daneben schreiben wir Protokolle, organisieren Veranstaltungen wie dieses Forum und geben Workshops. [Klick] Wir lehren, halten Vorträge auf Einladung und beraten in Sprechstunden. Jede dieser Aufgaben braucht Informationen, die irgendwo im Team schon entstanden sind: ein Termin, ein Raum, wer welchen Workshop schon gegeben hat. Oft sind sie veraltet, wenn man sie findet. [Klick] Die Frage ist also: Wie schaffen wir das nebenbei, während wir eigentlich Engineering machen?
- Visual: sechs runde Porträts aus `components/S1.1-input/assets/team/` in einer Reihe, Vorname darunter; die Aufgaben erscheinen als graue Etiketten über den Porträts, bis die Folie bewusst überladen wirkt; die Frage erscheint zuletzt in HPI-Rot über allem.
- Checkpoint: Kennen Sie das aus Ihrem Team? (rhetorisch, Blick in den Raum)

#### Slide 3: Ein System, das uns kennt

- Roam beat: route
- Main idea: Die Lösung ist ein System, das uns kennt; heute geht es nur um sein Rückgrat, das Wiki.
- Sub-ideas: was das System weiß, mit einem konkreten Beispiel; Rückgrat heißt Wiki; Ablauf des Abends.
- On-slide text:
  - Weiß, wie wir arbeiten
  - Weiß, wer wann welche Information braucht
  - Weiß, wann diese Information entsteht
  - Heute: sein Rückgrat, unser Wiki
  - 20 min Input, 15 min Live-Demo, 30 min Gespräche in Dreiergruppen
- Speaker note: Unsere Antwort ist ein System, das uns kennt. Teile davon sind kleine KI-Assistenten, zum Beispiel einer, der aus dem Transkript einer Sprechstunde ein Protokoll schreibt. Alle greifen auf dasselbe Wissen zu: unser Wiki. Das ganze System kann ich in 20 Minuten nicht zeigen, nur dieses Rückgrat. Danach zeige ich das Wiki 15 Minuten live, und dann sprechen Sie in drei kurzen Runden in Dreiergruppen über die Wissensablage Ihres eigenen Teams. Zuerst aber: Ein Rückgrat muss jemand aktuell halten.
- Visual: Die Aufgaben von Folie 2 liegen als Ring um einen Kasten "Wiki" in der Mitte, jede mit einer dünnen Linie zum Kasten.
- Checkpoint: Ist klar, wohin wir gehen?

#### Slide 4: Wie pflegen wir das Rückgrat ohne Overhead?

- Roam beat: route
- Main idea: Drei Wege, ein Rückgrat aktuell zu halten: von Hand, gar nicht (RAG) oder durch eine KI (LLM-Wiki).
- Sub-ideas: Wiki von Hand kostet Zeit und veraltet; RAG pflegt nichts und sucht bei jeder Frage; LLM-Wiki: KI verdichtet und pflegt, Menschen geben frei.
- On-slide text:
  - Spalte 1, Wiki von Hand: Menschen schreiben Seiten; kostet Zeit; Seiten veralten
  - Spalte 2, RAG: niemand pflegt; bei jeder Frage passende Ausschnitte aus den Rohdokumenten suchen; alte und neue Fassungen stehen nebeneinander
  - Spalte 3, LLM-Wiki: KI liest jede Quelle einmal; schreibt und pflegt Seiten; Menschen geben frei
  - Handzeichen: Wer hat schon über RAG für die eigene Teamablage nachgedacht?
- Speaker note: Overhead heißt hier: Arbeit, die niemand neben dem Engineering machen will. Die klassische Antwort ist ein Wiki, das Menschen von Hand pflegen, etwa in Confluence. Das kostet genau die Zeit, die wir nicht haben, und die Seiten veralten. In einem RAG-Forum liegt eine zweite Antwort nahe: gar nicht pflegen. RAG lässt die Dokumente, wie sie sind, und sucht bei jeder Frage die passenden Ausschnitte heraus. Liegen alte und neue Fassungen in der Ablage, findet RAG beide. Wer von Ihnen hat schon über so ein System für die Ablage des eigenen Teams nachgedacht? [Handzeichen] Für Sie gibt es am Ende vier Fragen, mit denen Sie das entscheiden, und in der zweiten Gruppenrunde wenden Sie sie an. Wir haben einen dritten Weg gewählt, ein LLM-Wiki. Eine KI liest jede Quelle einmal und verdichtet sie: Aus vielen Dokumenten wird eine kurze Seite pro Person, Projekt oder Veranstaltung. Die KI hält diese Seiten aktuell, und Menschen geben jede Änderung frei. Warum nicht RAG, sage ich Ihnen am Ende; erst zeige ich, wie das Wiki funktioniert.
- Visual: drei Spalten gleicher Bauart in Grau; Spalte 3 mit feinem Akzent in HPI-Rot.
- Checkpoint: Handzeichen (rund 0,5 min)

#### Slide 5: Das KISZ-Wiki: drei Schichten

- Roam beat: first step
- Main idea: Das Wiki hat drei Schichten, und jede hat eine eigene Antwort auf "wer schreibt, wer gibt frei".
- Sub-ideas: Quellen werden nur gelesen; Seiten schreibt die KI, Menschen geben frei und lesen sie selbst; Regeln schreibt das Team.
- On-slide text:
  - Regeln: eine Datei; wie Seiten aussehen, was nie hineindarf; schreibt und gibt frei: das Team
  - Seiten: rund 140 Textseiten zu Team, Projekten, Workshops, Veranstaltungen, Abläufen; schreibt die KI, geben Menschen frei
  - Quellen: GitHub, Eventbrite, Homepage, Nextcloud, Gespräche; liest die KI, verändert sie nie
  - Fußzeile: Idee: Andrej Karpathy, "LLM Wiki" (2026)
- Speaker note: Die Idee stammt von Andrej Karpathy, Mitgründer von OpenAI, der sie im April 2026 als LLM-Wiki beschrieben hat. Unser Wiki hat drei Schichten. Unten liegen die Quellen: Code-Ablagen auf GitHub, Veranstaltungen auf Eventbrite, unsere Homepage, Dokumente in Nextcloud und Gespräche mit Kolleg:innen. Die KI liest sie, verändert sie aber nie. In der Mitte liegen rund 140 Seiten in einfachem Text, eine Seite pro Person, Projekt, Workshop, Veranstaltung und Ablauf. Die KI ist bei uns Claude Code: ein Assistent wie ChatGPT, der aber Dateien lesen und schreiben darf. Diese Seiten schreibt die KI, Menschen geben sie frei, und Menschen lesen sie auch selbst, im Browser wie jede andere Dokumentation. Oben liegt eine einzige Datei mit Regeln: wie eine Seite aussieht, woher jede Aussage stammen muss und was nie hineindarf, zum Beispiel Daten von Teilnehmenden. Diese Regeln schreibt das Team. Kurze Kontrolle: Wer schreibt die Seiten, und wer gibt sie frei?
- Visual: drei gestapelte Bänder (figures-bw), rechts je eine Spalte "schreibt" und "gibt frei"; das Band "Seiten" ist das breiteste.
- Checkpoint: Wer schreibt die Seiten, und wer gibt sie frei? (Antwort aus dem Raum: die KI schreibt, Menschen geben frei)

#### Slide 6: So beantwortet die KI eine Frage

- Roam beat: next steps
- Main idea: Die KI liest zuerst das ganze Inhaltsverzeichnis und wählt dann selbst die passende Seite.
- Sub-ideas: echte Zeile aus dem Inhaltsverzeichnis; eine ganze Seite; Unterschied zu RAG in einem Satz.
- On-slide text:
  - Frage: Wann und wo ist das nächste RAG-Forum?
  - 1. Ganzes Inhaltsverzeichnis lesen: eine Zeile pro Seite
  - 2. Selbst die passende Seite wählen und ganz lesen
  - 3. Antworten: 2. November 2026, 17:30 Uhr, D-Space
  - Ausschnitt (Code-Kasten): `events/community/2026-11-02-rag-forum.md: RAG Forum in German on 2 November 2026 in the D-Space; ...`
- Speaker note: Fragt jemand das Wiki, liest die KI zuerst das ganze Inhaltsverzeichnis, eine Zeile pro Seite. Für die Frage "Wann und wo ist das nächste RAG-Forum?" findet sie dort diese Zeile, öffnet die eine Seite und antwortet: heute, 17:30 Uhr, im D-Space. Der Unterschied zu RAG: Bei RAG wählt eine Suche Ausschnitte aus, bevor das Modell irgendetwas sieht. Hier sieht das Modell das ganze Inhaltsverzeichnis und entscheidet selbst, welche ganze, freigegebene Seite es liest. Die Antwort stimmt aber nur, solange die Seite stimmt.
- Visual: Fluss von links nach rechts: Frage, Inhaltsverzeichnis mit hervorgehobener Zeile, eine Seite, Antwort; echter Text in Monospace.
- Checkpoint: Wer hat entschieden, welche Seite gelesen wird? (Antwort: die KI selbst, nach dem ganzen Inhaltsverzeichnis; bei RAG eine Suche vorab)

#### Slide 7: Wie Neues hineinkommt

- Roam beat: next steps
- Main idea: Der Pflegekreislauf: Ein Mensch gibt eine Quelle, die KI schreibt, ein Mensch gibt frei.
- Sub-ideas: wer die Quelle bringt; Entwurf mit offenen Fragen statt Raten; Änderungsvorschlag mit Freigabe; die menschliche Arbeit als Zahl.
- On-slide text:
  - Jemand gibt der KI eine Quelle: Link, Text, "ins Wiki"
  - KI zeigt, welche Seiten sich ändern, fragt einmal nach
  - KI schreibt den Entwurf; Unbekanntes wird offene Frage mit Namen
  - Änderungsvorschlag: ein Mensch gibt frei
  - Kasten: Unsere Arbeit: Quellen geben und freigeben, nicht schreiben
- Speaker note: So kommt Neues ins Wiki. Jemand aus dem Team gibt der KI eine Quelle, zum Beispiel den Link zu einer neuen Veranstaltung auf Eventbrite, oder sagt nach einem Gespräch einfach "ins Wiki". Die KI liest die Quelle, zeigt, welche Seiten sich ändern würden, und fragt einmal nach, ob sie weitermachen soll. Dann schreibt sie den Entwurf. Was die Quelle nicht hergibt, rät sie nicht: Sie schreibt eine offene Frage mit dem Namen der Person, die es weiß. Auch Widersprüche entscheidet sie nicht selbst. Beim ersten RAG-Forum nannte Eventbrite den 15. Juni, unser Ordner in Nextcloud den 15. Mai; die KI hat den Widerspruch notiert, statt ein Datum zu wählen, und ich habe den Ordner korrigiert. Jede Änderung ist ein Änderungsvorschlag, in der Softwareentwicklung heißt das Merge Request. Erst wenn ein Mensch freigibt, steht die Änderung im Wiki. Unsere Arbeit ist also Quellen geben und freigeben, nicht schreiben.
- Visual: Kreislauf mit vier Stationen (figures-bw), grau; die beiden menschlichen Stationen ("gibt Quelle", "gibt frei") in HPI-Rot.
- Checkpoint: Welcher Schritt bleibt bei uns Menschen? (Antwort: Quellen geben und freigeben)

#### Slide 8: Wie das Wiki aktuell bleibt

- Roam beat: next steps
- Main idea: Die KI findet Widersprüche und Lücken, ein Mensch entscheidet.
- Sub-ideas: Wartungssitzung alle zwei Wochen; ein Befund pro Frage mit Beleg; echter Befund.
- On-slide text:
  - Alle zwei Wochen: KI bietet eine Wartungssitzung an
  - KI sucht Widersprüche zwischen Seiten, Lücken, doppelten Text
  - Ein Befund pro Frage, mit Beleg; ein Mensch entscheidet
  - Befundkarte: Durchsicht am 9. Oktober. Seite A (Workshop-Abläufe): Vorbereitung beginnt, sobald das Material fertig ist. Seite B (Workshop-Vorbereitung): Das Material muss nicht fertig sein. Entscheidung: offen
- Speaker note: Auch Wiki-Seiten veralten oder widersprechen sich. Alle zwei Wochen bietet die KI, wenn jemand aus dem Team mit ihr zu arbeiten beginnt, eine Wartungssitzung an. Sie sucht Widersprüche zwischen Seiten, Lücken und doppelten Text und legt jeden Befund einzeln vor, mit der Stelle, an der sie ihn gefunden hat. Entscheiden muss ein Mensch. Ein Befund aus der ersten Durchsicht am 9. Oktober: Eine Seite sagt, die Vorbereitung eines Workshops beginnt, sobald das Material fertig ist; eine andere sagt, das Material muss dafür nicht fertig sein. Welche stimmt, weiß nur das Team. Auch das ist Freigabe: Die KI schlägt die Korrektur vor, ein Mensch entscheidet und gibt frei.
- Visual: die Befundkarte als Bild: Datum der Durchsicht, die beiden Stellen mit sprechendem Seitennamen (keine Dateipfade), Feld "Entscheidung" leer.
- Checkpoint: Wer entscheidet, was stimmt? (Antwort: ein Mensch)

#### Slide 9: Was das Wiki auslöst

- Roam beat: next steps
- Main idea: Weil jede Änderung durch dieselbe Stelle läuft, stößt das Wiki Abläufe an, manche automatisch, manche auf Zuruf.
- Sub-ideas: Slack-Meldung automatisch; To-do-Erinnerung und Repository-Vorschlag beim Arbeitsbeginn; Anfrage an die Öffentlichkeitsarbeit auf Zuruf; dieser Vortrag.
- On-slide text:
  - Jede freigegebene Änderung: Zusammenfassung in Slack (automatisch)
  - Offene Fragen werden To-dos mit Namen; einmal im Monat Erinnerung (beim Arbeitsbeginn)
  - Alle zwei Wochen: KI schlägt Seiten für neue Code-Ablagen vor (beim Arbeitsbeginn)
  - Auf Zuruf: Anfrage an die Öffentlichkeitsarbeit, mit Angaben aus dem Wiki
- Speaker note: Weil jede Änderung als Änderungsvorschlag durch dieselbe Stelle läuft, kann das Wiki auch etwas anstoßen. Nach jeder freigegebenen Änderung fasst eine KI automatisch zusammen, was sich geändert hat, und schreibt es in einen Slack-Kanal des Teams. Jede offene Frage aus dem Entwurf wird ein To-do mit Namen, und einmal im Monat erinnert die KI jede Person an ihre To-dos, wenn sie mit ihr zu arbeiten beginnt. Wer eine offene Frage beantwortet, gibt damit wieder eine Quelle. Alle zwei Wochen schlägt sie Seiten für neue Code-Ablagen auf GitHub vor. Und auf Zuruf schreibt sie mit den Angaben aus dem Wiki die Anfrage an unsere Öffentlichkeitsarbeit, so wie für dieses Forum. Auch diesen Vortrag habe ich mit dem Wiki geplant: Datum, Raum und frühere Teilnehmerzahlen kamen von dort.
- Visual: vier Zeilen "Auslöser, dann Aktion" mit Pfeil, grau; die Markierung "automatisch", "beim Arbeitsbeginn" oder "auf Zuruf" rechts in kleiner Schrift; keine Icons.
- Checkpoint: rhetorisch ("Welchen davon gäbe es bei Ihnen auch? Darüber sprechen Sie in Runde 3.")

#### Slide 10: Warum kein RAG?

- Roam beat: almost there
- Main idea: Das Inhaltsverzeichnis passt in eine einzige Anfrage, sogar an ein selbst gehostetes Modell; die KI muss nicht suchen.
- Sub-ideas: Kontextfenster erklärt (der Grund, warum RAG sucht); die Zahl; wir nutzen Claude, ein lokales Modell würde reichen.
- On-slide text:
  - Sprachmodell liest pro Anfrage begrenzt viel Text: das Kontextfenster
  - Inhaltsverzeichnis: rund 8.000 Tokens
  - Passt sogar in gpt-oss-120b, am HPI selbst gehostet (128.000 Tokens): rund 6 %
  - Keine Suche: KI liest freigegebene Seiten mit aktuellem Stand
  - Fußnote: Wir arbeiten mit Claude; zum Vergleich ein Modell, das wir selbst hosten
- Speaker note: Zurück zur Frage vom Anfang: Warum kein RAG? Ein Sprachmodell liest pro Anfrage nur eine begrenzte Menge Text, das sogenannte Kontextfenster. RAG sucht Ausschnitte heraus, weil die Dokumente nicht ganz hineinpassen. Unser Inhaltsverzeichnis umfasst rund 8.000 Tokens, also Wortstücke. Wir arbeiten mit Claude, einem Modell in der Cloud; aber selbst gpt-oss-120b, ein offenes Modell, das wir am HPI selbst betreiben, liest 128.000 Tokens pro Anfrage. Das zählt für alle, die ihre Daten nicht in eine Cloud geben dürfen. Das Inhaltsverzeichnis belegt davon rund 6 Prozent; die KI muss nicht suchen, sie liest. Dazu kommt, was Sie gerade gesehen haben: Die Seiten sind freigegeben, zeigen den aktuellen Stand, und Widersprüche fallen auf, statt im Suchergebnis unterzugehen.
- Visual: waagerechter Balken (figures-bw): Kontextfenster 128.000 als grauer Rahmen, Inhaltsverzeichnis 8.000 als gefüllter Teil in HPI-Rot.
- Checkpoint: Was müsste passieren, damit das nicht mehr reicht?

#### Slide 11: Wo RAG gewinnt

- Roam beat: almost there
- Main idea: RAG skaliert; das Wiki stößt an zwei Grenzen: die Größe des Inhaltsverzeichnisses und die Zahl der Menschen, die freigeben.
- Sub-ideas: Inhaltsverzeichnis wächst mit jeder Seite; große Kontextfenster lassen sich lokal kaum betreiben; eine Handvoll Freigebender reicht nicht für täglichen Zufluss.
- On-slide text:
  - Heute: rund 140 Seiten, rund 8.000 Tokens
  - 1.400 Seiten: rund 80.000 Tokens, kaum Platz für Seite und Antwort
  - 2.800 Seiten: passt nicht mehr; nötig wären riesige Kontextfenster, lokal kaum zu betreiben
  - Täglich viel Neues: eine Handvoll Menschen gibt nicht mehr alles frei
  - RAG liest nur passende Ausschnitte und wächst mit
- Speaker note: Genau hier gewinnt RAG. Jede Seite kostet im Inhaltsverzeichnis rund 60 Tokens. Bei 1.400 Seiten, zehnmal so viel wie heute, belegt es rund 80.000 Tokens, knapp zwei Drittel des Fensters, und für die Seite und die Antwort bleibt kaum Platz. Soll das Inhaltsverzeichnis höchstens das halbe Fenster belegen, liegt die Grenze rechnerisch bei rund 1.000 Seiten. Bei 2.800 Seiten passt es gar nicht mehr hinein. Dann braucht das Wiki Modelle mit riesigem Kontextfenster, und die lassen sich lokal kaum betreiben. Die zweite Grenze sind wir selbst: Kommt täglich viel Neues hinzu, kann eine Handvoll Menschen nicht mehr jede Änderung freigeben. RAG liest dagegen immer nur die passenden Ausschnitte und braucht keine Freigabe pro Dokument; es wächst mit.
- Visual: derselbe Balken wie Folie 10, beschriftet nach Seiten: 140 Seiten (rund 8.000), 1.400 Seiten (rund 80.000), 2.800 Seiten (rund 160.000, ragt über den Rahmen von 128.000 hinaus); gestrichelte Linie beim halben Fenster mit "Grenze: rund 1.000 Seiten".
- Checkpoint: Wo steht Ihr Team: eher bei 140 oder bei 2.800 Seiten? (rhetorisch)

#### Slide 12: Wiki oder RAG? Vier Fragen

- Roam beat: arrived
- Main idea: Vier Fragen in zwei Paaren entscheiden, ob ein Wiki, RAG oder beides passt.
- Sub-ideas: Paar "Passt es?"; Paar "Schaffen wir es?"; Faustregel mit Beispiel für "beides"; Kernbotschaft; Take-away; Übergabe an die Demo.
- On-slide text (Tabelle):

  | | Wiki | RAG |
  |---|---|---|
  | Passt es? Umfang (wie viele Seiten: Personen, Projekte, Termine, Abläufe) gegen Hosting (Fenster des Modells, das Sie nutzen dürfen) | einige hundert Seiten (Grenze rechnerisch bei rund 1.000) | mehr als rund 1.000 Seiten |
  | Schaffen wir es? Zufluss (Neues pro Woche) gegen Prüfende (Menschen, die freigeben) | eine Handvoll schafft es nebenbei | täglich mehr, als sie freigeben können |

  - Faustregel: Beide Paare gehen auf: Wiki. Eins geht nicht auf: RAG, oder ein Wiki für den kleinen Kern und RAG für die Masse (z. B. Projektseiten als Wiki, das Archiv aller Protokolle über RAG).
  - QR-Code und Link zum README im Session-Ordner
- Speaker note: Ob das für Ihr Team gilt, entscheiden vier Fragen, die paarweise zusammengehören. Das erste Paar fragt, ob es passt: Wie viele Seiten würde Ihr Wiki haben, eine pro Person, Projekt, Termin oder Ablauf, und welches Modell dürfen Sie nutzen? Mit einem selbst gehosteten Modell wie gpt-oss-120b reicht es für einige hundert Seiten. Das zweite Paar fragt, ob Sie es schaffen: Wie viel Neues kommt pro Woche hinzu, und wie viele Menschen geben frei? Gehen beide Paare auf, nehmen Sie das Wiki. Geht eins nicht auf, nehmen Sie RAG, oder ein Wiki für den kleinen Kern und RAG für die Masse. Kurz gesagt: RAG liest bei jeder Frage die Rohdokumente neu; ein Wiki verdichtet sie einmal, Menschen geben frei, und die KI hält es aktuell. Das Wiki gewinnt, solange es bei einigen hundert Seiten bleibt und langsam wächst. Die vier Fragen brauchen Sie gleich in den Gruppenrunden; der QR-Code führt zu einer Seite mit allem zum Nachlesen. Vorher zeige ich Ihnen das Wiki live.
- Visual: Tabelle im AISC-Stil, Spalte "Wiki" mit feinem HPI-Rot-Akzent; QR-Code unten rechts.
- Checkpoint: Können Sie die vier Fragen für Ihr Team beantworten? (Antwort folgt in S1.3)

### Appendix slides

| # | Title | On-slide text | Speaker note | Visual |
|---|---|---|---|---|
| X1 | Was ein eigenes Wiki braucht | Git-Repository mit Änderungsvorschlägen (bei uns GitLab); KI-Assistent mit Dateizugriff (bei uns Claude Code); eine Regeldatei; ein Prüfskript für Pflichtfelder und Datenschutz; Quellen bleiben, wo sie sind (Nextcloud, Confluence) | Für Rückfragen in S1.2. | Liste |
| X2 | Freigabe und Bestätigung | Freigabe: ein Mensch stimmt einer Änderung zu; Bestätigung: die Person, um deren Seite es geht, bestätigt den Inhalt (Stempel mit Datum, Name, Prüfsumme); Status: bestätigt, nach Bestätigung geändert, unbestätigt; Vertrauen: Punkte für Quellen und Bestätigung, Abzug für Alter und offene Fragen | Freigeben und bestätigen sind zwei Dinge: Eine Änderung kann freigegeben sein, ohne dass die zuständige Person den Inhalt bestätigt hat. Die Prüfsumme ist ein Fingerabdruck des Seitentexts; ändert sich ein Zeichen, passt sie nicht mehr. Vertrauen wird berechnet, nie von Hand gesetzt. | kleine Tabelle |
| X3 | Automatische Prüfungen bei jedem Änderungsvorschlag | Inhaltsverzeichnis aktuell; Pflichtfelder vorhanden; Links lösen auf; keine Mailadressen oder Telefonnummern; Stempel nur von der Person, die bestätigt hat | Diese Prüfungen laufen in der CI von GitLab (`wiki.py index --check`, `people --check`, `lint`, `privacy`, `reviewers`). | Liste |
| X4 | Wer darf was ändern | Frei: neue Seiten, Themenseiten; nach Ja: Änderungen an bestehenden Seiten und Personenseiten; nur auf eigenes Wort: Arbeitsweise und Ansprache auf der eigenen Personenseite | Die Stufen stehen in der Regeldatei; jede Änderung landet trotzdem nur über einen freigegebenen Änderungsvorschlag im Wiki. | Tabelle in drei Zeilen |
| X5 | Was nie ins Wiki kommt | Daten von Teilnehmenden; private Mailadressen und Telefonnummern; Bewertungen von Kolleg:innen; als vertraulich markierte Details; alles, was eine Person aus einer Sprechstunde erkennbar macht | Ein Prüfskript lässt jeden Änderungsvorschlag scheitern, der Mailadressen oder Telefonnummern enthält; der Rest ist Regel für die KI und Prüfpunkt für Menschen. | Liste |
| X6 | Zum Nachlesen | Andrej Karpathy, LLM Wiki: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f; Überblick: https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide; README dieser Sitzung mit den vier Fragen und den Folien; Verweis auf die Wiki-Vorlage aus Issue #2 (fügt Hanno Müller ein, sobald veröffentlicht) | none | Links und QR-Code zum README |
| X7 | Umsetzungen aus der Community | Tabelle mit Projekt, Beschreibung, Link: llmwiki (Dokumente hochladen, Claude über MCP verbinden, Wiki schreiben lassen), github.com/lucasastorian/llmwiki; obsidian-wiki (Rahmen für KI-Agenten, die Obsidian-Wikis nach Karpathys Muster bauen), github.com/Ar9av/obsidian-wiki; second-brain (von einem LLM gepflegte persönliche Wissensbasis für Obsidian), github.com/NicholasSpisak/second-brain; llm-wiki-compiler (verdichtet Markdown-Dateien zu Wikis nach Themen), github.com/ussumant/llm-wiki-compiler; CacheZero (das Muster als ein npm-Paket), news.ycombinator.com/item?id=47667723; wiki-skills (Claude-Code-Skills für das Muster), github.com/kfchou/wiki-skills; LLM Wiki v2 (erweitertes Muster mit Gedächtnis-Lebenszyklus und Vertrauenswerten), gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2; Fußzeile: Quelle Starmorph, "How to Build Karpathy's LLM Wiki", 2026-04-09 | Für Rückfragen: Unser Wiki ist eine eigene Umsetzung mit Claude Code, GitLab und einer Regeldatei; LLM Wiki v2 hat wie wir Vertrauenswerte. | Tabelle, kleine Schrift |

## 4. Internal bridges

| From | To | The one new thought |
|---|---|---|
| Entry state | 1 | Ein RAG-Forum, in dem jemand erklärt, warum er kein RAG nutzt. |
| 1 | 2 | Wer "wir" ist: sechs Engineers mit einer Kernaufgabe und vielen Aufgaben daneben. |
| 2 | 3 | Diese Aufgaben brauchen ein System, das uns kennt; heute nur sein Rückgrat, das Wiki. |
| 3 | 4 | Ein Rückgrat darf keine Arbeit machen; drei Wege, es aktuell zu halten. |
| 4 | 5 | Der dritte Weg im Aufbau: drei Schichten mit klaren Rollen. |
| 5 | 6 | Wie die Seiten gelesen werden: erst das ganze Inhaltsverzeichnis, dann eine ganze Seite. |
| 6 | 7 | Das trägt nur, solange die Seiten stimmen; also: wie Neues hineinkommt. |
| 7 | 8 | Neues kommt über Quellen; Bestehendes veraltet trotzdem, also sucht die KI regelmäßig nach Widersprüchen. |
| 8 | 9 | Weil jede Änderung durch dieselbe Stelle läuft, kann das Wiki Abläufe anstoßen. |
| 9 | 10 | Zurück zur Frage von Folie 4: Das Kontextfenster erklärt, warum wir nicht suchen müssen. |
| 10 | 11 | Dieselbe Zahl, hochgerechnet: wo das Wiki an Grenzen stößt und RAG skaliert. |
| 11 | 12 | Aus den zwei Grenzen werden zwei Paare von Fragen für das eigene Team. |
| 12 | Exit state | Übergabe an die Live-Demo: das Wiki bei der Arbeit. |

## 5. Parking lot

| Item | Destination | Reason |
|---|---|---|
| Konfidenzformel im Detail (ein Punkt pro Quelle bis zwei, Bestätigung bis zwei, Abzüge für Alter und drei oder mehr offene Fragen) | appendix X2 | Katrin reicht "freigegeben oder nicht" |
| Prüfstempel (bestätigt, nach Bestätigung geändert, unbestätigt) | appendix X2 | Audience-Befund: auf Folie 8 verwechselbar mit der Freigabe |
| CI-Befehle `wiki.py` | appendix X3, Sprechernotiz | Mechanik |
| Seitentypen (Zentrum, Team, Person, Ablauf, Projekt, Workshop, Präsentation, Veranstaltung, Thema, Vorlage, To-dos) | drop; Folie 5 nennt die wichtigsten | Liste ohne Erkenntnis |
| Rohschnappschüsse in `raw/` (Textkopien von Quellen ohne persönliche Daten) | Q&A in S1.2 | Detail zur Quellenschicht |
| Ganzes Wiki rund 174.000 Tokens, passt schon heute nicht in 128.000 | nur auf Nachfrage zu Folie 10 | Begründet, warum das Inhaltsverzeichnis zuerst gelesen wird; zweiter Gedanke auf Folie 10 wäre zu viel |
| Faustwert "rund 60 Tokens pro Zeile, also rechnerisch rund 1.000 Seiten bei 128.000 Tokens" (8.030 Tokens für 140 Zeilen; halbes Fenster für das Inhaltsverzeichnis, Rest für Seiten und Antwort); Community-Berichte: Grenzen schon ab 100 bis 200 Seiten (Starmorph, unverified) | Sprechernotiz Folie 11 und 12 | Herleitung, nicht Geschichte (inferred) |
| Sprechstunden-Protokolle, Workshop-Reporting, Workshop-Planung als weitere Teile des Systems | Networking | Folie 3 nennt zwei Beispiele und grenzt ab |
| Werkzeugkosten von Claude Code | Q&A in S1.2 | Katrins Frage nach Kosten; Zahl liegt nicht vor |
| Weitere Befunde der Durchsicht vom 2026-10-09 (`tmp/261009-wiki-review/findings.md` im kisz-marketplace; 52 insgesamt) | Q&A in S1.2 | Belege für Folie 8; die Zahl 52 lädt zur Frage nach der Arbeitszeit ein, die es nicht gibt |
| Community-Aussage "Navigation über das Inhaltsverzeichnis wird ab 100 bis 200 Seiten schwieriger" (Starmorph-Überblick, eigene Aussage des Artikels, nicht Erfahrungsberichte) | Q&A in S1.2 | Widersprach auf Folie 11 der Rechnung und ließ das KISZ-Wiki schon an der Grenze erscheinen |
| Das Wiki ist auf Englisch geschrieben (Zeile auf Folie 6) | Q&A in S1.2 | Nebensatz, schwächte die Brücke zu Folie 7 |
