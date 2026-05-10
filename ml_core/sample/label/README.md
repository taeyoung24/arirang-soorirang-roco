# Sound Labels

Audio samples are in `../sound/`.

Each JSON file keeps only the fields needed for manual labeling:

- `audio_file`: relative audio path
- `label`: `stretched_pronunciation` or `interior_pause`
- `script`: target sentence, if known
- `segments`: optional `[start_ms, end_ms]` intervals
- `notes`: free-form notes
