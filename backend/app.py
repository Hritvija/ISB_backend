# -*- coding: utf-8 -*-
"""
Created on Mon May 19 14:36:30 2025

@author: singh
"""
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
from llama_cpp import Llama

# === Paths ===
DB_PATH = "C:\\Users\\singh\\.spyder-py3\\survey_isb.db"
MODEL_PATH = "D:/gguf/codellama-nl2sql.Q4_K_M.gguf"  # <--- Your merged model

# === Load LLM ===
llm = Llama(model_path=MODEL_PATH, n_ctx=2048, n_threads=12)

# === App Init ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Schema Model ===
class NLQuery(BaseModel):
    query: str

# === Utility: Get DB schema ===
def get_schema():
    schema = ""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    for (table,) in tables:
        schema += f"Table: {table}\n"
        cursor.execute(f"PRAGMA table_info({table});")
        for col in cursor.fetchall():
            col_name, col_type, notnull = col[1], col[2], col[3]
            nullable = "NULLABLE" if notnull == 0 else "NOT NULL"
            schema += f"    {col_name} ({col_type}, {nullable})\n"
        schema += "\n"
    conn.close()
    return schema

# === Utility: Generate SQL ===
def generate_sql(nl_query, schema):
    context = f"""You are an expert SQLite analyst. Use this schema:

{schema}

Only generate valid SELECT SQLite queries. No MySQL/Postgres syntax allowed.\n"""
    prompt = context + f"\nUser query: {nl_query}\nSQLite query:"
    output = llm(prompt, max_tokens=512, stop=["###"])
    text = output["choices"][0]["text"].strip()
    sql = text.split(";")[0].strip() + ";"
    if not sql.lower().startswith("select"):
        raise ValueError("Generated SQL is not a SELECT statement.")
    return sql

# === Endpoint: NL to SQL ===
@app.post("/query")
def nl2sql(req: NLQuery):
    schema = get_schema()
    try:
        sql = generate_sql(req.query, schema)
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return {"sql": sql, "data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

