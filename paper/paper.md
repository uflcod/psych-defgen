---
title: 'psych-defgen: Psychological Construct Definition Retrieval and Synthesis'
tags:
    - Python
    - Psychological constructs
    - PubMed
    - Natural language processing
    - Ontology development
    - Large language models
    - Definition extraction
    - Definition synthesis

authors:
    - name: B. Damayanthi Jesudas
      affiliation: 1
      corresponding: true
    - name: Maxime Jublou
      affiliation: 3
    - name: Jeremy Ravenel
      affiliation: 3
    - name: Julie C. Bowker
      affiliation: 4
    - name: John Beverley
      affiliation: "5, 6"
    - name: William D. Duncan
      affiliation: "1, 2"


affiliations:
    - index: 1
      name: Department of Community Dentistry and Behavioral Science, University of Florida College of Dentistry, Gainesville, FL, USA
    - index: 2
      name: Geriatrics Research, Education, and Clinical Center (GRECC), NF/SG VAHS, Gainesville, FL, USA
    - index: 3
      name: NaasAI, Inc., DE, USA
    - index: 4
      name: Department of Psychology, University at Buffalo, Buffalo, NY, USA
    - index: 5
      name: Department of Philosophy, University at Buffalo, Buffalo, NY, USA
    - index: 6
      name: Institute for Artificial Intelligence and Data Science, Buffalo, NY, USA



date: 25 November 2026
bibliography: paper.bib
---

# Summary

`psych-defgen` is an open-source Python package for retrieving and synthesizing definitions of psychological constructs from scientific literature. Given a user-specified construct, the software searches PubMed and retrieves relevant PubMed Central (PMC) full-text articles. PubMed abstracts are used as fallback evidence when full text is not available.

The software supports two complementary definition outputs. The first is a literature-based definition extracted from scientific literature, when available. The second is an independently generated AI-synthesized definition that consolidates information from relevant evidence passages across the scientific literature into a comprehensive definition. The workflow combines rule-based definition candidate extraction, semantic evidence retrieval, and large language model (LLM)-assisted definition processing.

Both definitions are accompanied by ranked supporting evidence and available provenance information including article titles, source types (PMC full text or PubMed abstract), PubMed identifiers (PMIDs), PubMed Central identifiers (PMCIDs), and links to the corresponding literature records. Users can access the workflow through a command-line interface or a Streamlit-based web interface [@streamlit].


# Statement of Need

`psych-defgen` was developed as part of the Promoting Healthy Aging through Semantic Enrichment of Solitude Research (PHASES) project [@beverley2025healthyaging]. One aim of the PHASES project is to develop the Solitude Ontology and the Gerotranscendence Ontology. The software was subsequently developed to retrieve literature-based definitions for concepts identified through an earlier BERTopic analysis [@jesudas2026bertopic], as well as for other user-specified psychological constructs.

Manually searching numerous scientific articles to identify definitions and relevant supporting passages is time-consuming. Although bibliographic search systems such as PubMed identify publications containing a construct, researchers must examine the literature to locate definitions, which may vary across studies. Furthermore, some constructs may be discussed without being explicitly defined, and information describing a construct may be distributed across multiple scientific articles.

`psych-defgen` addresses these challenges by facilitating the retrieval of existing definitions and independently synthesizing definitions from relevant scientific evidence. This enables researchers to expeditiously review and trace definitions to their literature sources for expert evaluation and ontology curation.

# State of the Field

PubMed [@pubmed] and PMC [@pmc] enable researchers to find relevant publications and full-text articles, but identifying definitional statements within and across these resources requires further analysis. The APA Dictionary of Psychology [@apa_dictionary] provides curated definitions of psychological terms, but an entry is not necessarily available for every term investigated in research.

Existing AI-assisted research tools such as Elicit [@elicit], scite [@scite], and  Consensus [@consensus] support scientific literature retrieval, evidence synthesis, and AI-generated responses with supporting citations. Although these tools can provide definitions when prompted, their documented workflows are designed for broader research tasks rather than the systematic extraction and synthesis of psychological construct definitions as separate outputs.

`psych-defgen` addresses this gap through a dedicated workflow that extracts existing literature-based definitions while preserving their original wording and independently generates comprehensive definitions by consolidating information from semantically ranked evidence passages, including for constructs that are discussed but not explicitly defined in the retrieved scientific literature.


# Software Design

`psych-defgen` follows a modular architecture that supports the independent development and refinement of literature retrieval, candidate extraction, semantic evidence ranking, definition selection, and AI-assisted synthesis.

The overall architecture of `psych-defgen` is illustrated in \autoref{fig:workflow}.

![Overview of the psych-defgen workflow.\label{fig:workflow}](../images/psych-defgen-workflow.png)

Literature retrieval and processing: NCBI access is configured through Entrez using an email address and optional API key. PubMed is searched using a quoted Title/Abstract query for the requested construct, returning a configurable number of PMIDs sorted by relevance. Retrieved PMIDs are mapped to available PMC articles. When usable PMC full text is available, the article XML is retrieved and parsed to extract the article title, abstract, and body text. The article text is divided into overlapping chunks using a target chunk size of 180 words and an overlap of up to 40 words while preserving sentence boundaries. When usable PMC full text is unavailable, the corresponding PubMed abstract is retrieved as fallback evidence. Candidate definition statements are extracted using construct occurrences and predefined linguistic patterns.

Semantic evidence retrieval: Extracted definition candidates, PMC article chunks, and fallback PubMed abstracts form a combined retrieval pool. Evidence passages and five construct-focused definitional queries are embedded using the `all-MiniLM-L6-v2` sentence-transformer model [@minilm; @reimers2019sentencebert]. Evidence passages are ranked by their mean cosine similarity across the five queries. The retrieval process retains a configurable number of top-ranked passages, with no more than two passages per article. Although semantic similarity indicates the relevance of a passage to the queries, high similarity does not necessarily indicate that the passage contains a definition. Therefore, separate linguistic patterns and LLM-assisted selection are employed to identify existing definitions.

Literature-based definition extraction: Extracted definition candidates and semantically ranked evidence passages are evaluated using predefined linguistic patterns that prioritize explicit definitional constructions, such as "is defined as", "refers to", and "is a". Candidate definitions are prioritized according to their linguistic patterns, with semantic similarity used as a secondary ranking criterion. If no suitable explicit definition is identified, fallback patterns are applied to identify definition-like statements. The LLM-selected definition is accepted only if it occurs as an extact substring of one of the supplied evidence passages, thereby preserving its original wording without AI-generated rewriting or synthesis. If no suitable definition is identified, the software reports that no definition matching the selection criteria was found in the retrieved literature.

AI-synthesized definition generation: Independent of literature-based definition extraction, a configurable LLM generates a comprehensive definition by consolidating relevant information from the user-specified number of top-ranked evidence passages. The LLM is instructed to use only the supplied evidence, remove redundant information, and avoid introducing unsupported information. When no evidence is retrieved or the LLM reports insufficient evidence, no synthesized definition is returned. The software supports configurable LLM providers, including local models through Ollama, OpenRouter, and custom OpenAI-compatible endpoints.

Reference checking and interfaces: The APA Dictionary of Psychology is checked independently for an existing entry and its official reference URL, without incorporating dictionary content into definition selection or synthesis. The workflow is accessible through command-line and Streamlit interfaces, with structured results and supporting evidence available for review. The software records available LLM token usage for literature-based definition selection and AI synthesis and saves structured results in JSON format to support subsequent review and analysis.

Software testing: Automated tests evaluate literature-based definition selection, including multiple definitional constructions and singular/plural term variants.


# Research Impact Statement

Within the PHASES project, `psych-defgen` supports the development of the Solitude Ontology and the Gerotranscendence Ontology by facilitating the identification and curation of definitions for psychological constructs. When searching for a construct, the software can provide an existing literature-based definition alongside a synthesized definition that integrates relevant conceptual information from multiple evidence passages. This helps researchers to compare the definitions, examine the supporting literature, and refine definitions for ontology representation.

Beyond PHASES, the software provides a reusable approach to definition retrieval and synthesis for researchers in psychology, ontology development, and related fields with expert review remaining necessary to assess the accuracy and suitability of the resulting definitions.


# Tool Validation

The functionality of `psych-defgen` was assessed using 60 unique psychological constructs, of which 10 were qualitatively evaluated by a subject matter expert in psychology. Literature-based definition outputs were obtained for 41 constructs (68.3%), while AI-synthesized definitions were generated for 48 constructs (80.0%). AI synthesis provided candidate definitions for seven constructs for which no literature-based definition was retrieved. Neither definition was obtained for 12 constructs (20.0%).

The expert identified opportunities to improve definition selection, source attribution, and the conceptual accuracy and conciseness of synthesized definitions. Incorporating citation frequency was also suggested to facilitate the identification of widely cited definitions. These findings inform the continued refinement of `psych-defgen`.


# Funding
This research was funded by the National Institute on Aging, National Institutes of Health, grant number 1U01AG088074-01.


# AI Usage Disclosure

Generative AI was used to assist with code development and refinement, and with manuscript language editing. AI-generated suggestions were reviewed and modified by the authors.


