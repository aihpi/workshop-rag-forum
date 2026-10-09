# Das KISZ-Wiki: Wissen verdichten statt suchen

## 1. Header

- Level: workshop
- Format(s): slides (Input), live demonstration mit Q&A, Gruppenrunden
- Language: de (Sie, wie das Eventbrite-Listing)
- Slot: 90 min, Montag 2026-11-02, 17:30 bis 19:00; davon geplant 67 min (S1.1 bis S1.3), danach Networking
- Setting: D-Space am HPI, vor Ort; rund 20 Teilnehmende erwartet (frühere Ausgaben hatten 50 bis 70 Anmeldungen, aber viele kamen nicht); Teilnehmende brauchen kein Gerät
- Notebook flavour: none
- Template: ~/Presentations/Template/202608_AISC-Template_Light.pptx
- Quiz: none
- Inspiration: `03_workshop/260615-turbovec/` (turbovec_intro, 8 Folien, gleiches Template, im Repository als PDF); kisz-context `presentations/2026-04-23-triblecore-wissensmanagement.md` (lokales RAG für Wissensmanagement); Karpathys LLM-Wiki (Post auf X am 2026-04-02, danach ein "idea file" als GitHub-Gist; drei Schichten Rohquellen, Wiki, Schema; Operationen ingest, query, lint; Gist https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f); Überblick mit Umsetzungen aus der Community: https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide (2026-04-09, abgerufen 2026-10-09); Quellen zum Wiki: kisz-marketplace `plugins/kisz-knowledge/skills/kisz-context/schema.md`, `plugins/kisz-organize/skills/kisz-wiki/SKILL.md`, `plugins/kisz-organize/skills/wiki-maintenance/SKILL.md`, `ci/wiki-notify.sh`, `plugins/kisz-organize/hooks/hooks.json`
- Status log:
  - 2026-10-09 interview rounds 1 to 3 (core claim, learner, results, goals, overview) with Hanno Müller
  - 2026-10-09 overview confirmed by Hanno Müller ("Confirm"); level changed from single to workshop after the session shape (Input, Demo, Gruppenrunden) was added
  - 2026-10-09 audience, meta level, plan review: complete
  - 2026-10-09 presenter, meta level, full: complete
  - 2026-10-09 review findings folded in: Faustregel für die vier Fragen, Pflegeaufwand im Transfer Value und in G3, Begriffe (Merge Request, PR, "wer bürgt" wird "Freigabe"), Exit state S1.3, Ersatzbeispiel für D, Take-away, Zeitschätzung; open decisions listed in section 8
  - 2026-10-09 adjustments by Hanno Müller: rund 20 Teilnehmende statt 50 bis 70; RAG gewinnt allein durch Skalierung (Zahl der Dokumente, Kontextfenster lokal gehosteter Modelle, täglicher Zufluss gegen eine Handvoll Prüfender), kein Rahmen "RAG für Partnerdokumente"; vier Fragen jetzt Umfang, Hosting, Zufluss, Prüfende
  - 2026-10-09 meta plan confirmed by Hanno Müller with these adjustments ("Include adjustments and then continue"); open decisions 1 (Abschluss 2 min) and 4 (README als Take-away) taken as recommended, 2 and 3 move to S1.2 and S1.1 planning
  - 2026-10-09 from the S1.1 review: Entscheidungscheck in zwei Paaren (Umfang gegen Hosting, Zufluss gegen Prüfende), Umfang in Seiten statt Dokumenten, Faustwert 1.000 Seiten; Satz zur Vorbereitung in der Vorab-Kommunikation; Seitenzahl rund 140; confirmed by Hanno Müller with "Start creating the slides"
  - 2026-10-09 change C1 confirmed by Hanno Müller ("The slides should work without this information"): no numbers for work time or changes per week; S1.1 interface version 2
  - 2026-10-09 repository moved to ~/Workshops/workshop-rag-forum; first commit on branch feature/261102-llm-wiki
  - 2026-10-09 note by Hanno Müller: share the wiki maintenance skills from kisz-marketplace after a /security-review; Hanno adds the reference to the slides himself (section 8)

## 2. Learner

Katrin leitet Projekte an einem HPI-Fachgebiet. Sie nutzt ChatGPT täglich, kennt RAG aus Vorträgen und aus einem Prototyp ihres Teams, hat aber selbst nie eine Pipeline gebaut. Das Wissen ihres Teams liegt verteilt in Nextcloud, Confluence, Mails und Köpfen: Protokolle, Termine und Zuständigkeiten veralten, neue Kolleg:innen stellen dieselben Fragen. Sie kommt zum RAG-Forum, weil sie überlegt, ein RAG-System über die Teamablage zu legen, und will vorher wissen, ob das ihr Problem löst. Sie hört lieber Beispiele aus der Praxis als Architekturdiagramme und redet in Kleingruppen eher als im Plenum.

- Segment: Projektleitung
- Profile: Product- oder Projektrolle
- Technische Tiefe: mittel (kennt Begriffe, baut nicht selbst)
- "I aim to ...": entscheiden, wie mein Team sein Wissen für Menschen und KI-Assistenten auffindbar und aktuell hält.
- "I need ...": sehen, dass es im Alltag läuft, und wissen, was die Pflege kostet und wer sie macht.

Im Raum sitzen außerdem Kolleg:innen aus dem HPI und dem KI-Servicezentrum Berlin-Brandenburg (KISZ) sowie RAG-Entwickler:innen. Sie bekommen dieselbe Geschichte; technische Details (Prüfsumme, CI-Checks, Konfidenzformel) stehen im Anhang und kommen in Demo und Q&A dran.

## 3. Results

| Level | Result | Statement |
|---|---|---|
| Cognitive | Key Message | RAG liest bei jeder Frage die Rohdokumente neu; ein LLM-Wiki verdichtet sie einmal, Menschen prüfen das Ergebnis, und die KI hält es aktuell. Das Wiki gewinnt, solange wenige Dokumente langsam wachsen; RAG skaliert, wenn Umfang oder Zufluss zu groß werden. |
| Skill-based | Final Destination | In Gruppenrunde 2 ordnet jede Person die Wissenssammlung ihres eigenen Teams mit den vier Fragen und der Faustregel (unten) einer Lösung zu: Wiki, RAG oder beides. |
| Affective | Transfer Value | "Ich brauche ein Rückgrat, bei dem die KI schreibt und wir nur prüfen." Drei Momente erzeugen das, alle vor der letzten Folie von S1.1: die Folie mit dem Foto der Engineers, die sich Klick für Klick mit Aufgaben neben dem Engineering füllt (Katrin erkennt ihr Team wieder); in Abschnitt D der Kreislauf, in dem die einzigen menschlichen Schritte Quelle geben und Freigeben sind, nicht Schreiben; in Abschnitt F die Zahl, dass das Inhaltsverzeichnis des ganzen Wikis (rund 8.000 Tokens) in eine einzige Anfrage an ein selbst gehostetes Modell passt. S1.2 zeigt danach den Kreislauf am echten Wiki. |

### Entscheidungscheck (G5)

Die vier Fragen gehören paarweise zusammen; jedes Paar vergleicht eine Menge mit einer Grenze.

| Paar | Fragen | Spricht für Wiki | Spricht für RAG |
|---|---|---|---|
| Passt es? | Umfang: Wie viele Seiten hätte das Wiki, eine pro Person, Projekt, Termin oder Ablauf? Hosting: Welches Modell dürfen Sie nutzen, und wie viel liest es pro Anfrage? | Inhaltsverzeichnis passt bequem ins Fenster: bei 128.000 Tokens (gpt-oss-120b, selbst gehostet) bis rund 1.000 Seiten (KISZ: rund 140 Seiten, Inhaltsverzeichnis rund 8.000 Tokens) | tausende Seiten; das Inhaltsverzeichnis bräuchte ein Modell mit riesigem Kontextfenster, das sich lokal kaum betreiben lässt; RAG liest pro Frage nur die passenden Ausschnitte und wächst mit |
| Schaffen wir es? | Zufluss: Wie viel Neues kommt pro Woche hinzu? Prüfende: Wie viele Menschen geben Änderungen frei? | eine Handvoll Menschen schafft die Freigaben nebenbei | täglich mehr Neues, als eine Handvoll Menschen freigeben kann |

Die 1.000 Seiten sind eine Rechnung (rund 60 Tokens pro Zeile im Inhaltsverzeichnis, halbes Fenster). Erfahrungsberichte aus der Community sehen erste Grenzen der Navigation über das Inhaltsverzeichnis schon ab 100 bis 200 Seiten (Starmorph-Überblick, siehe Header; unverified); das KISZ-Wiki liegt mit rund 140 Seiten in diesem Bereich.

Faustregel: Gehen beide Paare auf, nehmen Sie das Wiki. Geht eins nicht auf, kostet die Pflege mehr, als sie bringt: RAG, oder ein Wiki für den kleinen, langsam wachsenden Kern und RAG für die große oder täglich wachsende Masse (z. B. Projektseiten als Wiki, das Archiv aller Protokolle über RAG).

Messwerte (2026-10-09, Tokenizer `o200k_base`, vor dem Talk neu messen): Inhaltsverzeichnis `index.md` rund 8.000 Tokens; ganzes Wiki (152 Dateien) rund 174.000 Tokens; Median einer Seite rund 770 Tokens. Das ganze Wiki passt also schon heute nicht in ein lokales Modell mit 128.000 Tokens, das Inhaltsverzeichnis belegt davon rund 6 %. Bei zehnmal so vielen Seiten belegt allein das Inhaltsverzeichnis rund 80.000 Tokens, knapp zwei Drittel (inferred, linear hochgerechnet).

## 4. Learning goals

| # | Kompetenz (Niveau) | Profile | Die Teilnehmenden können ... | Observable as | Served by |
|---|---|---|---|---|---|
| G1 | Verstehen & Einordnen (2) | all | den Unterschied zwischen RAG (bei jeder Frage in den Rohdokumenten suchen) und einem LLM-Wiki (Wissen einmal verdichten, prüfen lassen, aktuell halten) in eigenen Worten erklären | In einer Gruppenrunde beschreibt jemand den Unterschied ohne Folie | S1.1, S1.3 |
| G2 | Verstehen & Einordnen (1) | all | die drei Schichten des KISZ-Wikis (Quellen, Seiten, Regeln) benennen und sagen, wer jeweils schreibt und wer prüft | Antwort auf die Kontrollfrage "Wer schreibt, wer prüft?" in S1.1 nach Abschnitt B | S1.1, S1.2 |
| G3 | Verstehen & Einordnen (2) | all | den Pflegekreislauf (Quelle einlesen, Entwurf, Änderungsvorschlag mit Freigabe durch einen Menschen, Aufräumen) anhand eines Beispiels aus dem KISZ-Wiki beschreiben und sagen, welche Arbeit dabei bei Menschen bleibt | Fragen in Q&A zielen auf Details des Kreislaufs, nicht auf "Wie kommt das rein?" oder "Wer macht die Arbeit?" | S1.1, S1.2 |
| G4 | Verstehen & Einordnen (1) | all | zwei Abläufe benennen, die das Wiki über das Nachschlagen hinaus anstößt (z. B. Slack-Meldung bei Änderung, monatliche To-do-Erinnerung, Veranstaltungsanfrage an die Öffentlichkeitsarbeit) | In Gruppenrunde 3 nennt jemand einen Ablauf aus dem eigenen Team, der so laufen könnte | S1.1, S1.3 |
| G5 | Analysieren & Bewerten (2) | Projektrolle | für die Wissenssammlung des eigenen Teams anhand von vier Fragen (Umfang, Hosting, Zufluss, Prüfende) und der Faustregel einschätzen, ob ein Wiki, RAG oder beides passt | In Gruppenrunde 2 nennt jede Person ein Urteil und die Frage, die es entschieden hat; im Abschluss-Handzeichen (falls bestätigt) sichtbar für den Raum | S1.1 (führt ein), S1.3 (wendet an) |

## 5. Structure

### Workshop

| Session | Subject | Minutes | Goals served |
|---|---|---|---|
| S1 | RAG-Forum 2026-11-02: Input, Live-Demo, Gruppenrunden | 67 von 90 | G1 bis G5 |

#### S1 RAG-Forum 2026-11-02

| # | Component | Subject | Minutes | Goal | Anchor | Beginner variant | Advanced variant |
|---|---|---|---|---|---|---|---|
| S1.1 | Input (slides) | Das KISZ-Wiki als Rückgrat ohne Overhead, und warum wir dafür kein RAG nutzen | 20 | G1, G2, G3, G4; führt G5 ein | visual (Folie, die sich mit Aufgaben füllt), case (KISZ-Wiki) | same | same |
| S1.2 | Live demonstration | Das Wiki bei der Arbeit, mit Q&A | 15 | G2, G3 | case (KISZ-Wiki live) | same | same |
| S1.3 | Pair or group work | Drei Runden zu je 10 min, Gruppen mit höchstens drei Personen (bei 20 Personen rund sieben Gruppen), zufällig gemischt, je Runde neue Gruppen und eine neue Frage; 2 min Abschluss | 32 | G5, G4, G1 | case (eigene Wissenssammlung) | same | same |
| n/a | Networking | offenes Gespräch | offen | n/a | n/a | n/a | n/a |

##### S1.1 interface

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

##### S1.2 interface

| Field | Value |
|---|---|
| ID, type | S1.2, Live demonstration |
| Minutes | 15, inklusive Q&A; Aufteilung TBD (ask Hanno Müller, at the S1.2 planning), Vorschlag des Presenters 8 min Demo und 7 min Q&A mit hartem Stopp |
| Goals served | G2, G3 |
| Entry state | Exit state von S1.1: Schichten, Pflegekreislauf und vier Fragen als Folien gesehen. |
| Exit state | Die Teilnehmenden haben das Wiki bei der Arbeit gesehen und ihre Fragen gestellt. Was genau gezeigt wird: TBD (ask Hanno Müller, at the S1.2 planning). |
| Assets | TBD (ask Hanno Müller, at the S1.2 planning); eine Bildschirmaufnahme als Rückfall empfohlen; Anhang von S1.1 für Rückfragen |
| File | TBD (ask Hanno Müller, at the S1.2 planning) |
| Version | 1 |

##### S1.3 interface

| Field | Value |
|---|---|
| ID, type | S1.3, Pair or group work |
| Minutes | 32 (drei Runden zu je 10 min, Neuverteilung innerhalb der 10 min; 2 min Abschluss mit Handzeichen "Wiki, RAG oder beides?" und Verweis auf das Take-away) |
| Goals served | G5, G4, G1 |
| Entry state | Die Teilnehmenden haben Input und Demo gesehen; die vier Fragen mit Faustregel kennen sie von der letzten Inhaltsfolie in S1.1. |
| Exit state | Jede Person hat in Runde 2 die Wissenssammlung des eigenen Teams mit den vier Fragen eingeordnet und in drei Runden mit mehreren anderen Teilnehmenden gesprochen. Im Abschluss zeigt ein Handzeichen, wie sich der Raum entschieden hat; danach beginnt das Networking. |
| Assets | Eine Frage pro Runde plus die vier Fragen mit Faustregel auf jeder Rundenfolie oder Karte; Link oder QR-Code zum Take-away (README im Session-Ordner); Verfahren für die Zufallsgruppen: TBD (ask Hanno Müller, at the S1.3 planning) |
| File | TBD (ask Hanno Müller, at the S1.3 planning) |
| Version | 1 |

## 6. Bridges

| From | To | The one new thought |
|---|---|---|
| S1.1 (letzte Folie: vier Fragen, Kernbotschaft) | S1.2 | Die vier Fragen setzen voraus, dass sich ein Wiki pflegen lässt; die Demo zeigt, wie viel Arbeit das im Alltag ist. |
| S1.2 | S1.3 | Vom Wiki des KISZ zur eigenen Sammlung: erst sagen, wo das Wissen des eigenen Teams liegt (Runde 1), dann die vier Fragen darauf anwenden (Runde 2). |
| S1.3 (Abschluss) | Networking | Der Raum sieht im Handzeichen, wie die anderen entschieden haben; wer weiterreden will, findet im Networking die Person mit der anderen Antwort. |

## 7. Parking lot

| Item | Destination | Reason |
|---|---|---|
| Konfidenzformel aus `schema.md` (Quellen, Prüfstatus, Alter, offene TBDs) | appendix S1.1 | Für Katrin reicht "geprüft oder nicht"; RAG-Entwickler:innen fragen danach |
| Prüfsumme des Prüfstempels (`reviewed_hash`) | appendix S1.1 | Mechanik hinter "geprüft, geändert, ungeprüft" |
| CI-Checks (`wiki.py lint`, `privacy`, `reviewers`, `index --check`) | appendix S1.1 | Mechanik, nicht Geschichte |
| Tabelle der Seitentypen und Freigabestufen (Tiers) | appendix S1.1 | Detail zu Abschnitt B |
| Datenschutzregeln des Wikis (keine Teilnehmendendaten, keine Bewertungen von Kolleg:innen, nichts, was Personen aus Sprechstunden erkennbar macht) | appendix S1.1 und Q&A in S1.2 | Kommt sicher als Frage, trägt aber die Geschichte nicht |
| Voraussetzungen für ein eigenes Wiki (Git-Repository mit Merge Requests, KI-Assistent mit Dateizugriff, Prüfskript; Nextcloud oder Confluence bleiben Quellen) | appendix S1.1 und Take-away | Katrins Frage 3; für den Hauptpfad zu technisch |
| Das ganze System über das Wiki hinaus (Sprechstunden-Protokolle, Workshop-Reporting, Workshop-Planung) | Networking | Folie A2 sagt ausdrücklich, dass der Talk nur das Rückgrat zeigt; in Q&A fehlt die Zeit |
| Beispiel Datumswiderspruch erstes RAG-Forum (Nextcloud-Ordner 2026-05-15, Eventbrite 2026-06-15) | S1.1 Abschnitt D als "gefunden vom Wiki, korrigiert von einem Menschen", sobald Hanno Müller den Ordner korrigiert hat | Echte Geschichte für den Pflegekreislauf |
| Ersatzbeispiel für D: `topics/rag.md`, Abschnitt "Contradictions and open questions", z. B. GrundschutzKI nennt im Code `gpt-4o-mini`, die Evaluation lief mit `gpt-oss-120b`; offene Frage mit Zuständigem (Felix Boelter) | S1.1 Abschnitt D, falls das Datumsbeispiel nicht trägt | G3 braucht ein sicheres Beispiel |
| Begriffe, die S1.1 beim ersten Auftreten erklären muss: LLM-Wiki (Idee von Andrej Karpathy), Rückgrat, verdichten, Regeln (für die KI, wie Seiten aussehen), Merge Request (Änderungsvorschlag, den ein Mensch freigibt), Kontextfenster (wie viel Text ein Sprachmodell pro Anfrage liest; Grund, warum RAG überhaupt sucht) | S1.1 plan | Audience-Befund: Fachbegriffe ohne Einführung |
| Vorschläge des Presenters für S1.1: Titelsatz "Warum wir für unser eigenes Wissen kein RAG nutzen" als erster gesprochener Satz; Route-Satz auf A2 (20 min Input, 15 min Demo, 30 min Gespräche in Dreiergruppen über Ihre eigene Sammlung); B auf eine Folie (Karpathy nur gesprochen, Verweis im Anhang); Kontrollfrage "Wer schreibt, wer prüft?" nach B | S1.1 plan | Zeit (Schätzung 23,5 statt 20 min) und Roam-Checkpoints |
| Take-away: README.md im Session-Ordner (öffentliches Repository) mit den vier Fragen, der Faustregel, dem Verweis auf Karpathys LLM-Wiki (Gist-URL siehe Header) und den Folien als PDF; Link oder QR-Code auf der letzten Folie und den Rundenkarten (bestätigt 2026-10-09) | S1.1 (letzte Folie), S1.3 | Das KISZ-Wiki selbst ist privat; Katrin will nachlesen |
| Fragen für die drei Gruppenrunden, Vorschlag: R1 "Wo liegt das Wissen Ihres Teams heute, und wer hält es aktuell?"; R2 "Wiki, RAG oder beides? Jede Person ordnet die Sammlung ihres Teams mit den vier Fragen ein (rund 3 min pro Person), die anderen fragen nach."; R3 "Welcher Ablauf in Ihrem Team könnte sich aus so einem Wiki speisen?" | S1.3 plan | Nicht bestätigt; gehört zur Planung von S1.3 |

## 8. Expectations and pre-communication

- Told beforehand: Das Eventbrite-Listing übernimmt die Beschreibung der Juni-Ausgabe. Vorschlag für Mareike Grau, für Listing und November-Newsletter: "Fachlicher Input: Das KISZ-Wiki. Wie ein KI-gepflegtes Wiki das Wissen eines Teams aktuell hält, und warum wir dafür kein RAG nutzen. Danach eine Live-Demo und drei kurze Gesprächsrunden in Dreiergruppen über die Wissensablage Ihres eigenen Teams. Bringen Sie eine grobe Vorstellung mit, wie viele Dokumente Ihr Team ablegt und wie oft Neues dazukommt. Kein Laptop nötig." Versand TBD (ask Hanno Müller, before the Eventbrite listing).
- Expectation check on the day: kein eigener Check-in (Zeit). Die Folie mit den Aufgaben der Engineers holt die Teilnehmenden bei ihrem Alltag ab, der Route-Satz auf A2 sagt, was kommt, und Gruppenrunde 1 sammelt die Ausgangslage jeder Person.
- Interaction: Handzeichen in S1.1 (Abschnitt B0, rund 0,5 min) und Kontrollfrage nach Abschnitt B; Q&A in S1.2; drei Gruppenrunden und ein Abschluss-Handzeichen in S1.3. Nach Abzug der Neuverteilung reden die Teilnehmenden rund 27 der 67 geplanten Minuten untereinander. Beobachtung der Gruppen: KISZ-Kolleg:innen gehen zwischen den Gruppen herum, TBD (ask Hanno Müller, at the S1.3 planning).
- Time-content balance: Geplant sind 20 + 15 + 32 = 67 von 90 min (74 %). Schätzung mit Begrüßung (5 min), Demo-Zuschlag (mal 1,3, also 19,5 min) und Neuverteilung von rund 20 Personen (rund 1 min pro Runde, innerhalb der 10 min): 5 + 20 + 19,5 + 32 = 76,5 von 90 min (85 %), rund 13 min Networking. Voraussetzung: S1.1 hält 20 min; der Presenter schätzte die erste Übersicht auf 23,5 min, der S1.1-Plan kürzt deshalb (Vorschläge im Parkplatz). Kürzung im Ernstfall: Abschnitt B (Karpathy nur gesprochen), nicht Abschnitt E, weil Runde 3 die Abläufe aus E braucht.
- Open decisions for Hanno Müller: Aufteilung S1.2, bei der Planung von S1.2.
- Vorlage zum Nachbauen (Notiz von Hanno Müller, 2026-10-09): Statt einzelne Skills aus dem kisz-marketplace zu kopieren, entsteht eine eigenständige, generische Vorlage für ein LLM-Wiki ohne sensible Inhalte, konfigurierbar für eigene Daten, Quellen, Seitenstruktur und Harness, möglichst mit offenen Werkzeugen und Modellen über eine OpenAI-kompatible API. Planung und Ziele: Issue https://github.com/aihpi/workshop-rag-forum/issues/2, Branch `feature/261102-llm-wiki-template` (von `main`).
  - Vor dem Mergen: `/security-review` auf dem Branch, ohne Befund zu sensiblen Inhalten (Namen von Kolleg:innen und Partnern, interne Adressen und Pfade, Chat-Kanäle und Webhooks, Tokens, Inhalte des KISZ-Wikis).
  - Folien: Den Verweis auf die Vorlage fügt Hanno Müller selbst in die Folien ein (S1.1, Folie 12 und Anhang X6); das Take-away-README verlinkt sie ebenfalls.

## 9. Change log

| # | Date | Component | Field | Old | New | Reason | Status |
|---|---|---|---|---|---|---|---|
| C2 | 2026-10-09 | S1.1 to S1.2 | Bridge (section 6) | "die Demo zeigt, wie viel Arbeit das im Alltag ist" | "die Demo zeigt das Wiki bei der Arbeit" | Nach C1 gibt es keine Zahl zur Arbeit; das Versprechen lädt zu Fragen ein, die niemand beantworten kann; legt den Inhalt von S1.2 nicht fest | requested |
| C3 | 2026-10-09 | S1.2 | Entry state | "Exit state von S1.1: Schichten, Pflegekreislauf und vier Fragen als Folien gesehen." | "Exit state von S1.1: Schichten, Pflegekreislauf (Quelle geben, Entwurf mit offenen Fragen, Änderungsvorschlag mit Freigabe, Wartungssitzung) und vier Fragen gesehen; Änderungsvorschlag, Freigabe, Inhaltsverzeichnis und Kontextfenster sind eingeführt. Rückfragen zu Werkzeug, Quellenzugang, wer freigibt und Lesen im Browser gehen in die Q&A, mit Anhang X1 bis X7." | S1.2 muss die Fragen aufnehmen, die das Deck in die Q&A verschiebt | requested |
| C4 | 2026-10-09 | meta | Section 8, pre-communication | "wie viele Dokumente Ihr Team ablegt und wie oft Neues dazukommt" | "wie viele Personen, Projekte, Termine und Abläufe Ihr Team hat, wie oft Neues dazukommt, wer Änderungen freigeben könnte und ob Sie Cloud-Modelle nutzen dürfen" | Die vier Fragen zählen Seiten, nicht Dokumente; Hosting und Prüfende hatten keine Vorbereitung | requested |
| C5 | 2026-10-09 | meta | Section 3, Key Message | "Das Wiki gewinnt, solange wenige Dokumente langsam wachsen" | "Das Wiki gewinnt, solange es bei einigen hundert Seiten bleibt und langsam wächst" | Einheit wie im Entscheidungscheck (Seiten) | requested |
| C1 | 2026-10-09 | S1.1 | Exit state; Assets | Exit state nennt "die Prüfzeit pro Woche"; Foto TBD | Exit state ohne Zahl ("in dem Menschen nur Quellen geben und freigeben"); Fotos als Kreise in `assets/team/` | Hanno Müller kann keine Arbeitszeit oder Änderungen pro Woche nennen; Fotos geliefert | confirmed (version 1 to 2) |
