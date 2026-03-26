import os
import sqlite3
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), 'o2c.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.txt')

if os.path.exists(SCHEMA_PATH):
    with open(SCHEMA_PATH, 'r') as f:
        SCHEMA_TEXT = f.read()
else:
    SCHEMA_TEXT = "Schema not found."

class QueryRequest(BaseModel):
    messages: list

def execute_sql(query: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        # Cap results to avoid huge context limits, 50 rows is plenty for these examples
        if len(df) > 50:
            df = df.head(50)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

def extract_related_graph(context_ids, fetch_all=False):
    nodes = []
    edges = []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    def add_node(nid, label, group, props=None, title=None):
        if not any(n['id'] == nid for n in nodes):
            nodes.append({"id": nid, "label": label, "group": group, "title": title or label, "properties": props or {}})
            
    def add_edge(source, target, label, title=None):
        if not any(e['source'] == source and e['target'] == target and e['label'] == label for e in edges):
            edges.append({"source": source, "target": target, "label": label, "title": title or label})

    def format_tooltip(name, row):
        lines = [name, f"Entity: {name}"]
        c = 0
        for k, v in row.items():
            if pd.notna(v) and str(v).strip() not in ["", "None", "NaN", "NaT"]:
                lines.append(f"{k}: {v}")
                c += 1
                if c >= 15:
                    lines.append("Additional fields hidden for readability")
                    break
        return "\n".join(lines)

    try:
        if fetch_all:
            so_df = pd.read_sql_query("SELECT * FROM sales_order_headers LIMIT 200", conn)
            so_list = so_df['salesOrder'].tolist()
        else:
            so_list = context_ids.get("salesOrders", [])
            
        for so in so_list:
            so = str(so)
            headers = pd.read_sql_query(f"SELECT * FROM sales_order_headers WHERE salesOrder='{so}'", conn)
            so_title = format_tooltip("Sales Order", headers.iloc[0]) if not headers.empty else f"Sales Order\nID: {so}"
            add_node(so, f"SO {so}", "SalesOrder", title=so_title)
            
            items = pd.read_sql_query(f"SELECT * FROM sales_order_items WHERE salesOrder='{so}'", conn)
            for _, item in items.iterrows():
                mat = str(item['material'])
                amt = str(item.get('netAmount', ''))
                mat_title = format_tooltip("Product", item)
                add_node(mat, f"Product {mat}", "Product", title=mat_title)
                add_edge(so, mat, "contains", title=mat_title)
            
            if not headers.empty:
                cust = str(headers.iloc[0]['soldToParty'])
                amt = str(headers.iloc[0].get('totalNetAmount', ''))
                add_node(cust, f"Customer {cust}", "Customer", title=f"Customer\nID: {cust}")
                add_edge(cust, so, "ordered", title=so_title)

            del_items = pd.read_sql_query(f"SELECT * FROM outbound_delivery_items WHERE referenceSdDocument='{so}'", conn)
            for _, di in del_items.iterrows():
                dlv = str(di['deliveryDocument'])
                qty = str(di.get('actualDeliveryQuantity', ''))
                dlv_header = pd.read_sql_query(f"SELECT * FROM outbound_delivery_headers WHERE deliveryDocument='{dlv}'", conn)
                dlv_title = format_tooltip("Delivery", dlv_header.iloc[0]) if not dlv_header.empty else format_tooltip("Delivery", di)
                add_node(dlv, f"Delivery {dlv}", "Delivery", title=dlv_title)
                add_edge(so, dlv, "delivered_via", title=dlv_title)
                
                plt = str(di.get('plant', ''))
                if plt and plt != "None" and plt != "NaN" and len(plt) > 0:
                    add_node(plt, f"Plant {plt}", "Plant", title=f"Plant\nID: {plt}")
                    add_edge(dlv, plt, "from_plant", title=f"Plant\nID: {plt}")
            
            bill_items = pd.read_sql_query(f"SELECT * FROM billing_document_items WHERE referenceSdDocument='{so}'", conn)
            for _, bi in bill_items.iterrows():
                blg = str(bi['billingDocument'])
                bamt = str(bi.get('netAmount', ''))
                blg_header = pd.read_sql_query(f"SELECT * FROM billing_document_headers WHERE billingDocument='{blg}'", conn)
                blg_title = format_tooltip("Billing", blg_header.iloc[0]) if not blg_header.empty else format_tooltip("Billing", bi)
                add_node(blg, f"Billing {blg}", "Billing", title=blg_title)
                add_edge(so, blg, "billed_in", title=blg_title)
                
                journal = pd.read_sql_query(f"SELECT * FROM journal_entry_items_accounts_receivable WHERE referenceDocument='{blg}'", conn)
                for _, je in journal.iterrows():
                    je_id = str(je['accountingDocument'])
                    je_amt = str(je.get('amountInTransactionCurrency', ''))
                    je_title = format_tooltip("Journal Entry", je)
                    add_node(je_id, f"Journal {je_id}", "JournalEntry", title=je_title)
                    add_edge(blg, je_id, "accounted_in", title=je_title)

        if not fetch_all:
            for dlv in context_ids.get("deliveries", []):
                dlv = str(dlv)
                dlv_header = pd.read_sql_query(f"SELECT * FROM outbound_delivery_headers WHERE deliveryDocument='{dlv}'", conn)
                dlv_title = format_tooltip("Delivery", dlv_header.iloc[0]) if not dlv_header.empty else f"Delivery\nID: {dlv}"
                add_node(dlv, f"Delivery {dlv}", "Delivery", title=dlv_title)
                
                del_items = pd.read_sql_query(f"SELECT * FROM outbound_delivery_items WHERE deliveryDocument='{dlv}'", conn)
                for _, di in del_items.iterrows():
                    ref = str(di.get('referenceSdDocument', ''))
                    qty = str(di.get('actualDeliveryQuantity', ''))
                    if ref and ref != "None" and str(ref).strip() != "":
                        add_node(ref, f"SO {ref}", "SalesOrder", title=f"Sales Order\nID: {ref}")
                        add_edge(ref, dlv, "delivered_via", title=dlv_title)

            for blg in context_ids.get("billingDocuments", []):
                blg = str(blg)
                blg_header = pd.read_sql_query(f"SELECT * FROM billing_document_headers WHERE billingDocument='{blg}'", conn)
                blg_title = format_tooltip("Billing", blg_header.iloc[0]) if not blg_header.empty else f"Billing\nID: {blg}"
                add_node(blg, f"Billing {blg}", "Billing", title=blg_title)
                
                bill_items = pd.read_sql_query(f"SELECT * FROM billing_document_items WHERE billingDocument='{blg}'", conn)
                for _, bi in bill_items.iterrows():
                    ref = str(bi.get('referenceSdDocument', ''))
                    bamt = str(bi.get('netAmount', ''))
                    if ref and ref != "None" and str(ref).strip() != "":
                        add_node(ref, f"SO {ref}", "SalesOrder", title=f"Sales Order\nID: {ref}")
                        add_edge(ref, blg, "billed_in", title=blg_title)
                
                journal = pd.read_sql_query(f"SELECT * FROM journal_entry_items_accounts_receivable WHERE referenceDocument='{blg}'", conn)
                for _, je in journal.iterrows():
                    je_id = str(je['accountingDocument'])
                    je_title = format_tooltip("Journal Entry", je)
                    add_node(je_id, f"Journal {je_id}", "JournalEntry", title=je_title)
                    add_edge(blg, je_id, "accounted_in", title=je_title)
                    
            for p in context_ids.get("products", []):
                p = str(p)
                add_node(p, f"Product {p}", "Product", title=f"Product\nID: {p}")

    except Exception as e:
        print("Graph extract error:", e)
        
    conn.close()
    return {"nodes": nodes, "edges": edges}

from fastapi import FastAPI, HTTPException, Request

@app.get("/api/graph/init")
async def init_graph_endpoint():
    # Return the entire default graph limit configuration
    graph_data = extract_related_graph({}, fetch_all=True)
    return {"graph": graph_data}

@app.post("/api/chat")
async def chat_endpoint(req: QueryRequest, req_obj: Request):
    auth_header = req_obj.headers.get("Authorization")
    request_api_key = auth_header.replace("Bearer ", "").strip() if auth_header else os.environ.get("GEMINI_API_KEY", "dummy")
    
    local_client = genai.Client(api_key=request_api_key)
    
    system_prompt = f"""You are an advanced context graph exploration AI for an SAP Order-to-Cash dataset.
    The user will ask questions about orders, deliveries, invoices, payments, materials, etc.
    
    RULES & GUARDRAILS:
    1. Only return answers derived from the dataset itself.
    2. If the user asks a general knowledge, coding, or unrelated question, respond EXACTLY with:
       "This system is designed to answer questions related to the provided dataset only."
       
    DATASET SCHEMA:
    {SCHEMA_TEXT}
    
    INSTRUCTIONS:
    1. If a query requires data, call `execute_sql` tool.
    2. When you have the requested data, call `final_response` tool with the text response and relevant entity IDs so the UI can draw the context graph.
    3. If the query is rejected due to guardrails, just return a direct text message instead of calling tools.
    """
    
    # Convert messages
    contents = []
    for m in req.messages:
        role = "user" if m.get("role") == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m.get("content", ""))]))
        
    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="execute_sql",
                    description="Execute a SQL SELECT query against the SQLite database to retrieve data.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "query": types.Schema(
                                type=types.Type.STRING,
                                description="A valid SQLite query."
                            )
                        },
                        required=["query"]
                    )
                ),
                types.FunctionDeclaration(
                    name="final_response",
                    description="Format the final response for the user, including the primary entities found which will be graphed.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "answer": types.Schema(
                                type=types.Type.STRING,
                                description="The natural language answer to the user's question."
                            ),
                            "graph_entities": types.Schema(
                                type=types.Type.OBJECT,
                                description="Lists of entity IDs related to the response to build the graph.",
                                properties={
                                    "salesOrders": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                                    "deliveries": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                                    "billingDocuments": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                                    "products": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                                    "customers": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING))
                                }
                            )
                        },
                        required=["answer", "graph_entities"]
                    )
                )
            ]
        )
    ]
    
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=tools,
        temperature=0.0
    )
    
    try:
        response = local_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=config
        )
        
        while response.function_calls:
            should_continue = False
            contents.append(response.candidates[0].content)
            
            for fn_call in response.function_calls:
                if fn_call.name == "execute_sql":
                    query = fn_call.args.get("query", "")
                    res = execute_sql(query)
                    
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_function_response(
                                    name="execute_sql",
                                    response={"result": res}
                                )
                            ]
                        )
                    )
                    should_continue = True
                    
                elif fn_call.name == "final_response":
                    answer = fn_call.args.get("answer", "")
                    entities = fn_call.args.get("graph_entities", {})
                    
                    if hasattr(entities, "to_dict"):
                        entities = entities.to_dict()
                    elif not isinstance(entities, dict):
                        entities = dict(entities)
                        
                    graph_data = extract_related_graph(entities)
                    
                    return {
                        "role": "model",
                        "content": answer,
                        "graph": graph_data
                    }
                    
            if should_continue:
                response = local_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents,
                    config=config
                )
            else:
                break
                
        return {"role": "model", "content": response.text, "graph": {"nodes": [], "edges": []}}
    except Exception as e:
        print("API Error:", str(e))
        return {"role": "model", "content": "I encountered an error processing your query. Please format or try again.", "graph": {"nodes": [], "edges": []}}

# Mount frontend last so it doesn't intercept /api requests
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
