# File Validation Preview - Test Examples

## Example Validation Results

### 1. Valid CSV File with Genes

**Input File**: `gene_panel.csv`
```csv
gene,pathogenicity,condition
BRCA1,pathogenic,breast cancer
TP53,likely_pathogenic,tumor suppressor
CFTR,pathogenic,cystic fibrosis
```

**Validation Result**:
```
✅ gene_panel.csv - Valid
📊 Statistics:
- 3 Data Rows
- 3 Columns  
- 3 Unique Genes
- Gene Column: gene

🧬 Sample Genes: BRCA1, TP53, CFTR
```

### 2. File with Warnings

**Input File**: `large_panel.tsv`
```tsv
entity_name	confidence	disease_group
BRCA1	high	cancer
tp53	medium	oncology
invalidGene123	low	unknown
```

**Validation Result**:
```
✅ large_panel.tsv - Valid (with warnings)
⚠️ Warnings:
- 1 genes may have invalid symbols (e.g., invalidGene123)
- Mixed case gene symbols detected

📊 Statistics:
- 3 Data Rows
- 3 Columns
- 3 Unique Genes  
- Gene Column: entity_name

🧬 Sample Genes: BRCA1, tp53, invalidGene123
```

### 3. File with Errors

**Input File**: `invalid_file.txt`
```txt
not,a,gene,file
just,random,data,here
no,genes,found,anywhere
```

**Validation Result**:
```
❌ invalid_file.txt - Invalid
🚫 Errors:
- No recognized gene column found. Looking for: gene, genes, entity_name, genesymbol, symbol, gene_symbol

📊 Statistics:
- 3 Data Rows
- 4 Columns
- 0 Unique Genes
- Gene Column: None
```

### 4. Large File Warning

**Input File**: `huge_panel.csv` (15,000 rows)
```
✅ huge_panel.csv - Valid (with warnings)
⚠️ Warnings:
- Large file with 15000 rows. Processing may take longer.

📊 Statistics:
- 14,999 Data Rows
- 2 Columns
- 8,432 Unique Genes
- Gene Column: gene_symbol

🧬 Sample Genes: BRCA1, TP53, CFTR, ATM, CHEK2, PALB2, BARD1, RAD51C, ...
+8,412 more
```

### 5. Excel File Detection

**Input File**: `panel_data.xlsx`
```
✅ panel_data.xlsx - Valid (with warnings)
⚠️ Warnings:
- Excel files will be processed server-side. Preview may be limited.

📊 Statistics:
- Format: Excel
- Requires Server Processing: true
```

## User Interface Flow

### Step 1: File Selection
```
[Drop Zone]
📁 Drag & drop your file here, or click to select
```

### Step 2: Auto-Validation
```
[Loading State]
🔄 Validating files...
```

### Step 3: Results Display
```
[Validation Results]
🔍 File Validation Results

✅ gene_panel.csv - Valid
📊 [Statistics Grid]
🧬 [Gene Samples]
📋 [Data Preview - expandable]

[Buttons]
🚀 Upload  |  🔍 Validate Files
```

### Step 4: Upload Confirmation
If errors exist:
```
❌ Some files have validation errors. 
Do you want to proceed with upload anyway?
[Cancel] [Proceed Anyway]
```

## Technical Implementation Highlights

### Validation Pipeline:
1. **File Size Check** → Reject if >10MB
2. **Format Detection** → CSV/TSV/TXT parsing, Excel flagging  
3. **Structure Analysis** → Row/column validation
4. **Gene Column Detection** → Smart column name matching
5. **Content Extraction** → Gene list compilation
6. **Symbol Validation** → Basic pattern matching
7. **Statistics Generation** → Summary creation
8. **UI Rendering** → Interactive results display

### Error Recovery:
- **Clear Messages**: Specific error descriptions with solutions
- **Partial Success**: Show what was detected even with errors
- **Re-validation**: Easy re-run after file modifications
- **Progressive Enhancement**: Basic functionality works without JS

### Performance Optimizations:
- **Streaming Reading**: Large file handling
- **Preview Limits**: Only process first 100 rows for preview
- **Lazy Rendering**: Expandable sections for detailed data
- **Async Processing**: Non-blocking validation

This implementation provides comprehensive file validation while maintaining excellent user experience and performance.
