# Psychological Construct Definition Retrieval

Psychological Construct Definition Retrieval is a Python package for retrieving evidence-based definitions of psychological constructs from PubMed and PubMed Central (PMC) literature.

## Overview

The package implements a literature retrieval workflow that searches the biomedical literature for a target psychological construct, retrieves relevant PubMed abstracts and PubMed Central (PMC) full-text articles, identifies candidate definition statements, ranks evidence using semantic similarity, and selects the strongest explicit definition found in the retrieved literature.

The APA Dictionary of Psychology is used only to verify and reference existing dictionary entries. APA content is not used to identify definitions from the scientific literature.

## Workflow

![Workflow diagram: psych-defgen](images/psych-defgen-workflow.png)

## Features

- Search PubMed for articles related to a psychological construct.
- Retrieve full-text articles from PubMed Central (PMC), when available.
- Retrieve PubMed abstracts and examine them alongside available full-text articles.
- Extract candidate definition and conceptual passages from PMC full text and PubMed abstracts.
- Chunk and prepare retrieved evidence for semantic retrieval.
- Perform semantic retrieval using sentence-transformer embeddings.
- Rank evidence passages by cosine similarity to the construct-focused definitional query.
- Select the strongest explicit definition found in the retrieved literature.
- Verify APA Dictionary entries and provide the official reference URL when available.
- Export the definition from literature and supporting evidence as Markdown.
- Streamlit-based web interface for interactive construct retrieval.


---

## Installation

```bash
pip install psych-defgen
playwright install chromium
```


## Verify Installation

```bash
python -c "import psych_defgen; print('Package installed successfully')"
```

## Development Installation

To install development version from GitHub:

```bash
git clone https://github.com/uflcod/psych-defgen.git
cd psych-defgen

pip install -e .
playwright install chromium

```

Editable installation allows you to make changes to the source code and use them immediately without reinstalling the package.


---

## Configure NCBI Credentials

This package uses the NCBI Entrez API to retrieve PubMed and PubMed Central articles.

Create a `.env` file in the root of the project directory:

```text
.env
```

Add your NCBI email address and optional NCBI API key:

```env
NCBI_EMAIL=YOUR_NCBI_EMAIL
NCBI_API_KEY=YOUR_NCBI_API_KEY
```

Replace `YOUR_NCBI_EMAIL` with your email address and `YOUR_NCBI_API_KEY` with your NCBI API key.

The NCBI email address is required. The NCBI API key is optional but recommended for higher request rate limits.

The package does not store or transmit your email address or API key except when making requests to the official NCBI Entrez API. These credentials are used only to identify your requests in accordance with NCBI API guidelines.

Do not commit the `.env` file to the repository.


---

## Usage

Retrieve a definition for a psychological construct:

```bash
psych-defgen gerotranscendence
```

Multi-word constructs are supported:

```bash
psych-defgen "social isolation"
```

Specify the number of retrieved articles and evidence passages:

```bash
psych-defgen "social isolation" \
    --max-results 20 \
    --top-k 5
```

Specify a custom output file:

```bash
psych-defgen "social isolation" \
    --output results/social_isolation_definition.md
```

Display all available command-line options:

```bash
psych-defgen --help
```


---

## Web Interface

psych-defgen also provides a Streamlit-based web interface for retrieving evidence-based definitions wothout using the command line.

Start the wen interface from the project directory:

```bash
uv run streamlit run src/psych-defgen/streamlit_app.py
```

Streamlit will start a local web server and provide a URL, typically:

```text
http://localhost:8501
```

Enter a psychological construct in the web interface, optionally adjust the maximum number of evidence passages, and select **Retrieve definition**.

The web interface uses the same retrieval pipeline as the command-line interface. The retrieval, evidence ranking, and explicit-definition selection logic are therefore shared between CLI and web interface rather than implemented separately.

### NCBI Credentials in the Web Interface

- The web interface reads the NCBI email address and optional API key from environment variables:

```env
NCBI_EMAIL=YOUR_NCBI_EMAIL
NCBI_API_KEY=YOUR_NCBI_API_KEY
```

- These values can be defined in the local `.env` environment configuration file.

- NCBI credentials are used internally by the retrieval pipeline and are not displayed in the Streamlit interface.

- Then `.env` file should not be committed to Git and should remain excluded through `.gitignore`. Do not place NCBI credentials directly in the source code.

- When running `psych-defgen` locally, the credentials remain part of the local environment. If the Streamlit application is deployed to a server or hosting platform, configure the NCBI credentials using the platform's environment-variable rather than committing or uploading the local `.env` file.


## Output

By default, retrieved definitions and supporting evidence are saved as Markdown files in the `outputs` directory. A custom output file can be specified using the `--output` option.

```text
outputs/social_isolation_definition.md
```

The output filename is automatically created from the requested psychological construct.


---

## Requirements

- Python 3.11+
- Valid NCBI email address
- Chromium browser installed through Playwright

Install the required Playwright browser with

```bash
playwright install chromium
```

An NCBI API key is optional but recommended for higher request rate limits.


---

## License

This project is licensed under the MIT License.

## Citation

Citation information will be provided upon publication of the accompanying manuscript.