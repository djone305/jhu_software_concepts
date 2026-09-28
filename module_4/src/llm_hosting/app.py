from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

from flask import Flask, jsonify, request
from huggingface_hub import hf_hub_download
from llama_cpp import Llama


# ============================================================
# Flask application
# ============================================================

app = Flask(__name__)


# ============================================================
# Model configuration
# ============================================================

MODEL_REPO = os.getenv(
    "MODEL_REPO",
    "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
)

MODEL_FILE = os.getenv(
    "MODEL_FILE",
    "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
)

N_THREADS = int(
    os.getenv(
        "N_THREADS",
        str(os.cpu_count() or 2)
    )
)

N_CTX = int(
    os.getenv(
        "N_CTX",
        "2048"
    )
)

N_GPU_LAYERS = int(
    os.getenv(
        "N_GPU_LAYERS",
        "0"
    )
)

CANON_UNIS_PATH = os.getenv(
    "CANON_UNIS_PATH",
    "canon_universities.txt"
)

CANON_PROGS_PATH = os.getenv(
    "CANON_PROGS_PATH",
    "canon_programs.txt"
)


# ============================================================
# JSON extraction
# ============================================================

JSON_OBJ_RE = re.compile(
    r"\{.*?\}",
    re.DOTALL
)


# ============================================================
# Canonical lists
# ============================================================

def _read_lines(
    path: str
) -> List[str]:

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return [
                line.strip()
                for line in f
                if line.strip()
            ]

    except FileNotFoundError:

        return []


CANON_UNIS = _read_lines(
    CANON_UNIS_PATH
)

CANON_PROGS = _read_lines(
    CANON_PROGS_PATH
)


# ============================================================
# University abbreviations and corrections
# ============================================================

ABBREV_UNI: Dict[str, str] = {

    r"(?i)^mcg(?:\.|ill)?$":
        "McGill University",

    r"(?i)^(ubc|u\.?b\.?c\.?)$":
        "University of British Columbia",

    r"(?i)^uoft$":
        "University of Toronto",
}


COMMON_UNI_FIXES: Dict[str, str] = {

    "McGiill University":
        "McGill University",

    "Mcgill University":
        "McGill University",

    "University Of British Columbia":
        "University of British Columbia",
}


COMMON_PROG_FIXES: Dict[str, str] = {

    "Mathematic":
        "Mathematics",

    "Info Studies":
        "Information Studies",
}


# ============================================================
# LLM prompt
# ============================================================

SYSTEM_PROMPT = (
    "You are a data cleaning assistant. "
    "Standardize degree program and university names.\n\n"

    "Rules:\n"

    "- Input provides a single string under key "
    "\"program\" that may contain both program and university.\n"

    "- Split into program name and university name.\n"

    "- Trim extra spaces and commas.\n"

    "- Expand obvious abbreviations such as "
    "\"McG\" to \"McGill University\" and "
    "\"UBC\" to \"University of British Columbia\".\n"

    "- Use Title Case for program names.\n"

    "- Use official capitalization for university names.\n"

    "- Correct obvious spelling errors.\n"

    "- If university cannot be inferred, return \"Unknown\".\n\n"

    "Return JSON ONLY with keys:\n"

    "standardized_program, standardized_university\n"
)


FEW_SHOTS: List[
    Tuple[
        Dict[str, str],
        Dict[str, str]
    ]
] = [

    (
        {
            "program":
                "Information Studies, McGill University"
        },
        {
            "standardized_program":
                "Information Studies",

            "standardized_university":
                "McGill University",
        },
    ),

    (
        {
            "program":
                "Information, McG"
        },
        {
            "standardized_program":
                "Information Studies",

            "standardized_university":
                "McGill University",
        },
    ),

    (
        {
            "program":
                "Mathematics, University Of British Columbia"
        },
        {
            "standardized_program":
                "Mathematics",

            "standardized_university":
                "University of British Columbia",
        },
    ),
]


# ============================================================
# LLM instance
# ============================================================

_LLM: Llama | None = None


def _load_llm() -> Llama:

    global _LLM

    if _LLM is not None:
        return _LLM

    print(
        "Loading TinyLlama model..."
    )

    print(
        f"Model repository: {MODEL_REPO}"
    )

    print(
        f"Model file: {MODEL_FILE}"
    )

    print(
        f"GPU layers: {N_GPU_LAYERS}"
    )

    model_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
        local_dir="models",
    )

    print(
        f"Model downloaded to: {model_path}"
    )

    _LLM = Llama(
        model_path=model_path,
        n_ctx=N_CTX,
        n_threads=N_THREADS,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False,
    )

    print(
        "LLM loaded successfully."
    )

    return _LLM


# ============================================================
# Fallback parser
# ============================================================

def _split_fallback(
    text: str
) -> Tuple[str, str]:

    s = re.sub(
        r"\s+",
        " ",
        (text or "")
    ).strip().strip(",")

    parts = [
        p.strip()
        for p in re.split(
            r",| at | @ ",
            s,
            flags=re.IGNORECASE
        )
        if p.strip()
    ]

    prog = (
        parts[0]
        if parts
        else ""
    )

    uni = (
        parts[1]
        if len(parts) > 1
        else ""
    )

    # McGill
    if re.fullmatch(
        r"(?i)mcg(?:ill)?\.?",
        uni or ""
    ):

        uni = "McGill University"

    # UBC
    if re.fullmatch(
        r"(?i)(ubc|u\.?b\.?c\.?|university of british columbia)",
        uni or ""
    ):

        uni = "University of British Columbia"

    prog = prog.title()

    if uni:

        uni = re.sub(
            r"\bOf\b",
            "of",
            uni.title()
        )

    else:

        uni = "Unknown"

    return prog, uni


# ============================================================
# Fuzzy matching
# ============================================================

def _best_match(
    name: str,
    candidates: List[str],
    cutoff: float = 0.86
) -> str | None:

    if not name or not candidates:
        return None

    matches = difflib.get_close_matches(
        name,
        candidates,
        n=1,
        cutoff=cutoff
    )

    return (
        matches[0]
        if matches
        else None
    )


# ============================================================
# Program normalization
# ============================================================

def _post_normalize_program(
    prog: str
) -> str:

    p = (
        prog or ""
    ).strip()

    p = COMMON_PROG_FIXES.get(
        p,
        p
    )

    p = p.title()

    if p in CANON_PROGS:
        return p

    match = _best_match(
        p,
        CANON_PROGS,
        cutoff=0.84
    )

    return match or p


# ============================================================
# University normalization
# ============================================================

def _post_normalize_university(
    uni: str
) -> str:

    u = (
        uni or ""
    ).strip()

    # Abbreviations
    for pattern, full_name in ABBREV_UNI.items():

        if re.fullmatch(
            pattern,
            u
        ):

            u = full_name
            break

    # Common spelling corrections
    u = COMMON_UNI_FIXES.get(
        u,
        u
    )

    # Capitalization
    if u:

        u = re.sub(
            r"\bOf\b",
            "of",
            u.title()
        )

    # Canonical match
    if u in CANON_UNIS:
        return u

    match = _best_match(
        u,
        CANON_UNIS,
        cutoff=0.86
    )

    return (
        match
        or u
        or "Unknown"
    )


# ============================================================
# Call the LLM
# ============================================================

def _call_llm(
    program_text: str
) -> Dict[str, str]:

    llm = _load_llm()

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    # Few-shot examples
    for x_in, x_out in FEW_SHOTS:

        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    x_in,
                    ensure_ascii=False
                ),
            }
        )

        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(
                    x_out,
                    ensure_ascii=False
                ),
            }
        )

    # Actual request
    messages.append(
        {
            "role": "user",
            "content": json.dumps(
                {
                    "program":
                        program_text
                },
                ensure_ascii=False
            ),
        }
    )

    output = llm.create_chat_completion(
        messages=messages,
        temperature=0.0,
        max_tokens=128,
        top_p=1.0,
    )

    text = (
        output["choices"][0]["message"]["content"]
        or ""
    ).strip()

    try:

        match = JSON_OBJ_RE.search(
            text
        )

        obj = json.loads(
            match.group(0)
            if match
            else text
        )

        standardized_program = str(
            obj.get(
                "standardized_program",
                ""
            )
        ).strip()

        standardized_university = str(
            obj.get(
                "standardized_university",
                ""
            )
        ).strip()

    except Exception:

        (
            standardized_program,
            standardized_university
        ) = _split_fallback(
            program_text
        )

    standardized_program = (
        _post_normalize_program(
            standardized_program
        )
    )

    standardized_university = (
        _post_normalize_university(
            standardized_university
        )
    )

    return {
        "standardized_program":
            standardized_program,

        "standardized_university":
            standardized_university,
    }


# ============================================================
# Input normalization
# ============================================================

def _normalize_input(
    payload: Any
) -> List[Dict[str, Any]]:

    if isinstance(
        payload,
        list
    ):

        return payload

    if (
        isinstance(
            payload,
            dict
        )
        and isinstance(
            payload.get("rows"),
            list
        )
    ):

        return payload["rows"]

    # Also accept one individual record.
    if isinstance(
        payload,
        dict
    ):

        return [payload]

    return []


# ============================================================
# Health endpoint
# ============================================================

@app.get("/health")
def health() -> Any:

    return jsonify(
        {
            "ok": True,
            "model_loaded":
                _LLM is not None,
        }
    )


# ============================================================
# Standardization endpoint
# ============================================================

@app.post("/standardize")
def standardize() -> Any:

    payload = request.get_json(
        force=True,
        silent=True
    )

    rows = _normalize_input(
        payload
    )

    output_rows = []

    for row in rows:

        if not isinstance(
            row,
            dict
        ):
            continue

        # Accept the format sent by clean.py.
        program_text = (
            row.get("program")
            or row.get("Program Name")
            or ""
        )

        result = _call_llm(
            program_text
        )

        # These are the field names specified by your
        # original LLM-hosting project.
        row[
            "llm-generated-program"
        ] = result[
            "standardized_program"
        ]

        row[
            "llm-generated-university"
        ] = result[
            "standardized_university"
        ]

        output_rows.append(
            row
        )

    return jsonify(
        {
            "rows": output_rows
        }
    )


# ============================================================
# CLI mode
# ============================================================

def _cli_process_file(
    in_path: str,
    out_path: str | None,
    append: bool,
    to_stdout: bool,
) -> None:

    with open(
        in_path,
        "r",
        encoding="utf-8"
    ) as f:

        rows = _normalize_input(
            json.load(f)
        )

    sink = (
        sys.stdout
        if to_stdout
        else None
    )

    if not to_stdout:

        out_path = (
            out_path
            or (in_path + ".jsonl")
        )

        mode = (
            "a"
            if append
            else "w"
        )

        sink = open(
            out_path,
            mode,
            encoding="utf-8"
        )

    assert sink is not None

    try:

        for row in rows:

            program_text = (
                row.get("program")
                or row.get("Program Name")
                or ""
            )

            result = _call_llm(
                program_text
            )

            row[
                "llm-generated-program"
            ] = result[
                "standardized_program"
            ]

            row[
                "llm-generated-university"
            ] = result[
                "standardized_university"
            ]

            json.dump(
                row,
                sink,
                ensure_ascii=False
            )

            sink.write("\n")
            sink.flush()

    finally:

        if sink is not sys.stdout:
            sink.close()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Standardize program/university "
            "with a tiny local LLM."
        )
    )

    parser.add_argument(
        "--file",
        help=(
            "Path to JSON input "
            "(list of rows or {'rows': [...]})"
        ),
        default=None,
    )

    parser.add_argument(
        "--serve",
        action="store_true",
        help=(
            "Run the HTTP server "
            "instead of CLI."
        ),
    )

    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Output path for JSON Lines."
        ),
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help=(
            "Append to output instead "
            "of overwriting."
        ),
    )

    parser.add_argument(
        "--stdout",
        action="store_true",
        help=(
            "Write JSON Lines to stdout."
        ),
    )

    args = parser.parse_args()

    if args.serve or args.file is None:

        # Load the model before starting Flask so that
        # model-loading errors appear immediately.
        _load_llm()

        port = int(
            os.getenv(
                "PORT",
                "8000"
            )
        )

        print(
            f"Starting LLM API on port {port}..."
        )

        app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            threaded=False,
        )

    else:

        _cli_process_file(
            in_path=args.file,
            out_path=args.out,
            append=bool(args.append),
            to_stdout=bool(args.stdout),
        )