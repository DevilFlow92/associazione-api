# Changelog

## [Unreleased]

### Changed

- **Storage: rimosso dedup per checksum (#229).** `storage.save()` non
  deduplica più i file per contenuto identico: ogni chiamata genera sempre
  una key/path univoca (discriminante uuid4), indipendentemente dal
  checksum del contenuto. In precedenza due righe DB distinte con lo stesso
  contenuto potevano condividere lo stesso oggetto fisico su storage — la
  cancellazione di una faceva perdere silenziosamente il file all'altra
  (scoperto durante #217, tracciato in #229). I file salvati prima di
  questo cambiamento restano con la loro key già persistita, non vengono
  migrati. Conseguenza pratica: upload ripetuti dello stesso file non
  condividono più spazio fisico su storage, a differenza di prima.
