# ITMOStalk

View students' schedules using publicly available info from ISU, which is apparently considered as stalking.

## Features:

- Authorization into ISU
- Selecting individual groups and people
- Selecting learning groups (potok)
- Caching everything for later usage

## Usage:

1. Install requirements:
```bash
pip install -r requirements.txt
```
2. Run module:
```bash 
python -m itmostalk
```

## Debugging:
1. Install `textual_dev` package
2. Open two consoles:
   1. `textual console`
   2. `textual serve --dev "python -m itmostalk"`
3. Visit http://localhost:8000 in your browser