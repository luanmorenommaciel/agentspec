#!/usr/bin/env bash
# =============================================================================
# init-workspace.sh — AgentSpec Workspace Initializer
#
# Creates SDD workspace directories and detects project stack at session
# start. Runs on SessionStart — idempotent, silent on success.
#
# Prerequisites:
#   - bash 3.2+ (uses ${BASH_SOURCE} and mapfile-free patterns)
#   - Standard POSIX utilities: mkdir, cat
#   - Called with the project working directory as CWD
#
# Usage:
#   ./init-workspace.sh          # normal run (SessionStart hook)
#   ./init-workspace.sh --help   # show this help
#
# Behavior:
#   - No-ops unless the CWD looks like an AgentSpec-aware project
#     (has .git/, CLAUDE.md, or .claude/)
#   - Creates .claude/sdd/{features,reports,archive}/ if missing
#   - Writes .claude/sdd/.detected-stack.md with inferred tech-stack hints
# =============================================================================

set -euo pipefail

# Parse --help early, before side effects
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    sed -n '3,22p' "$0"
    exit 0
fi

# ---------------------------------------------------------------------------
# Phase 1: Workspace Initialization (existing behavior)
# ---------------------------------------------------------------------------

init_workspace() {
    if [[ -d ".git" ]] || [[ -f "CLAUDE.md" ]] || [[ -d ".claude" ]]; then
        mkdir -p .claude/sdd/features || true
        mkdir -p .claude/sdd/reports  || true
        mkdir -p .claude/sdd/archive  || true
    fi
}

# ---------------------------------------------------------------------------
# Phase 2: Project Stack Detection
# ---------------------------------------------------------------------------

detect_project_stack() {
    local -a detected_techs=()
    local -a kb_domains=()
    local -a agents=()
    local -a commands=()

    # --- dbt ---
    if [[ -f "dbt_project.yml" ]] || [[ -f "profiles.yml" ]]; then
        detected_techs+=("dbt")
        kb_domains+=("dbt/ -- model types, incremental strategies, testing")
        kb_domains+=("sql-patterns/ -- window functions, CTEs, optimization")
        agents+=("dbt-specialist -- dbt model development")
        agents+=("sql-optimizer -- query performance")
        agents+=("schema-designer -- dimensional modeling")
        commands+=("/schema -- design star schema")
        commands+=("/sql-review -- review SQL code")
        commands+=("/data-quality -- generate quality checks")

        if [[ -f "profiles.yml" ]]; then
            if grep -q "snowflake" profiles.yml 2>/dev/null; then
                detected_techs+=("Snowflake (profiles.yml target)")
                kb_domains+=("cloud-platforms/ -- Snowflake, Databricks, BigQuery")
            fi
            if grep -q "bigquery" profiles.yml 2>/dev/null; then
                detected_techs+=("BigQuery (profiles.yml target)")
                kb_domains+=("gcp/ -- Cloud Run, Pub/Sub, BigQuery")
                kb_domains+=("cloud-platforms/ -- Snowflake, Databricks, BigQuery")
            fi
            if grep -q "databricks" profiles.yml 2>/dev/null; then
                detected_techs+=("Databricks (profiles.yml target)")
                kb_domains+=("cloud-platforms/ -- Snowflake, Databricks, BigQuery")
                kb_domains+=("lakehouse/ -- Iceberg, Delta, catalogs")
            fi
        fi
    fi

    # --- Lakeflow / Databricks ---
    if [[ -f "databricks.yml" ]] || compgen -G "**/bronze.py" >/dev/null 2>&1 || compgen -G "**/silver.py" >/dev/null 2>&1; then
        detected_techs+=("Databricks Lakeflow")
        kb_domains+=("lakeflow/ -- DLT pipelines, expectations, streaming tables")
        kb_domains+=("medallion/ -- Bronze/Silver/Gold architecture")
        kb_domains+=("lakehouse/ -- Iceberg, Delta, catalogs")
        agents+=("lakeflow-specialist -- DLT pipeline development")
        agents+=("lakeflow-architect -- Lakeflow design patterns")
        agents+=("medallion-architect -- medallion layer design")
        commands+=("/pipeline -- DAG/pipeline scaffolding")
        commands+=("/lakehouse -- table format and catalog guidance")
    fi

    # --- AWS Lambda (SAM) ---
    if [[ -f "template.yaml" ]] && [[ -f "samconfig.toml" ]]; then
        detected_techs+=("AWS Lambda (SAM)")
        kb_domains+=("aws/ -- Lambda, S3, Glue, SAM")
        agents+=("aws-lambda-architect -- Lambda design")
        agents+=("lambda-builder -- Lambda implementation")
        agents+=("aws-deployer -- SAM deployment")
        commands+=("/pipeline -- DAG/pipeline scaffolding")
    fi

    # --- Airflow ---
    if [[ -d "dags" ]] || [[ -f "airflow.cfg" ]] || [[ -d "airflow" ]]; then
        detected_techs+=("Apache Airflow")
        kb_domains+=("airflow/ -- DAG design, operators, TaskFlow API")
        agents+=("airflow-specialist -- DAG development")
        agents+=("pipeline-architect -- orchestration design")
        commands+=("/pipeline -- DAG/pipeline scaffolding")
    fi

    # --- Supabase ---
    if [[ -f "docker-compose.yml" ]] && grep -q "supabase" docker-compose.yml 2>/dev/null; then
        detected_techs+=("Supabase")
        kb_domains+=("supabase/ -- Auth, Edge Functions, Realtime, RLS")
        agents+=("supabase-specialist -- Supabase development")
    fi

    # --- Terraform / IaC ---
    if compgen -G "*.tf" >/dev/null 2>&1; then
        detected_techs+=("Terraform")
        kb_domains+=("terraform/ -- IaC modules, state, workspaces")
        agents+=("data-platform-engineer -- infrastructure design")
        commands+=("/pipeline -- infrastructure pipeline scaffolding")
    fi

    # --- Spark ---
    if [[ -f "pyproject.toml" ]] && grep -q "pyspark" pyproject.toml 2>/dev/null; then
        detected_techs+=("PySpark (pyproject.toml)")
        kb_domains+=("spark/ -- DataFrames, performance, Delta integration")
        agents+=("spark-engineer -- Spark job development")
        agents+=("spark-specialist -- Spark architecture")
        agents+=("spark-performance-analyzer -- Spark tuning")
        commands+=("/pipeline -- pipeline scaffolding")
    elif [[ -f "setup.py" ]] && grep -q "pyspark" setup.py 2>/dev/null; then
        detected_techs+=("PySpark (setup.py)")
        kb_domains+=("spark/ -- DataFrames, performance, Delta integration")
        agents+=("spark-engineer -- Spark job development")
        agents+=("spark-specialist -- Spark architecture")
        agents+=("spark-performance-analyzer -- Spark tuning")
        commands+=("/pipeline -- pipeline scaffolding")
    fi

    # --- Streaming ---
    if [[ -d "streaming" ]] || compgen -G "**/kafka*.properties" >/dev/null 2>&1 || compgen -G "**/kafka*.yml" >/dev/null 2>&1 || compgen -G "**/kafka*.yaml" >/dev/null 2>&1; then
        detected_techs+=("Streaming / Kafka")
        kb_domains+=("streaming/ -- Flink, Kafka, Spark Streaming, CDC")
        agents+=("streaming-engineer -- stream processing")
        agents+=("spark-streaming-architect -- Spark Streaming design")
        commands+=("/pipeline -- streaming pipeline scaffolding")
    fi

    # --- Microsoft Fabric ---
    if [[ -d "Fabric" ]] || compgen -G "*.pbix" >/dev/null 2>&1; then
        detected_techs+=("Microsoft Fabric")
        kb_domains+=("microsoft-fabric/ -- Lakehouse, Warehouse, Pipelines")
        agents+=("fabric-architect -- Fabric architecture")
        agents+=("fabric-pipeline-developer -- Fabric pipelines")
        commands+=("/pipeline -- Fabric pipeline scaffolding")
    fi

    # --- Data Quality ---
    local dq_found=false
    if [[ -f "requirements.txt" ]]; then
        if grep -qE "great.expectations|soda" requirements.txt 2>/dev/null; then
            dq_found=true
        fi
    fi
    if [[ -f "pyproject.toml" ]]; then
        if grep -qE "great.expectations|soda" pyproject.toml 2>/dev/null; then
            dq_found=true
        fi
    fi
    if [[ "$dq_found" == "true" ]]; then
        detected_techs+=("Data Quality (Great Expectations / Soda)")
        kb_domains+=("data-quality/ -- expectations, validation, observability")
        agents+=("data-quality-analyst -- quality checks")
        agents+=("data-contracts-engineer -- data contracts")
        commands+=("/data-quality -- generate quality checks")
        commands+=("/data-contract -- contract authoring")
    fi

    # --- Always-useful additions based on Python projects ---
    if [[ -f "pyproject.toml" ]] || [[ -f "setup.py" ]] || [[ -f "requirements.txt" ]]; then
        if [[ -f "pyproject.toml" ]] && grep -qE "pydantic" pyproject.toml 2>/dev/null; then
            detected_techs+=("Pydantic")
            kb_domains+=("pydantic/ -- validation, LLM output schemas")
        fi
        if [[ -f "requirements.txt" ]] && grep -qE "pydantic" requirements.txt 2>/dev/null; then
            detected_techs+=("Pydantic")
            kb_domains+=("pydantic/ -- validation, LLM output schemas")
        fi
    fi

    # Return results via global arrays
    DETECTED_TECHS=("${detected_techs[@]+"${detected_techs[@]}"}")
    KB_DOMAINS=("${kb_domains[@]+"${kb_domains[@]}"}")
    AGENTS=("${agents[@]+"${agents[@]}"}")
    COMMANDS=("${commands[@]+"${commands[@]}"}")
}

# ---------------------------------------------------------------------------
# Phase 3: Generate Context Hint File
# ---------------------------------------------------------------------------

generate_context_hint() {
    local output_file=".claude/sdd/.detected-stack.md"

    detect_project_stack

    # If nothing detected, skip file generation
    if [[ ${#DETECTED_TECHS[@]} -eq 0 ]]; then
        # Remove stale file from a previous session if it exists
        rm -f "$output_file" 2>/dev/null || true
        return 0
    fi

    mkdir -p .claude/sdd

    # Deduplicate arrays (preserving order)
    local -a unique_kb=()
    local -A seen_kb=()
    for item in "${KB_DOMAINS[@]}"; do
        if [[ -z "${seen_kb[$item]+x}" ]]; then
            seen_kb[$item]=1
            unique_kb+=("$item")
        fi
    done

    local -a unique_agents=()
    local -A seen_agents=()
    for item in "${AGENTS[@]}"; do
        if [[ -z "${seen_agents[$item]+x}" ]]; then
            seen_agents[$item]=1
            unique_agents+=("$item")
        fi
    done

    local -a unique_cmds=()
    local -A seen_cmds=()
    for item in "${COMMANDS[@]}"; do
        local cmd_key="${item%% -- *}"
        if [[ -z "${seen_cmds[$cmd_key]+x}" ]]; then
            seen_cmds[$cmd_key]=1
            unique_cmds+=("$item")
        fi
    done

    # Write the file
    {
        echo "# Detected Project Stack"
        echo ""
        echo "> Auto-generated by AgentSpec on $(date +%Y-%m-%d). Do not edit manually."
        echo ""
        echo "## Technologies Found"
        for tech in "${DETECTED_TECHS[@]}"; do
            echo "- ${tech}"
        done
        echo ""
        echo "## Recommended KB Domains"
        for domain in "${unique_kb[@]}"; do
            echo "- \`${domain}\`"
        done
        echo ""
        echo "## Recommended Agents"
        for agent in "${unique_agents[@]}"; do
            echo "- \`${agent}\`"
        done
        echo ""
        echo "## Quick Commands"
        for cmd in "${unique_cmds[@]}"; do
            echo "- \`${cmd}\`"
        done
    } > "$output_file"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

init_workspace
generate_context_hint
