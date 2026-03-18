---
name: python-notebook
description: Use when writing or editing a Python notebook as a .py file with # %% cell separators instead of .ipynb format.
---

# Python Notebook (.py format)

Write notebooks as `.py` files using `# %%` to delimit cells. Compatible with VS Code, Jupyter, and Cursor.

## Cell Examples

```python
# %% [markdown]
# ## Section heading
# Prose explanation here.

# %%
import pandas as pd

df = pd.read_csv("data.csv")
df.head()

# %% Named cell
result = df.groupby("col").sum()
```

## Rules

- First cell: imports only
- One logical idea per cell
- Markdown cells for section headings and explanations
- Name cells (`# %% My Label`) when they produce a key result
- No `print()` for dataframes/arrays - bare expression on last line renders inline
