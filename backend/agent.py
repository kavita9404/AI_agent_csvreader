# agent.py
import getpass
import os
import dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
import json
from typing import List  

dotenv.load_dotenv()

schema = {
    "name": "data_processing_plan",
    "description": "A comprehensive plan containing a sequence of data processing operations.",
    "parameters": {
        "type": "object",
        "properties": {
            "operations": {
                "type": "array",
                "description": "The sequence of data processing operations to be executed.",
                "items": {
                    "type": "object",
                    "properties": {
                        "operation_type": {
                            "type": "string",
                            "description": "The specific operation to perform (e.g., 'read_csv', 'calculate_sum', 'filter_rows', 'write_output', 'group_and_aggregate', 'drop_columns', 'rename_column', 'merge_dataframes').",
                        },
                        "input_data_key": {
                            "type": ["string", "null"],
                            "description": "Optional key referencing data from a previous operation. Use null if this operation generates new data (e.g., 'read_csv').",
                        },
                        "output_data_key": {
                            "type": ["string", "null"],
                            "description": "Optional key to name the output data from this operation for future operations. Use null if output is not needed for chaining (e.g., 'display_data').",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Parameters specific to the operation.",
                            "additionalProperties": True,  # Allows for any other properties not explicitly listed
                            "properties": {
                                "filepath": {"type": "string"},
                                "column": {"type": "string"},
                                "value": {"type": ["string", "number"]},
                                "operator": {"type": "string"},
                                "label": {"type": "string"},
                                "order": {
                                    "type": "string",
                                    "enum": ["ascending", "descending"],
                                },
                                "columns_to_drop": {  # For drop_columns
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of column names to drop.",
                                },
                                "old_name": {"type": "string"},  # For rename_column
                                "new_name": {"type": "string"},  # For rename_column
                                "by_columns": {  # For group_and_aggregate
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of columns to group by.",
                                },
                                "aggregations": {  # For group_and_aggregate
                                    "type": "array",
                                    "description": "List of aggregation definitions.",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "column": {"type": "string"},
                                            "function": {
                                                "type": "string",
                                                "enum": [
                                                    "sum",
                                                    "mean",
                                                    "count",
                                                    "min",
                                                    "max",
                                                ],
                                            },
                                            "output_column_name": {
                                                "type": "string",
                                                "description": "Optional: New name for the aggregated column.",
                                            },
                                        },
                                        "required": ["column", "function"],
                                    },
                                },
                                "right_data_key": {
                                    "type": "string"
                                },  # For merge_dataframes
                                "on_column": {
                                    "type": "string"
                                },  # For merge_dataframes (single join column)
                                "how": {
                                    "type": "string",
                                    "enum": ["inner", "left", "right", "outer"],
                                },  # For merge_dataframes
                            },
                        },
                        "description": {
                            "type": ["string", "null"],
                            "description": "Optional human-readable explanation of this step.",
                        },
                    },
                    "required": ["operation_type", "parameters"],
                },
            },
        },
        "required": ["operations"],
    },
}
guided_prompt = """
You are a data processing planner. Based on the user's request,
generate a JSON object representing a sequence of operations to perform on CSV file(s).
The JSON must strictly follow the provided schema, particularly ensuring the top-level
object contains an 'operations' array.

IMPORTANT:
1. Always complete the full sequence of operations needed to answer the user's query.
2. **COLUMN NAME CONSTRAINT:** When generating operations (e.g., 'calculate_sum', 'calculate_average', 'filter_rows', 'sort_column', 'group_and_aggregate', 'drop_columns', 'rename_column', 'merge_dataframes'), you **MUST USE ONLY THE COLUMN NAMES PROVIDED IN THE 'AVAILABLE COLUMNS' LIST**. Do NOT invent, assume, or use column names not explicitly listed. If the user's query refers to a column not in the available list, state the column is not found if no reasonable operation is possible with available columns.
3. Use the appropriate operations for each query type. Always end with 'display_data' to show results.

Available operations and their EXACT parameters:
- operation_type: 'read_csv'
  Parameters: {{"filepath": "string"}} (Use the file path provided in the user's query context)
- operation_type: 'calculate_sum'
  Parameters: {{"column": "string"}}
- operation_type: 'calculate_average'
  Parameters: {{"column": "string"}}
- operation_type: 'filter_rows'
  Parameters: {{"column": "string", "value": "number", "operator": "string"}} (operator can be "==", ">", "<", ">=", "<=", "!=")
- operation_type: 'sort_column'
  Parameters: {{"column": "string", "order": "string"}} (order must be "ascending" or "descending")
- operation_type: 'drop_columns'
  Parameters: {{"columns_to_drop": "array of strings"}} (e.g., ["column_a", "column_b"])
- operation_type: 'rename_column'
  Parameters: {{"old_name": "string", "new_name": "string"}}
- operation_type: 'group_and_aggregate'
  Parameters: {{"by_columns": "array of strings", "aggregations": "array of objects"}}
    - Each object in 'aggregations' must have:
      - "column": "string" (column to aggregate)
      - "function": "string" (e.g., "sum", "mean", "count", "min", "max")
      - "output_column_name": "string" (optional, for the new aggregated column name)
- operation_type: 'merge_dataframes'
  Parameters: {{"right_data_key": "string", "on_column": "string", "how": "string"}}
    - 'right_data_key' refers to the key of the DataFrame to merge with (from 'read_csv' or prior step's 'output_data_key').
    - 'on_column' is the common column for merging.
    - 'how' can be "inner", "left", "right", "outer".
- operation_type: 'display_data'
  Parameters: {{"label": "string"}}

IMPORTANT RULES FOR PLAN GENERATION:
1. Only include the parameters specified above for each operation type.
2. For filter_rows, 'value' parameter should be a number when comparing numeric columns.
3. For sort_column, 'order' must be either "ascending" or "descending".
4. Always include a 'display_data' operation at the end to show results.
5. Use 'input_data_key' to specify which data from a previous step an operation should use.
6. Use 'output_data_key' to name the result of an operation so subsequent operations can use it.
7. 'read_csv' typically does not need an 'input_data_key'.
8. 'display_data' typically does not need an 'output_data_key'.

Here are examples of complete operation sequences for different queries given specific contexts:
"""


def llm_agent(user_query_text: str, filename: str, available_columns: List[str]):
    if not os.environ.get("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google API key")

    llm_context_input = f"""
User Request: {user_query_text}
Target File: {filename}
Available Columns: {', '.join(available_columns)}
"""
    prompt_messages = [
        ("system", guided_prompt),
        # --- Example 1: Find Most Popular Song (unchanged for consistency) ---
        HumanMessage(
            content="""
User Request: Which song has the most popularity?
Target File: music_data.csv
Available Columns: Song, Artist, popularity, duration_ms, genre
"""
        ),
        AIMessage(
            content=json.dumps(
                {
                    "operations": [
                        {
                            "operation_type": "read_csv",
                            "parameters": {"filepath": "music_data.csv"},
                            "output_data_key": "raw_music_data",
                            "description": "Load the CSV data from 'music_data.csv'.",
                        },
                        {
                            "operation_type": "sort_column",
                            "input_data_key": "raw_music_data",
                            "output_data_key": "sorted_music",
                            "parameters": {
                                "column": "popularity",
                                "order": "descending",
                            },
                            "description": "Sort songs by the 'popularity' column in descending order.",
                        },
                        {
                            "operation_type": "display_data",
                            "input_data_key": "sorted_music",
                            "output_data_key": None,
                            "parameters": {"label": "Most Popular Songs"},
                            "description": "Display the sorted songs to show the most popular ones.",
                        },
                    ]
                }
            )
        ),
        # --- Example 2: Group and Aggregate (NEW COMPLEX EXAMPLE) ---
        HumanMessage(
            content="""
User Request: What is the total sales and average quantity for each product category?
Target File: sales_data.csv
Available Columns: transaction_id, product_name, category, sales_amount, quantity, date
"""
        ),
        AIMessage(
            content=json.dumps(
                {
                    "operations": [
                        {
                            "operation_type": "read_csv",
                            "parameters": {"filepath": "sales_data.csv"},
                            "output_data_key": "sales_df",
                            "description": "Load sales data.",
                        },
                        {
                            "operation_type": "group_and_aggregate",
                            "input_data_key": "sales_df",
                            "output_data_key": "category_summary",
                            "parameters": {
                                "by_columns": ["category"],
                                "aggregations": [
                                    {
                                        "column": "sales_amount",
                                        "function": "sum",
                                        "output_column_name": "Total Sales",
                                    },
                                    {
                                        "column": "quantity",
                                        "function": "mean",
                                        "output_column_name": "Average Quantity",
                                    },
                                ],
                            },
                            "description": "Group by category and calculate total sales and average quantity.",
                        },
                        {
                            "operation_type": "display_data",
                            "input_data_key": "category_summary",
                            "output_data_key": None,
                            "parameters": {"label": "Sales Summary by Category"},
                            "description": "Display the aggregated summary.",
                        },
                    ]
                }
            )
        ),
        # --- Example 3: Drop and Rename Columns (NEW EXAMPLE) ---
        HumanMessage(
            content="""
User Request: I only need product name and its price. Also, rename 'price' to 'unit_price'.
Target File: products.csv
Available Columns: product_id, name, description, price, category, stock_count
"""
        ),
        AIMessage(
            content=json.dumps(
                {
                    "operations": [
                        {
                            "operation_type": "read_csv",
                            "parameters": {"filepath": "products.csv"},
                            "output_data_key": "product_data",
                            "description": "Load product data.",
                        },
                        {
                            "operation_type": "drop_columns",
                            "input_data_key": "product_data",
                            "output_data_key": "relevant_products",
                            "parameters": {
                                "columns_to_drop": [
                                    "product_id",
                                    "description",
                                    "category",
                                    "stock_count",
                                ]
                            },
                            "description": "Drop irrelevant columns.",
                        },
                        {
                            "operation_type": "rename_column",
                            "input_data_key": "relevant_products",
                            "output_data_key": "final_products",
                            "parameters": {
                                "old_name": "price",
                                "new_name": "unit_price",
                            },
                            "description": "Rename 'price' column to 'unit_price'.",
                        },
                        {
                            "operation_type": "display_data",
                            "input_data_key": "final_products",
                            "output_data_key": None,
                            "parameters": {"label": "Product Names and Unit Prices"},
                            "description": "Display the final product data.",
                        },
                    ]
                }
            )
        ),
        # --- Example 4: Merge DataFrames (NEW COMPLEX EXAMPLE) ---
        HumanMessage(
            content="""
User Request: Combine sales data from 'daily_sales.csv' with product details from 'product_info.csv' using 'product_id'. Show total sales amounts for the combined data.
Target File: daily_sales.csv AND product_info.csv
Available Columns:
  daily_sales.csv: date, product_id, amount, quantity
  product_info.csv: product_id, product_name, category
"""
        ),
        AIMessage(
            content=json.dumps(
                {
                    "operations": [
                        {
                            "operation_type": "read_csv",
                            "parameters": {"filepath": "daily_sales.csv"},
                            "output_data_key": "daily_sales_data",
                            "description": "Load daily sales data.",
                        },
                        {
                            "operation_type": "read_csv",
                            "parameters": {"filepath": "product_info.csv"},
                            "output_data_key": "product_info_data",
                            "description": "Load product information.",
                        },
                        {
                            "operation_type": "merge_dataframes",
                            "input_data_key": "daily_sales_data",  # Left DataFrame
                            "output_data_key": "merged_sales_products",
                            "parameters": {
                                "right_data_key": "product_info_data",  # Right DataFrame
                                "on_column": "product_id",
                                "how": "inner",
                            },
                            "description": "Merge sales and product data on 'product_id'.",
                        },
                        {
                            "operation_type": "calculate_sum",
                            "input_data_key": "merged_sales_products",
                            "output_data_key": "total_combined_sales",
                            "parameters": {"column": "amount"},
                            "description": "Calculate the total sales from the combined data.",
                        },
                        {
                            "operation_type": "display_data",
                            "input_data_key": "total_combined_sales",
                            "output_data_key": None,
                            "parameters": {"label": "Total Combined Sales Amount"},
                            "description": "Display the total sales amount.",
                        },
                    ]
                }
            )
        ),
        HumanMessage(content=llm_context_input),
    ]

    prompt = ChatPromptTemplate.from_messages(prompt_messages)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0)

    structured_llm = llm.with_structured_output(schema)
    chain = prompt | structured_llm

    response = chain.invoke({"input": llm_context_input})

    return response
