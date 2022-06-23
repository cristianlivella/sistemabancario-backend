# Progetto Sistemi Distribuiti 2021-2022 (traccia 2)
|Sistema bancario|
|----------------|
|Cristian Livella, matricola 866169, UniMiB|

## Descrizione del progetto

La parte backend del progetto è stata realizzata in Python, utilizzando il framework [Flask](https://flask.palletsprojects.com/).

Per il salvataggio dei dati in memoria centrale è stato utilizzato un database sqlite.

In aggiunta ai metodi con le funzionalità richieste nella consegna, è stato aggiunto un parametro facoltativo `detailed` all'endpoint `GET` `/api/account/{accountId}`. Se presente nell'URL, oltre agli identificativi delle transazioni, vengono ritornati anche tutti i dati relativi ad esse. Questo per permettere di mostrare i dati delle transazioni relative ad un account nella pagina web.

La parte frontend del progetto è stata realizzata in JavaScript, con l'aggiunta di TypeScript, del framework React e della libreria grafica Material UI.

Infine, il progetto è stato anche pubblicato online, in modo da poter essere facilmente fruibile anche senza dover installare ed eseguire nessun software.

Il progetto è disponibile al seguente indirizzo: [https://sistema-bancario.cristianlivella.com/](https://sistema-bancario.cristianlivella.com/).

Nel file `ISTRUZIONI.md` sono comunque presenti tutte le indicazioni necessarie per eseguire il progetto in locale.
