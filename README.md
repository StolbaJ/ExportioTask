# Baselinker Product Management

Tool for managing product supplementary fields in Baselinker inventory via API.

## Setup
```bash
pip install -r requirements.txt
echo "BASELINKER_API_TOKEN=your_token" > .env
```

## Usage

### Web Interface (for non-technical users)
```bash
streamlit run web_app.py
```
Opens browser at `http://localhost:8501` with editable product table.

### CLI (for technical users)
```bash
python main.py
```

## Tests
```bash
pytest -v
```

