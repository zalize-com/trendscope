# Kaggle upload bundle

`dataset-metadata.json` is ready for `kaggle datasets create` or the web UI.

To build the upload dir locally:

```bash
cp data/history.csv data/latest.json data/kaggle/
kaggle datasets create -p data/kaggle        # first upload
kaggle datasets version -p data/kaggle -m "daily refresh"  # subsequent
```

(history.csv + latest.json are .gitignored in this directory to avoid
duplicating 67 MB into the repo — they regenerate every collect.)
