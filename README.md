# Bouquet ASCII

Un bouquet di fiori animato, disegnato interamente con caratteri ASCII a colori direttamente nel terminale.

Gli steli crescono, i fiori sbocciano uno dopo l'altro, compare la carta di incarto con il nastro e, a composizione completa, i fiori continuano a oscillare dolcemente finche' non interrompi il programma.

## Caratteristiche

- Rendering a colori a 24 bit (true color) tramite sequenze ANSI
- Animazione in un solo ciclo di crescita, seguita da un'oscillazione continua
- Fiori generati in modo procedurale: numero di petali, dimensione, rotazione e colori variano da fiore a fiore
- Tre stili di caratteri diversi per i petali, per dare piu' varieta' visiva
- Adattamento automatico alla dimensione del terminale, anche se la finestra viene ridimensionata mentre l'animazione gira
- Un solo `write` per frame, per evitare lo sfarfallio
- Risultato riproducibile: il seed casuale e' fisso, quindi il bouquet e' sempre lo stesso

## Requisiti

- Python 3.8 o superiore
- NumPy
- Un terminale con supporto ai colori a 24 bit (ad esempio Windows Terminal, iTerm2, GNOME Terminal, Kitty, Alacritty)

## Installazione

```bash
git clone https://github.com/sam1093k/Bouquet.git
cd Bouquet
pip install numpy
```

## Utilizzo

```bash
python bouquet_ascii.py
```

Per cambiare la velocita' dell'animazione, passa un moltiplicatore come argomento:

```bash
python bouquet_ascii.py 1.5   # 1.5x piu' veloce
python bouquet_ascii.py 0.5   # meta' velocita'
```

Il valore minimo accettato e' `0.1`; un valore non valido viene ignorato e si usa la velocita' normale.

Per uscire premi `Ctrl+C`: il terminale viene ripristinato (cursore e schermo originale compresi).

Consiglio: ingrandisci la finestra del terminale prima di avviare lo script, cosi' il bouquet viene disegnato con maggiore dettaglio.

## Configurazione

I parametri principali si trovano in cima al file:

| Parametro | Descrizione |
|---|---|
| `FPS` | Frame al secondo dell'animazione |
| `N_FLOWERS` | Numero di fiori nel bouquet |
| `T_STEMS` | Frame in cui finiscono di crescere gli steli |
| `T_BLOOM` | Frame in cui finiscono di sbocciare i fiori |
| `T_WRAP` | Frame in cui compare la carta con il nastro |
| `TOTAL` | Frame in cui la composizione e' completa |
| `FLOWER_SCALE` | Dimensione dei fiori (piu' alto = fiori piu' grandi) |
| `MAX_ROWS` | Altezza massima in righe del disegno |

Per cambiare la disposizione dei fiori modifica il seed in `np.random.default_rng(7)`. La palette si personalizza nella lista `PALETTE` (colori in esadecimale) e i caratteri usati per i petali in `STYLES`.

## Come funziona

1. **Griglia di caratteri.** La classe `Renderer` mantiene due matrici: una di caratteri e una di colori. Il "mondo" e' un rettangolo di coordinate (`XMIN`..`XMAX`, `YMIN`..`YMAX`) mappato sulla griglia, tenendo conto che le celle del terminale sono alte circa il doppio di quanto sono larghe.
2. **Primitive.** Ellissi (petali, foglie, centri), triangoli (carta e nastro) e polilinee (steli) vengono rasterizzati con NumPy in modo vettorializzato.
3. **Steli.** Ogni stelo e' una curva di Bezier quadratica, che cresce progressivamente e oscilla leggermente una volta completata la composizione.
4. **Fiori.** Ogni fiore e' composto da due corone di petali (esterna e interna sfalsata), con bordo dedicato e centro. Lo sbocciare e' controllato da una funzione di easing (`smoothstep`).
5. **Output.** La scena viene convertita in una singola stringa di sequenze ANSI, scritta in un unico `write` per frame sullo schermo alternativo del terminale.

## Struttura del progetto

```
.
├── bouquet_ascii.py   # script principale
└── README.md
```

## Risoluzione dei problemi

- **I colori sono sbagliati o assenti:** il terminale non supporta il true color. Usa Windows Terminal o un emulatore moderno. Il vecchio `cmd.exe` non e' adatto.
- **Il disegno e' piccolo o tagliato:** ingrandisci la finestra e rilancia lo script.
- **L'animazione e' lenta:** abbassa `FPS` o riduci la dimensione della finestra; il costo del rendering cresce con l'area disegnata.

## Licenza

Aggiungi qui la licenza del progetto (ad esempio MIT).
