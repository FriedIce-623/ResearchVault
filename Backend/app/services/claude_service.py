"""
claude_service.py
-----------------
Single source of truth for every Claude API call in ResearchVault.

Functions:
  detect_paper_type(text)            -> "empirical" | "survey" | "theoretical"
  extract_paper(text, paper_type)    -> dict matching the paper schema
  ask_question(question, chunks, history) -> dict { answer, citations }
  ask_question_stream(question, chunks, history) -> generator of SSE strings
  compare_papers(paper_docs, dimensions)  -> dict comparison result
"""

import os
import json
import time
import anthropic
from anthropic import Anthropic
from anthropic.types import (
    MessageParam,
    ToolParam,
    TextBlock,
    ToolUseBlock,
)
from typing import Generator, Any, cast

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------------------
# SYSTEM PROMPTS
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """\
You are an expert academic research paper analyst with deep knowledge across \
computer science, machine learning, NLP, computer vision, and related fields.

Your job is to extract structured metadata from research papers with high precision.

Rules:
- Extract only what is explicitly stated in the paper. Do not infer or fabricate.
- If a field is not mentioned or not applicable to this paper, omit it entirely.
- For numeric values (samples, classes etc.), extract the exact number stated.
- For dates, use the format YYYY-MM if the full date is unavailable, or YYYY if only the year is stated.
- For authors, use the full name as written in the paper (e.g. "Ashish Vaswani", not "Vaswani et al.").
- For DOI, extract the raw DOI string (e.g. "10.1234/example") not the full URL.
- For code_link, only include if an explicit GitHub or project URL is provided in the paper.
- For metrics_used, use the metric name as the key and a description/formula as the value \
  (e.g. {"accuracy": "top-1 classification accuracy on test set", "F1": "macro-averaged F1 score"}).
- For results, use the metric name as the key and the best reported value as the value \
  (e.g. {"accuracy": "94.3%", "F1": "0.912"}). Include the dataset name in the key if results \
  are reported on multiple datasets (e.g. {"accuracy_ImageNet": "78.2%"}).
- key_insights should be 2-4 sentences capturing what makes this paper novel or important.
- limitations should be a concise paragraph of what the authors acknowledge as weaknesses or \
  future work. Include limitations you can infer from the methodology if not explicitly stated.
- Be precise and technical. These extractions are used by ML researchers.\
"""

ASK_SYSTEM_PROMPT = """\
You are ResearchVault, an AI research assistant with access to a curated library \
of research papers. You help researchers understand, analyse, and navigate academic literature.

You have been given retrieved sections from relevant papers as context. Your answers must:
1. Be grounded only in the provided context — do not use outside knowledge to fill gaps.
2. Always cite the specific paper and section your answer draws from, \
   using the format [Paper: <paper_id> | Section: <section>].
3. If the context does not contain enough information to answer fully, say so explicitly \
   rather than guessing.
4. Use precise technical language appropriate for ML/CS researchers.
5. If asked to compare, contrast, or summarise across multiple papers, structure your \
   answer clearly with headings or bullet points.
6. Be concise but complete. Prefer depth over breadth.\
"""

COMPARE_SYSTEM_PROMPT = """\
You are an expert ML research analyst. You will be given structured metadata \
for multiple research papers and asked to compare them across specific dimensions.

Rules:
- Be objective and precise. Report what the papers state, not your opinion.
- For numeric comparisons (metrics, results), extract exact numbers where available.
- For the summary, write 3-5 sentences capturing the most important differences.
- For key_differences, write each as a standalone factual statement.
- For recommendation, suggest which paper is best suited for which use case — \
  be specific (e.g. "Paper A is better for low-resource settings; Paper B achieves \
  higher accuracy but requires 10x more compute").
- If a dimension does not apply to a paper, set value to "N/A" with a brief reason.\
"""

# ---------------------------------------------------------------------------
# TOOL DEFINITIONS
# ---------------------------------------------------------------------------

DETECT_TYPE_TOOL = {
    "name": "classify_paper",
    "description": "Detect and classify the type of a research paper based on its content.",
    "input_schema": {
        "type": "object",
        "properties": {
            "paper_type": {
                "type": "string",
                "enum": ["empirical", "survey", "theoretical"],
                "description": (
                    "empirical: paper that proposes a model, system, or method and evaluates it "
                    "with experiments, benchmarks, or quantitative results. "
                    "survey: paper that reviews, categorises, and synthesises existing literature "
                    "without proposing a new method. Also called literature review or systematic review. "
                    "theoretical: paper that proposes mathematical frameworks, proofs, complexity "
                    "analyses, or conceptual frameworks without primary experiments."
                )
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "How confident you are in this classification."
            },
            "reasoning": {
                "type": "string",
                "description": "One sentence explaining why you chose this type."
            }
        },
        "required": ["paper_type", "confidence", "reasoning"]
    }
}


EMPIRICAL_TOOL = {
    "name": "extract_empirical",
    "description": "Extract all structured metadata from an empirical research paper.",
    "input_schema": {
        "type": "object",
        "properties": {

            # --- Base fields ---
            "name": {
                "type": "string",
                "description": "Full official title of the paper exactly as it appears in the document."
            },
            "authors": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Full names of all authors in order of appearance "
                    "(e.g. ['Ashish Vaswani', 'Noam Shazeer', 'Niki Parmar']). "
                    "Do not abbreviate or use 'et al.'."
                )
            },
            "date_of_publication": {
                "type": "string",
                "description": (
                    "Publication date. Use YYYY-MM-DD if full date known, "
                    "YYYY-MM if only month and year, YYYY if only year. "
                    "Check the paper header, footer, and conference/journal reference."
                )
            },
            "doi": {
                "type": "string",
                "description": (
                    "Digital Object Identifier as a raw string without the https://doi.org/ prefix "
                    "(e.g. '10.18653/v1/2020.acl-main.463'). Only include if explicitly stated."
                )
            },
            "link": {
                "type": "string",
                "description": (
                    "URL to the paper (arXiv link, ACL Anthology, conference proceedings page etc.). "
                    "Only include if explicitly stated in the paper."
                )
            },
            "code_link": {
                "type": "string",
                "description": (
                    "URL to the official code repository (GitHub, GitLab, project website etc.). "
                    "Only include if an explicit link is provided in the paper. "
                    "Do not infer from author names or institution."
                )
            },
            "key_insights": {
                "type": "string",
                "description": (
                    "2-4 sentences capturing: (1) what problem this paper solves, "
                    "(2) what is novel about their approach, "
                    "(3) what the key result or contribution is. "
                    "Write for a technical ML audience. Be specific, not generic."
                )
            },
            "limitations": {
                "type": "string",
                "description": (
                    "Concise paragraph covering limitations explicitly acknowledged by the authors "
                    "(often in a Limitations or Future Work section) plus any clear methodological "
                    "weaknesses observable from the paper (e.g. only tested on English, "
                    "requires large compute, sensitive to hyperparameters). "
                    "Be specific and technical."
                )
            },
            "metrics_used": {
                "type": "object",
                "description": (
                    "Dictionary of evaluation metrics used in the paper. "
                    "Key = metric name (e.g. 'accuracy', 'BLEU', 'F1', 'mAP', 'perplexity'). "
                    "Value = description of how it is computed or what it measures "
                    "(e.g. 'macro-averaged F1 score over all classes', "
                    "'BLEU-4 computed on the test set with Moses tokenizer'). "
                    "Include all metrics reported in results tables."
                ),
                "additionalProperties": {"type": "string"}
            },
            "results": {
                "type": "object",
                "description": (
                    "Best reported results from the paper. "
                    "Key = metric name, optionally suffixed with dataset name if multiple datasets used "
                    "(e.g. 'accuracy_ImageNet', 'F1_CoNLL2003', 'BLEU_WMT14_EN-DE'). "
                    "Value = exact value as reported (e.g. '94.3%', '0.912', '29.4'). "
                    "Include the main results table results. For multiple runs, use the best/final result."
                ),
                "additionalProperties": {"type": "string"}
            },

            # --- Empirical-specific fields ---
            "architecture": {
                "type": "string",
                "description": (
                    "The core model architecture or system design proposed or used. "
                    "Be specific: not just 'transformer' but 'encoder-decoder transformer with "
                    "cross-attention and relative position embeddings'. "
                    "Include the key architectural innovation if any."
                )
            },
            "key_techniques": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of the most important techniques, methods, or components used or proposed. "
                    "Each item should be a short noun phrase (e.g. 'multi-head self-attention', "
                    "'contrastive learning', 'data augmentation with mixup', "
                    "'gradient checkpointing', 'LoRA fine-tuning'). "
                    "Include 3-8 items. Focus on what is technically distinctive."
                )
            },
            "preprocessing": {
                "type": "string",
                "description": (
                    "Data preprocessing pipeline applied before training. Include: "
                    "tokenisation strategy (BPE, WordPiece, character-level etc.), "
                    "normalisation (lowercasing, Unicode normalisation etc.), "
                    "filtering steps (deduplication, length filtering etc.), "
                    "image transforms if applicable (resize, crop, normalise etc.), "
                    "and any data cleaning steps. Be specific about parameters where stated."
                )
            },
            "training_strategy": {
                "type": "string",
                "description": (
                    "How the model was trained. Include: optimiser and learning rate schedule, "
                    "batch size, number of epochs or steps, hardware used (e.g. '8x A100 GPUs'), "
                    "training time if stated, regularisation (dropout, weight decay etc.), "
                    "loss function, any special training tricks (gradient clipping, mixed precision etc.), "
                    "and fine-tuning strategy if applicable (full fine-tune, adapter, LoRA etc.)."
                )
            },

            # --- Datasets sub-documents ---
            "datasets": {
                "type": "array",
                "description": (
                    "All datasets used in this paper for training, validation, or evaluation. "
                    "Include benchmark datasets, custom datasets, and pre-training corpora. "
                    "Extract one object per dataset."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "dataset_name": {
                            "type": "string",
                            "description": (
                                "Official name of the dataset exactly as used in the paper "
                                "(e.g. 'ImageNet-1K', 'SQuAD 2.0', 'COCO 2017', 'Common Crawl'). "
                                "Do not abbreviate unless the paper uses abbreviations."
                            )
                        },
                        "public": {
                            "type": "boolean",
                            "description": (
                                "True if the dataset is publicly available for download. "
                                "False if it is proprietary, internal, or not publicly released. "
                                "Omit if not determinable from the paper."
                            )
                        },
                        "samples": {
                            "type": "integer",
                            "description": (
                                "Total number of samples/examples in the dataset. "
                                "If split sizes are given (train/val/test), sum them. "
                                "For text corpora, use number of documents or sentences if tokens not given. "
                                "Omit if not stated."
                            )
                        },
                        "support": {
                            "type": "string",
                            "description": (
                                "Train/validation/test split sizes as a string "
                                "(e.g. '100K train / 5K val / 10K test'). "
                                "Omit if not stated."
                            )
                        },
                        "classes": {
                            "type": "integer",
                            "description": (
                                "Number of output classes or labels for classification tasks. "
                                "For NER, number of entity types. "
                                "Omit for regression, generation, or retrieval tasks."
                            )
                        },
                        "task": {
                            "type": "string",
                            "description": (
                                "The ML task this dataset is used for. Be specific: "
                                "'image classification', 'named entity recognition', "
                                "'machine translation (EN→DE)', 'question answering', "
                                "'text summarisation', 'object detection', "
                                "'semantic segmentation', 'pre-training language model' etc."
                            )
                        },
                        "modality": {
                            "type": "string",
                            "description": (
                                "Data modality or type: 'text', 'image', 'audio', 'video', "
                                "'tabular', 'graph', 'multimodal (text+image)', "
                                "'point cloud', 'time series' etc."
                            )
                        },
                        "link": {
                            "type": "string",
                            "description": (
                                "URL to download or access the dataset. "
                                "Only include if explicitly stated in the paper."
                            )
                        },
                        "key_insights": {
                            "type": "string",
                            "description": (
                                "1-2 sentences on how this dataset is used in the paper and "
                                "any notable characteristics mentioned "
                                "(e.g. 'Used for pre-training only; authors note it contains "
                                "significant noise requiring careful filtering')."
                            )
                        }
                    },
                    "required": ["dataset_name"]
                }
            }
        },
        "required": ["name", "authors"]
    }
}


SURVEY_TOOL = {
    "name": "extract_survey",
    "description": "Extract all structured metadata from a survey or literature review paper.",
    "input_schema": {
        "type": "object",
        "properties": {

            # --- Base fields (same descriptions as empirical) ---
            "name": {
                "type": "string",
                "description": "Full official title of the paper exactly as it appears in the document."
            },
            "authors": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Full names of all authors in order of appearance. "
                    "Do not abbreviate or use 'et al.'."
                )
            },
            "date_of_publication": {
                "type": "string",
                "description": (
                    "Publication date. Use YYYY-MM-DD if full date known, "
                    "YYYY-MM if only month and year, YYYY if only year."
                )
            },
            "doi": {
                "type": "string",
                "description": "Raw DOI string without https://doi.org/ prefix. Only if explicitly stated."
            },
            "link": {
                "type": "string",
                "description": "URL to the paper. Only if explicitly stated."
            },
            "code_link": {
                "type": "string",
                "description": "URL to code or resources released alongside the survey. Only if stated."
            },
            "key_insights": {
                "type": "string",
                "description": (
                    "2-4 sentences on: (1) what field or topic this survey covers, "
                    "(2) what gap or need motivated this survey, "
                    "(3) the key conclusions or open problems identified. "
                    "Be specific about the subfield (not just 'deep learning' but "
                    "'self-supervised learning for speech processing')."
                )
            },
            "limitations": {
                "type": "string",
                "description": (
                    "Scope limitations of this survey: what topics, time periods, languages, "
                    "or subtopics are explicitly excluded or not covered. "
                    "Also include any acknowledged biases in paper selection."
                )
            },
            "metrics_used": {
                "type": "object",
                "description": (
                    "If the survey includes quantitative comparison of methods, "
                    "list the metrics used for that comparison. "
                    "Key = metric name, Value = description. "
                    "Omit if the survey is purely qualitative."
                ),
                "additionalProperties": {"type": "string"}
            },
            "results": {
                "type": "object",
                "description": (
                    "If the survey reports comparative results across methods, "
                    "capture the key figures (e.g. {'best_accuracy_ImageNet': '91.1% (ViT-G/14)'}). "
                    "Omit if no quantitative comparisons are made."
                ),
                "additionalProperties": {"type": "string"}
            },

            # --- Survey-specific fields ---
            "papers_surveyed": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of the most important or frequently cited papers discussed in this survey. "
                    "Use the format 'Author et al. (YEAR) - Short title' "
                    "(e.g. 'Vaswani et al. (2017) - Attention Is All You Need'). "
                    "Include up to 20 of the most central works. "
                    "Do not list every reference — focus on landmark papers."
                )
            },
            "taxonomy": {
                "type": "object",
                "description": (
                    "The categorisation or taxonomy the authors use to organise the field. "
                    "Key = category name, Value = description of what falls in that category. "
                    "(e.g. {'discriminative models': 'Models trained with supervised labels', "
                    "'generative models': 'Models that learn data distributions'}). "
                    "Reflect the actual taxonomy structure used in the paper."
                ),
                "additionalProperties": {"type": "string"}
            },
            "research_gaps": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Open problems, underexplored areas, and future research directions "
                    "explicitly identified by the authors. "
                    "Each item should be a specific, actionable gap "
                    "(e.g. 'Few methods address low-resource multilingual settings', "
                    "'No established benchmark for evaluating robustness to distribution shift'). "
                    "Include 3-8 items."
                )
            },
            "time_period_covered": {
                "type": "string",
                "description": (
                    "The time range of papers included in this survey "
                    "(e.g. '2017-2023', 'up to March 2024', '2012-present'). "
                    "Extract from the paper's stated scope or infer from the earliest and "
                    "latest cited works."
                )
            }
        },
        "required": ["name", "authors"]
    }
}


THEORETICAL_TOOL = {
    "name": "extract_theoretical",
    "description": "Extract all structured metadata from a theoretical research paper.",
    "input_schema": {
        "type": "object",
        "properties": {

            # --- Base fields ---
            "name": {
                "type": "string",
                "description": "Full official title of the paper exactly as it appears in the document."
            },
            "authors": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Full names of all authors in order of appearance. "
                    "Do not abbreviate or use 'et al.'."
                )
            },
            "date_of_publication": {
                "type": "string",
                "description": (
                    "Publication date. Use YYYY-MM-DD, YYYY-MM, or YYYY depending on available precision."
                )
            },
            "doi": {
                "type": "string",
                "description": "Raw DOI string without https://doi.org/ prefix. Only if explicitly stated."
            },
            "link": {
                "type": "string",
                "description": "URL to the paper. Only if explicitly stated."
            },
            "code_link": {
                "type": "string",
                "description": "URL to any accompanying code or proof verification tools. Only if stated."
            },
            "key_insights": {
                "type": "string",
                "description": (
                    "2-4 sentences on: (1) what theoretical question or problem this paper addresses, "
                    "(2) the main theorem, result, or framework proposed, "
                    "(3) what the practical or theoretical implications are. "
                    "Use precise mathematical language where appropriate."
                )
            },
            "limitations": {
                "type": "string",
                "description": (
                    "Scope of the theoretical results: what assumptions are required for the theorems to hold, "
                    "what settings or regimes are excluded, "
                    "and what the authors acknowledge as open questions or extensions."
                )
            },
            "metrics_used": {
                "type": "object",
                "description": (
                    "If the paper includes empirical validation, list the metrics used. "
                    "For purely theoretical papers, use this for theoretical measures "
                    "(e.g. {'sample_complexity': 'Number of samples needed to achieve epsilon error', "
                    "'regret': 'Cumulative regret bound over T rounds'}). "
                    "Omit if not applicable."
                ),
                "additionalProperties": {"type": "string"}
            },
            "results": {
                "type": "object",
                "description": (
                    "Key quantitative results. For theoretical papers this may be complexity bounds "
                    "(e.g. {'sample_complexity': 'O(d log d / epsilon^2)', 'regret_bound': 'O(sqrt(T))'}). "
                    "For papers with experiments, include those results. "
                    "Omit if no quantitative results are stated."
                ),
                "additionalProperties": {"type": "string"}
            },

            # --- Theoretical-specific fields ---
            "propositions": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "The main theorems, lemmas, propositions, or corollaries proved or stated in the paper. "
                    "Each item should be a concise informal statement of what is proved "
                    "(e.g. 'Theorem 1: Under assumptions A1-A3, gradient descent converges to "
                    "a global minimum at rate O(1/T)', "
                    "'Lemma 2: The KL divergence between the variational posterior and the prior "
                    "is bounded by the ELBO'). "
                    "Include 3-8 most important results."
                )
            },
            "proofs_or_derivations": {
                "type": "string",
                "description": (
                    "Summary of the proof techniques or mathematical derivations used. "
                    "Include: what proof strategy is employed (induction, contradiction, "
                    "coupling argument, martingale theory etc.), "
                    "what mathematical tools are used (measure theory, information theory, "
                    "convex analysis, PAC-Bayes bounds etc.), "
                    "and what the key steps or insights in the proof are. "
                    "Write for a technically sophisticated reader."
                )
            },
            "assumptions": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Formal assumptions required for the theoretical results to hold. "
                    "Each item should be a specific assumption stated or implied in the paper "
                    "(e.g. 'Loss function is L-smooth and mu-strongly convex', "
                    "'Data is drawn i.i.d. from a fixed but unknown distribution', "
                    "'Model is overparameterised with more parameters than training samples'). "
                    "Include all assumptions that constrain the applicability of the results."
                )
            },
            "applicability": {
                "type": "string",
                "description": (
                    "Practical settings or problem classes where the theoretical results apply. "
                    "Include: what types of models, data distributions, or tasks the theory covers, "
                    "what scale or regime the results are relevant to, "
                    "and any practical implications or design principles that follow from the theory."
                )
            }
        },
        "required": ["name", "authors"]
    }
}


COMPARE_TOOL = {
    "name": "compare_papers",
    "description": "Generate a structured side-by-side comparison of multiple research papers.",
    "input_schema": {
        "type": "object",
        "properties": {
            "dimensions": {
                "type": "array",
                "description": (
                    "One object per comparison dimension. Each dimension compares all papers "
                    "on that specific aspect."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "dimension": {
                            "type": "string",
                            "description": "Name of the comparison dimension (e.g. 'Architecture', 'Dataset', 'F1 Score')"
                        },
                        "papers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "paper_id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "value": {
                                        "type": "string",
                                        "description": "Human-readable value for this paper on this dimension. Use 'N/A' if not applicable."
                                    },
                                    "numeric_value": {
                                        "type": "number",
                                        "description": "Numeric value if applicable (for chart rendering). Omit if not a number."
                                    }
                                },
                                "required": ["paper_id", "name", "value"]
                            }
                        }
                    },
                    "required": ["dimension", "papers"]
                }
            },
            "summary": {
                "type": "string",
                "description": (
                    "3-5 sentence objective summary of the most important differences and similarities "
                    "across these papers. Focus on what matters most for a researcher choosing between them."
                )
            },
            "key_differences": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "3-6 specific, factual statements about how these papers differ. "
                    "Each should be a complete sentence referencing specific papers by name "
                    "(e.g. 'Paper A uses a CNN backbone while Paper B uses a Vision Transformer, "
                    "resulting in 3x faster inference for Paper A'). "
                    "Focus on differences that matter for practitioners."
                )
            },
            "recommendation": {
                "type": "string",
                "description": (
                    "Practical guidance on which paper is best suited for which use case. "
                    "Be specific: name each paper and the scenario where it excels "
                    "(e.g. 'Choose Paper A for production systems requiring low latency; "
                    "choose Paper B if accuracy is the priority and compute is available; "
                    "Paper C is best if your data is unlabelled'). "
                    "Do not hedge — give a clear recommendation."
                )
            }
        },
        "required": ["dimensions", "summary", "key_differences", "recommendation"]
    }
}

# ---------------------------------------------------------------------------
# PUBLIC FUNCTIONS
# ---------------------------------------------------------------------------

def detect_paper_type(text: str) -> str:
    """
    First call: classify the paper as empirical, survey, or theoretical.
    Uses only the first 3000 chars (abstract + intro is enough).
    """
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=EXTRACTION_SYSTEM_PROMPT,
        tools=cast(list[ToolParam], [DETECT_TYPE_TOOL]),
        tool_choice={"type": "tool", "name": "classify_paper"},
        messages=cast(list[MessageParam], [{
            "role": "user",
            "content": (
                "Read the following text from the beginning of a research paper and classify it.\n\n"
                f"{text[:3000]}"
            )
        }])
    )
    for block in resp.content:
        if isinstance(block, ToolUseBlock):
            paper_type = block.input.get("paper_type", "empirical")  # type: ignore[union-attr]
            return str(paper_type)
    return "empirical"


def extract_paper(text: str, paper_type: str) -> dict[str, Any]:
    """
    Second call: extract all metadata fields for the detected paper type.
    System prompt is cached — only the paper text is sent fresh each call.
    Returns a dict ready to insert into MongoDB (excluding paper_id and dataset_ids).
    """
    tool_map = {
        "empirical": EMPIRICAL_TOOL,
        "survey": SURVEY_TOOL,
        "theoretical": THEORETICAL_TOOL,
    }
    tool = tool_map.get(paper_type, EMPIRICAL_TOOL)

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[{
            "type": "text",
            "text": EXTRACTION_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        tools=cast(list[ToolParam], [tool]),
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=cast(list[MessageParam], [{
            "role": "user",
            "content": (
                "Extract all available metadata from this research paper. "
                "Cover every field you can find evidence for. "
                "For fields with no evidence in the text, omit them.\n\n"
                f"{text[:15000]}"
            )
        }])
    )

    for block in resp.content:
        if isinstance(block, ToolUseBlock):
            return dict(block.input)  # type: ignore[arg-type]
    return {}


def ask_question(
    question: str,
    chunks: list[dict[str, Any]],
    history: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Answer a natural language question using retrieved paper chunks as context.
    Returns { answer, citations, latency_ms, tokens }.
    """
    if not chunks:
        return {
            "answer": "No relevant sections found in your library. Try uploading more papers or rephrasing your question.",
            "citations": [],
            "latency_ms": 0,
            "tokens": 0
        }

    context = "\n\n".join([
        f"[Paper: {c['paper_id']} | Section: {c['section']}]\n{c['text']}"
        for c in chunks
    ])

    messages: list[dict[str, Any]] = list(history)
    messages.append({
        "role": "user",
        "content": (
            f"Retrieved context from your paper library:\n\n{context}\n\n"
            f"---\n\nQuestion: {question}"
        )
    })

    start = time.time()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=ASK_SYSTEM_PROMPT,
        messages=cast(list[MessageParam], messages)
    )

    # Safe text extraction — only TextBlock has .text
    answer = ""
    for block in resp.content:
        if isinstance(block, TextBlock):
            answer = block.text
            break

    citations = [
        {
            "paper_id": c["paper_id"],
            "section": c["section"],
            "text": c["text"][:200]
        }
        for c in chunks
    ]

    return {
        "answer": answer,
        "citations": citations,
        "latency_ms": round((time.time() - start) * 1000),
        "tokens": resp.usage.input_tokens + resp.usage.output_tokens
    }


def ask_question_stream(
    question: str,
    chunks: list[dict[str, Any]],
    history: list[dict[str, Any]]
) -> Generator[str, None, str]:
    """
    Same as ask_question but streams the answer as SSE events.
    Yields strings formatted as 'data: {...}\\n\\n'.
    Returns the full answer text when done (via StopIteration value).
    """
    context = "\n\n".join([
        f"[Paper: {c['paper_id']} | Section: {c['section']}]\n{c['text']}"
        for c in chunks
    ])

    citations = [
        {"paper_id": c["paper_id"], "section": c["section"]}
        for c in chunks
    ]

    yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

    messages: list[dict[str, Any]] = list(history)
    messages.append({
        "role": "user",
        "content": (
            f"Retrieved context from your paper library:\n\n{context}\n\n"
            f"---\n\nQuestion: {question}"
        )
    })

    full_answer = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=ASK_SYSTEM_PROMPT,
        messages=cast(list[MessageParam], messages)
    ) as stream:
        for text in stream.text_stream:
            full_answer += text
            yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return full_answer


def compare_papers(paper_docs: list[dict[str, Any]], dimensions: list[str] | None = None) -> dict[str, Any]:
    """
    Generate a structured comparison across the given paper documents.
    paper_docs: list of MongoDB paper documents (with _id removed).
    dimensions: optional list of comparison axes. Defaults to the standard set.
    """
    default_dims = [
        "architecture",
        "key techniques",
        "training strategy",
        "datasets used",
        "metrics and results",
        "limitations",
        "key insights"
    ]
    dims = dimensions or default_dims

    paper_summaries = json.dumps([{
        "paper_id": p.get("paper_id"),
        "name": p.get("name", "Unknown"),
        "paper_type": p.get("paper_type"),
        "authors": p.get("authors", []),
        "date_of_publication": p.get("date_of_publication"),
        "architecture": p.get("architecture"),
        "key_techniques": p.get("key_techniques", []),
        "preprocessing": p.get("preprocessing"),
        "training_strategy": p.get("training_strategy"),
        "metrics_used": p.get("metrics_used", {}),
        "results": p.get("results", {}),
        "limitations": p.get("limitations"),
        "key_insights": p.get("key_insights"),
        # survey fields
        "papers_surveyed": p.get("papers_surveyed", []),
        "taxonomy": p.get("taxonomy"),
        "research_gaps": p.get("research_gaps", []),
        "time_period_covered": p.get("time_period_covered"),
        # theoretical fields
        "propositions": p.get("propositions", []),
        "assumptions": p.get("assumptions", []),
        "applicability": p.get("applicability"),
    } for p in paper_docs], indent=2)

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=COMPARE_SYSTEM_PROMPT,
        tools=cast(list[ToolParam], [COMPARE_TOOL]),
        tool_choice={"type": "tool", "name": "compare_papers"},
        messages=cast(list[MessageParam], [{
            "role": "user",
            "content": (
                f"Compare the following {len(paper_docs)} papers across these dimensions: "
                f"{', '.join(dims)}.\n\n"
                f"Paper data:\n{paper_summaries}"
            )
        }])
    )

    for block in resp.content:
        if isinstance(block, ToolUseBlock):
            return dict(block.input)  # type: ignore[arg-type]

    return {"error": "Comparison failed — no tool use block returned"}