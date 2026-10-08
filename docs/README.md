# Sudarshan Documentation & Report Generators

This directory contains formal documentation, presentation guides, and pure Python report generator scripts created for the Compiler Design Laboratory evaluation.

## Documents & Generators Index

| File | Type | Description |
|---|---|---|
| `Phase1_Report.pdf` | Document | Formal academic project report covering lexical analysis, parsing, and semantic validation |
| `Review1_Defense_Guide.pdf` | Document | Viva-Voce presentation and defense Q&A guide for evaluation |
| `SUDARSHAN_Compiler_Documentation.pdf` | Document | Comprehensive technical specification of Sudarshan compiler architecture |
| `Phase1_Project_Report.docx` | Document | Editable Word document version of the project report |
| `Phase2_Core_Implementation_Progress_Report.pdf` | Document | Review 2 academic implementation progress report |
| `generate_pdf.py` | Engine | Pure Python PDF layout and typesetting engine |
| `generate_phase1_pdf.py` | Script | PDF compilation script generating `Phase1_Report.pdf` |
| `generate_review1_pdf.py` | Script | PDF compilation script generating `Review1_Defense_Guide.pdf` |
| `generate_docx.py` | Script | Document generator producing `Phase1_Project_Report.docx` |

## Regenerating Reports

To regenerate any report, execute its python generator script:

```bash
python3 docs/generate_phase1_pdf.py
python3 docs/generate_review1_pdf.py
python3 docs/generate_docx.py
python3 docs/generate_phase2_report.py
```
