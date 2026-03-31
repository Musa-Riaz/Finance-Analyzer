from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


@dataclass
class TenantContext:
    user_id: str
    household_id: str
    account_id: str


def is_db_enabled() -> bool:
    return bool(os.getenv("DATABASE_URL")) and psycopg is not None


def _connect():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for DB-native mode")
    if psycopg is None:
        raise RuntimeError("psycopg is not installed")
    return psycopg.connect(database_url)


def _get_or_create_tenant_context(conn) -> TenantContext:
    demo_email = os.getenv("DEMO_USER_EMAIL", "demo@finance-analyzer.local")
    demo_household = os.getenv("DEMO_HOUSEHOLD_NAME", "Personal Finance")
    demo_account = os.getenv("DEMO_ACCOUNT_NAME", "Primary Account")

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (demo_email,))
        row = cur.fetchone()
        if row:
            user_id = row[0]
        else:
            cur.execute(
                "INSERT INTO users (email, display_name) VALUES (%s, %s) RETURNING id",
                (demo_email, "Demo User"),
            )
            user_id = cur.fetchone()[0]

        cur.execute(
            """
            SELECT hm.household_id, hm.role
            FROM household_members hm
            WHERE hm.user_id = %s
            ORDER BY hm.joined_at ASC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            household_id = row[0]
        else:
            cur.execute(
                "INSERT INTO households (name) VALUES (%s) RETURNING id",
                (demo_household,),
            )
            household_id = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO household_members (household_id, user_id, role)
                VALUES (%s, %s, 'owner')
                ON CONFLICT (household_id, user_id) DO NOTHING
                """,
                (household_id, user_id),
            )

        cur.execute(
            """
            SELECT id
            FROM accounts
            WHERE household_id = %s
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (household_id,),
        )
        row = cur.fetchone()
        if row:
            account_id = row[0]
        else:
            cur.execute(
                """
                INSERT INTO accounts (household_id, account_name, account_type)
                VALUES (%s, %s, 'bank')
                RETURNING id
                """,
                (household_id, demo_account),
            )
            account_id = cur.fetchone()[0]

    return TenantContext(user_id=user_id, household_id=household_id, account_id=account_id)


def _stable_row_id(row: pd.Series) -> str:
    canonical = "|".join(
        [
            row["timestamp"].isoformat(),
            str(row.get("description", "")),
            f"{float(row.get('amount', 0.0)):.2f}",
            str(row.get("type", "")),
            f"{float(row.get('balance', 0.0)):.2f}",
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:40]


def _category_kind_for_direction(direction: str) -> str:
    return "income" if direction == "IN" else "expense"


def persist_processed_dataframe(df: pd.DataFrame, source_label: str) -> None:
    if not is_db_enabled() or len(df) == 0:
        return

    copy_df = df.copy()
    copy_df["timestamp"] = pd.to_datetime(copy_df["timestamp"])
    payload_hash = hashlib.sha256(
        copy_df[["timestamp", "description", "amount", "direction"]]
        .astype(str)
        .to_json(orient="records")
        .encode("utf-8")
    ).hexdigest()

    with _connect() as conn:
        tenant = _get_or_create_tenant_context(conn)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO statement_uploads (
                    household_id,
                    account_id,
                    uploaded_by_user_id,
                    file_name,
                    file_hash,
                    status,
                    imported_rows,
                    processed_at
                )
                VALUES (%s, %s, %s, %s, %s, 'completed', %s, %s)
                ON CONFLICT (account_id, file_hash)
                DO UPDATE SET processed_at = EXCLUDED.processed_at
                RETURNING id
                """,
                (
                    tenant.household_id,
                    tenant.account_id,
                    tenant.user_id,
                    source_label,
                    payload_hash,
                    len(copy_df),
                    datetime.now(timezone.utc),
                ),
            )
            upload_id = cur.fetchone()[0]

            categories_by_name: dict[str, str] = {}
            category_rows = (
                copy_df[["category", "direction"]]
                .dropna(subset=["category"])
                .drop_duplicates()
            )
            for _, category_row in category_rows.iterrows():
                category_name = str(category_row["category"])
                category_kind = _category_kind_for_direction(str(category_row["direction"]))
                cur.execute(
                    """
                    INSERT INTO categories (household_id, name, kind)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (household_id, name)
                    DO UPDATE SET kind = EXCLUDED.kind, updated_at = NOW()
                    RETURNING id
                    """,
                    (tenant.household_id, category_name, category_kind),
                )
                categories_by_name[category_name] = cur.fetchone()[0]

            for _, row in copy_df.iterrows():
                external_id = _stable_row_id(row)
                category_id = categories_by_name.get(str(row.get("category")))
                raw_payload: dict[str, Any] = {
                    "month": row.get("month"),
                    "month_label": row.get("month_label"),
                    "source_type": row.get("type"),
                }

                cur.execute(
                    """
                    INSERT INTO transactions (
                        household_id,
                        account_id,
                        upload_id,
                        external_transaction_id,
                        occurred_at,
                        description,
                        normalized_description,
                        source_type,
                        amount,
                        balance,
                        direction,
                        raw_payload,
                        category_id
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s
                    )
                    ON CONFLICT (account_id, external_transaction_id)
                    DO NOTHING
                    RETURNING id
                    """,
                    (
                        tenant.household_id,
                        tenant.account_id,
                        upload_id,
                        external_id,
                        row["timestamp"].to_pydatetime(),
                        str(row.get("description", "")),
                        str(row.get("description", "")).lower(),
                        str(row.get("type", "")) or None,
                        float(row.get("amount", 0.0)),
                        float(row.get("balance", 0.0))
                        if pd.notna(row.get("balance"))
                        else None,
                        str(row.get("direction", "OUT")),
                        json.dumps(raw_payload),
                        category_id,
                    ),
                )

                inserted = cur.fetchone()
                if not inserted:
                    continue

                transaction_id = inserted[0]
                cur.execute(
                    """
                    INSERT INTO transaction_enrichments (
                        transaction_id,
                        anomaly_score,
                        is_anomaly,
                        anomaly_reason,
                        model_version,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (transaction_id)
                    DO UPDATE SET
                        anomaly_score = EXCLUDED.anomaly_score,
                        is_anomaly = EXCLUDED.is_anomaly,
                        anomaly_reason = EXCLUDED.anomaly_reason,
                        model_version = EXCLUDED.model_version,
                        updated_at = NOW()
                    """,
                    (
                        transaction_id,
                        float(row.get("anomaly_score", 0.0))
                        if pd.notna(row.get("anomaly_score"))
                        else None,
                        bool(row.get("is_anomaly", False)),
                        str(row.get("reason", "")) or None,
                        "python-ml-v1",
                    ),
                )

        conn.commit()


def load_processed_dataframe() -> pd.DataFrame | None:
    if not is_db_enabled():
        return None

    with _connect() as conn:
        tenant = _get_or_create_tenant_context(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.occurred_at,
                    t.description,
                    t.amount::float8,
                    t.direction::text,
                    COALESCE(c.name, 'Uncategorized') AS category,
                    COALESCE(e.is_anomaly, false) AS is_anomaly,
                    e.anomaly_score::float8,
                    COALESCE(t.source_type, '') AS source_type
                FROM transactions t
                LEFT JOIN transaction_enrichments e
                    ON e.transaction_id = t.id
                LEFT JOIN categories c
                    ON c.id = t.category_id
                WHERE t.account_id = %s
                  AND t.is_archived = false
                ORDER BY t.occurred_at ASC
                """,
                (tenant.account_id,),
            )
            rows = cur.fetchall()

    if not rows:
        return None

    df = pd.DataFrame(
        rows,
        columns=[
            "timestamp",
            "description",
            "amount",
            "direction",
            "category",
            "is_anomaly",
            "anomaly_score",
            "type",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_localize(None)
    df["amount"] = df["amount"].astype(float)
    df["direction"] = df["direction"].astype(str)
    df["is_anomaly"] = df["is_anomaly"].fillna(False).astype(bool)
    df["anomaly_score"] = pd.to_numeric(df["anomaly_score"], errors="coerce")
    df["date"] = df["timestamp"].dt.date
    df["month"] = df["timestamp"].dt.strftime("%Y-%m")
    df["month_label"] = df["timestamp"].dt.strftime("%b %Y")
    return df
