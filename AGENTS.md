# ClearGrid repository instructions

Read PROJECT_BRIEF.md before planning or editing. Inspect the existing code,
README, dependencies, and Git status before deciding what needs to be built.

The organizer's original PDFs are in data/materials/. Read the challenge,
rubric, kickoff deck, and data dictionary. Use them to resolve requirements
and field definitions. The four AMI ZIPs and two Excel workbooks are in
data/raw/. Inventory them and inspect their headers and workbook tabs before
writing the loader. Process large files locally in chunks. Keep restricted
inputs and customer-level exports out of Git and external services.

First verify the diversity calculation and constrained battery dispatch on
small hand-computable cases. Then reproduce the 30-home showcase. Build on
working code already in this repository and report mismatches with prior
results. Generate the deck figures from the model outputs.

Use a simple script or notebook with a documented run command. Prioritize
the classification-to-offer table, July 3 dispatch figure, cost crossover,
and a runnable submission. Keep measured inputs, simulated outputs, and
assumed costs visibly labeled in all outputs.
