# Bouquet animato

Un bouquet di fiori che cresce e sboccia, scritto in Python. Gli steli salgono, i fiori si aprono, una carta di incarto con il nastro avvolge il mazzo, e alla fine i fiori continuano a oscillare dolcemente.

Il progetto ha due versioni:

| File | Cosa fa |
|------|---------|
| `bouquet_ascii.py` | Disegna il bouquet direttamente nel terminale, in ASCII a colori. Versione principale. |
| `bouquet.py` | Versione grafica con matplotlib, in una finestra senza bottoni, su sfondo scuro. |

## Requisiti

- Python 3.8 o superiore
- `numpy` (per entrambe le versioni)
- `matplotlib` (solo per `bouquet.py`)
- `pillow` (solo per salvare la GIF con `bouquet.py --save`)

Per la versione ASCII serve inoltre un terminale con colori a 24 bit (true color) e un font a larghezza fissa. Su Windows va bene Windows Terminal; il vecchio prompt dei comandi non basta.

## Installazione

```
pip install numpy
```

Per la versione matplotlib:

```
pip install numpy matplotlib pillow
```

## Uso

### Versione ASCII

```
python bouquet_ascii.py
python bouquet_ascii.py 1.5
```

L'argomento facoltativo è la velocità: `1.5` significa 1,5 volte più veloce, `0.5` metà velocità (minimo `0.1`).

- La crescita avviene una sola volta, poi i fiori restano a oscillare.
- Premi `Ctrl+C` per uscire. Il terminale torna com'era prima (il bouquet scompare dallo schermo).
- Ingrandisci il terminale prima di avviarlo: l'animazione si adatta alle dimensioni e si ridimensiona anche se le cambi mentre gira. Più righe ci sono, più il disegno è dettagliato (fino a 60 righe).

### Versione matplotlib

```
python bouquet.py
python bouquet.py --save
```

- Senza argomenti apre una finestra con solo l'animazione, senza barra dei bottoni e, con il backend TkAgg, senza barra del titolo. Premi `Esc` o `Q` per chiuderla.
- Con `--save` crea `bouquet.gif` (serve `pillow`).
- Se non vuoi la finestra senza bordo, togli la riga con `overrideredirect(True)`.

## Come funziona la versione ASCII

Ogni frame viene disegnato su una griglia di caratteri con numpy: gli steli sono curve di Bézier che crescono nel tempo, i petali sono ellissi calcolate solo in una piccola finestra attorno al loro centro, la carta e il nastro sono triangoli. Il frame intero viene poi trasformato in una sola stringa con sequenze ANSI di colore e scritto in un unico `write`, per evitare lo sfarfallio. Il rendering costa pochi millisecondi a frame.

I fiori sono su tre livelli di altezza per sovrapporsi meno, e ognuno dei tre ha un set di caratteri diverso per i petali, così fiori vicini si distinguono anche dove si toccano. I colori seguono una palette di sei tonalità.

## Personalizzazione (`bouquet_ascii.py`)

I parametri principali sono in cima al file:

| Parametro | Effetto |
|-----------|---------|
| `FPS` | Fotogrammi al secondo (default 40) |
| `N_FLOWERS` | Numero di fiori (default 9). Più fiori significa più sovrapposizioni |
| `FLOWER_SCALE` | Dimensione dei fiori |
| `MAX_ROWS` | Righe massime usate nel terminale |
| `XMIN`, `XMAX`, `YMIN`, `YMAX` | Proporzioni della scena: più alta che larga rende il bouquet più slanciato |
| `T_STEMS`, `T_BLOOM`, `T_WRAP`, `TOTAL` | Tempi (in frame) di crescita, fioritura, incarto e fine della composizione |
| `STYLES` | Caratteri usati per i petali di ciascun tipo di fiore |
| `PALETTE` | Colori dei fiori |

Il fatto che i fiori siano sempre uguali a ogni avvio dipende dal seed del generatore casuale (`default_rng(7)`): cambialo per ottenere un mazzo diverso.

L'ampiezza dell'oscillazione è il valore `0.07` nella riga `sway = ...` della funzione `render`, e la frequenza è il `0.12`.

## Problemi comuni

- **Colori sbagliati o caratteri strani sul terminale**: il terminale non supporta il true color. Usa Windows Terminal o un terminale moderno.
- **Fiori schiacciati o allungati**: le celle del tuo font hanno un rapporto altezza/larghezza diverso da quello previsto (circa 2:1). Cambia il rapporto nel calcolo di `self.W` nella classe `Renderer`.
- **Il disegno è piccolo o poco dettagliato**: ingrandisci la finestra del terminale o riduci il carattere. Lo script usa tutto lo spazio disponibile.
- **Nulla appare, o compaiono sequenze di escape come testo**: assicurati di avviare lo script da un terminale e non da un ambiente che non interpreta i codici ANSI (alcuni editor, console integrate).
