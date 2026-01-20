# manipulator.py
import pandas as pd
from typing import Dict, Any, List, Optional, Callable, Union
import json
import sys
from io import StringIO
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Form
from pathlib import Path

from agent import llm_agent


class DataProcessorAgent:
    """
    The execution engine for planned data processing operations.
    It takes a sequence of operations and applies them to data.
    """

    def __init__(self):
        self.tools: Dict[str, Callable] = {
            "read_csv": self._read_csv,
            "calculate_sum": self._calculate_sum,
            "calculate_average": self._calculate_average,
            "filter_rows": self._filter_rows,
            "sort_column": self._sort_column,
            "display_data": self._display_data,
            
            "group_and_aggregate": self._group_and_aggregate,
            "drop_columns": self._drop_columns,
            "rename_column": self._rename_column,
            "merge_dataframes": self._merge_dataframes,
            
        }
        self.data_store: Dict[str, pd.DataFrame] = {}
        self.results_store: Dict[str, Any] = {}
        self.final_output: Any = None

    def _read_csv(self, params: Dict[str, Any]) -> pd.DataFrame:
        filepath = params.get("filepath")
        if not filepath:
            raise ValueError(
                "No 'filepath' provided for read_csv operation in parameters."
            )

        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"CSV file not found at '{filepath}'. Please ensure it exists in the folder."
            )

        try:
            print(f"TOOL: Reading data from actual file '{filepath}'...")
            df = pd.read_csv(filepath)
            print(f"Successfully loaded '{filepath}'. Shape: {df.shape}")
            return df
        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file '{filepath}' is empty or has no data.")
        except pd.errors.ParserError as pe:
            raise ValueError(
                f"Failed to parse CSV file '{filepath}'. Check file format: {pe}"
            )
        except Exception as e:
            raise ValueError(
                f"An unexpected error occurred while reading '{filepath}': {str(e)}"
            )

    def _calculate_sum(
        self, df: pd.DataFrame, params: Dict[str, Any]
    ) -> Union[int, float]:
        column = params.get("column")
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found for sum operation.")
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise TypeError(f"Column '{column}' is not numeric. Cannot calculate sum.")
        print(f"TOOL: Calculating sum of column '{column}'...")
        return df[column].sum()

    def _calculate_average(
        self, df: pd.DataFrame, params: Dict[str, Any]
    ) -> Union[int, float]:
        column = params.get("column")
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found for average operation.")
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise TypeError(
                f"Column '{column}' is not numeric. Cannot calculate average."
            )
        print(f"TOOL: Calculating average of column '{column}'...")
        return df[column].mean()

    def _filter_rows(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        column = params.get("column")
        value = params.get("value")
        operator_str = params.get("operator", "==")

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found for filter operation.")

        print(f"TOOL: Filtering rows where '{column}' {operator_str} '{value}'...")

        if pd.api.types.is_numeric_dtype(df[column]):
            try:
                # Attempt to convert filter value to the column's numeric type
                value = type(df[column].iloc[0])(value)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Cannot compare non-numeric value '{value}' with numeric column '{column}'."
                )
        elif isinstance(value, (int, float)):
            raise ValueError(
                f"Cannot compare numeric value '{value}' with non-numeric column '{column}'."
            )

        if operator_str == "==":
            return df[df[column] == value]
        elif operator_str == ">":
            return df[df[column] > value]
        elif operator_str == "<":
            return df[df[column] < value]
        elif operator_str == ">=":
            return df[df[column] >= value]
        elif operator_str == "<=":
            return df[df[column] <= value]
        elif operator_str == "!=":
            return df[df[column] != value]
        else:
            raise ValueError(f"Unsupported filter operator: {operator_str}")

    def _sort_column(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        column = params.get("column")
        order = params.get("order", "ascending")

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found for sort operation.")
        if order not in ["ascending", "descending"]:
            raise ValueError(
                f"Unsupported sort order: {order}. Use 'ascending' or 'descending'."
            )

        ascending = order == "ascending"
        print(f"TOOL: Sorting by column '{column}' in {order} order...")
        return df.sort_values(by=column, ascending=ascending).reset_index(drop=True)

    def _display_data(self, data: Any, params: Dict[str, Any]):
        label = params.get("label", "Result")
        print(f"\n--- {label} ---")
        if isinstance(data, pd.DataFrame):
            if len(data) > 10:
                print(data.head().to_string())
                print("...\n(Showing top 5 rows, data truncated for display)\n...")
            else:
                print(data.to_string())
        else:
            print(data)
        print("-----------------\n")
        return None 
    def _group_and_aggregate(
        self, df: pd.DataFrame, params: Dict[str, Any]
    ) -> pd.DataFrame:
        by_columns = params.get("by_columns")
        aggregations = params.get("aggregations")

        if not by_columns:
            raise ValueError(
                "No 'by_columns' provided for group_and_aggregate operation."
            )
        if not aggregations:
            raise ValueError(
                "No 'aggregations' provided for group_and_aggregate operation."
            )

        for col in by_columns:
            if col not in df.columns:
                raise ValueError(f"Grouping column '{col}' not found in DataFrame.")

        named_aggs = {}
        for agg in aggregations:
            col_to_agg = agg.get("column")
            func = agg.get("function")
            output_name = agg.get("output_column_name", f"{col_to_agg}_{func}")

            if col_to_agg not in df.columns:
                raise ValueError(
                    f"Aggregation column '{col_to_agg}' not found in DataFrame."
                )
            if func not in ["sum", "mean", "count", "min", "max"]:
                raise ValueError(
                    f"Unsupported aggregation function: {func}. Use 'sum', 'mean', 'count', 'min', 'max'."
                )

            named_aggs[output_name] = pd.NamedAgg(column=col_to_agg, aggfunc=func)

        print(f"TOOL: Grouping by {by_columns} and aggregating: {aggregations}...")

        result_df = df.groupby(by_columns).agg(**named_aggs).reset_index()
        return result_df

    def _drop_columns(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        columns_to_drop = params.get("columns_to_drop")
        if not columns_to_drop:
            raise ValueError(
                "No 'columns_to_drop' provided for drop_columns operation."
            )

        # Check if all columns exist before dropping
        missing_columns = [col for col in columns_to_drop if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Columns to drop not found: {', '.join(missing_columns)}")

        print(f"TOOL: Dropping columns: {columns_to_drop}...")
        return df.drop(columns=columns_to_drop)

    def _rename_column(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        old_name = params.get("old_name")
        new_name = params.get("new_name")

        if not old_name or not new_name:
            raise ValueError(
                "Both 'old_name' and 'new_name' must be provided for rename_column."
            )
        if old_name not in df.columns:
            raise ValueError(f"Column '{old_name}' not found for renaming.")

        print(f"TOOL: Renaming column '{old_name}' to '{new_name}'...")
        return df.rename(columns={old_name: new_name})

    def _merge_dataframes(
        self, left_df: pd.DataFrame, params: Dict[str, Any]
    ) -> pd.DataFrame:
        right_data_key = params.get("right_data_key")
        on_column = params.get("on_column")
        how = params.get("how", "inner")

        if not right_data_key:
            raise ValueError(
                "No 'right_data_key' provided for merge_dataframes operation."
            )
        if not on_column:
            raise ValueError("No 'on_column' provided for merge_dataframes operation.")

        right_df = self.data_store.get(right_data_key)
        if right_df is None:
            raise ValueError(
                f"Right DataFrame with key '{right_data_key}' not found in data_store for merging."
            )

        if on_column not in left_df.columns:
            raise ValueError(
                f"Join column '{on_column}' not found in left DataFrame (input_data_key)."
            )
        if on_column not in right_df.columns:
            raise ValueError(
                f"Join column '{on_column}' not found in right DataFrame ('{right_data_key}')."
            )
        if how not in ["inner", "left", "right", "outer"]:
            raise ValueError(
                f"Unsupported merge 'how' type: {how}. Use 'inner', 'left', 'right', 'outer'."
            )

        print(f"TOOL: Merging DataFrames on '{on_column}' with '{how}' join...")
        return pd.merge(left_df, right_df, on=on_column, how=how)

    def execute_plan(self, plan: Dict[str, Any]):
        self.data_store = {}
        self.results_store = {}
        self.final_output = None

        print("\n--- Starting Plan Execution ---")

        operations = plan.get("operations", [])
        if not operations:
            raise ValueError("No 'operations' array found in the plan. Cannot execute.")

        for i, op_dict in enumerate(operations):
            op_type = op_dict.get("operation_type")
            input_key = op_dict.get("input_data_key")
            output_key = op_dict.get("output_data_key")
            params = op_dict.get("parameters", {})
            description = op_dict.get("description", f"Step {i+1}: {op_type}")

            print(f"STEP {i+1}: {description}")

            if op_type not in self.tools:
                raise ValueError(f"ERROR: Unknown operation type '{op_type}' in plan.")

            tool_func = self.tools[op_type]
            current_input_data = None  
            
            if op_type == "read_csv":
                pass  # read_csv generates new data
            elif op_type == "merge_dataframes":
                
                if not input_key:
                    raise ValueError(
                        f"Operation '{op_type}' requires 'input_data_key' (left DataFrame)."
                    )
                current_input_data = self.data_store.get(input_key)
                if current_input_data is None:
                    raise ValueError(
                        f"Left DataFrame with key '{input_key}' not found for '{op_type}'."
                    )
                if not isinstance(current_input_data, pd.DataFrame):
                    raise TypeError(
                        f"Left DataFrame from '{input_key}' for '{op_type}' is not a DataFrame."
                    )
            elif input_key:
                
                current_input_data = self.data_store.get(input_key)
                if current_input_data is None:
                    current_input_data = self.results_store.get(input_key)

                if current_input_data is None:
                    raise ValueError(
                        f"ERROR: Input data with key '{input_key}' not found for operation '{op_type}'. "
                        f"Ensure previous operations have completed and stored their output correctly."
                    )
            else:
                # If input_key is not specified, it's an error for operations that need it
                if op_type not in [
                    "read_csv",
                    "display_data",
                ]:  # Display can take scalar or DF directly from results_store
                    raise ValueError(
                        f"Operation '{op_type}' requires 'input_data_key' but none was provided."
                    )

            try:
                
                if op_type == "read_csv":
                    result = tool_func(params)
                elif op_type == "display_data":
                    # Display tool takes the data to display and its params
                    result = tool_func(current_input_data, params)
                elif op_type == "merge_dataframes":
                    
                    result = tool_func(current_input_data, params)
                else:  
                    if not isinstance(current_input_data, pd.DataFrame):
                        raise TypeError(
                            f"ERROR: Operation '{op_type}' expects a DataFrame input, but got {type(current_input_data)} from '{input_key}'."
                        )
                    result = tool_func(current_input_data, params)

                if output_key:
                    if isinstance(result, pd.DataFrame):
                        self.data_store[output_key] = result
                        print(
                            f"Stored DataFrame as '{output_key}'. Shape: {result.shape}"
                        )
                    else:
                        self.results_store[output_key] = result
                        print(f"Stored result as '{output_key}'. Value: {result}")
                elif result is not None and op_type != "display_data":
                    print(
                        f"WARNING: Operation '{op_type}' produced a result but no 'output_data_key' was provided. Result will not be chained effectively."
                    )

                if result is not None and op_type != "display_data":
                    self.final_output = result

            except Exception as e:
                print(f"ERROR: Execution failed for '{op_type}' (Step {i+1}): {e}")
                raise

        print("\n--- Plan Execution Complete ---")
        
        if self.final_output is not None:
            if isinstance(self.final_output, pd.DataFrame):
                # Convert DataFrame to list of dictionaries for JSON
                return self.final_output.to_dict(orient="records")
            elif isinstance(
                self.final_output, (pd.Series, pd.Index)
            ):  # Handle Series if it somehow became final_output
                return self.final_output.tolist()  # Convert Series to list
            return (
                self.final_output
            )  # Already serializable (int, float, str, dict, list etc.)
        elif self.results_store:
            # If final_output is None, but results_store has data, return it
            # Ensure contents are also serializable.
            # If result_store itself contains DataFrames or Series, they need conversion.
            # Assuming results_store typically holds scalar values or dicts/lists.
            for key, value in self.results_store.items():
                if isinstance(value, pd.DataFrame):
                    self.results_store[key] = value.to_dict(orient="records")
                elif isinstance(value, (pd.Series, pd.Index)):
                    self.results_store[key] = value.tolist()
            return self.results_store
        elif self.data_store:
            # If no final_output or results_store, return the last DataFrame from data_store
            # This should always be converted to a list of dicts for JSON
            last_df = list(self.data_store.values())[-1]
            if isinstance(last_df, pd.DataFrame):
                return last_df.to_dict(orient="records")
            elif isinstance(
                last_df, (pd.Series, pd.Index)
            ):  
                return last_df.tolist()
            return last_df  
        return {
            "message": "No significant output to return."
        } 


# Main execution block
def process_csv_file(file_path: Path, user_query: str):
    agent_executor = DataProcessorAgent()

    print("\n--- AI Data Processor ---")

    filename = file_path  
    available_columns: List[str] = []
    try:
        temp_df = pd.read_csv(filename, nrows=0)  
        available_columns = temp_df.columns.tolist()
        print(
            f"Successfully read columns from '{filename}'. Available columns: {', '.join(available_columns)}"
        )
    except FileNotFoundError:
        print(
            f"Error: File '{filename}' not found. Please ensure it is in the same directory."
        )
        raise ValueError(
            f"File not found: {filename}"
        )   
    except pd.errors.EmptyDataError:
        print(f"Error: File '{filename}' is empty. Cannot extract columns.")
        raise ValueError(f"File is empty: {filename}")  
    except Exception as e:
        print(
            f"An unexpected error occurred while reading columns from '{filename}': {e}"
        )
        raise ValueError(f"Error reading columns from file: {e}")  

    print("\nGetting plan from LLM...")
    llm_plan_response = llm_agent(
        user_query, str(filename), available_columns
    )  

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    execution_success = False
    try:
        print("\nExecuting plan...")
        final_result = agent_executor.execute_plan(llm_plan_response)
        execution_success = True
        print("\nPlan execution finished.")
    except Exception as e:
        print(f"\nExecution Aborted due to Error: {e}")
        final_result = {"status": "error", "message": f"Execution failed: {str(e)}"}

    sys.stdout = old_stdout

    print("\n--- LLM Generated Plan ---")
    print(json.dumps(llm_plan_response, indent=2))
    print("--------------------------")
    print(f"\nFinal result from executor (before backend return): {final_result}")

    output_txt_final_result = (
        json.dumps(final_result, indent=2)
        if isinstance(final_result, (dict, list))
        else str(final_result)
    )

    with open("output.txt", "w") as f:
        f.write("User Query: " + user_query + "\n")
        f.write(
            "Target File: " + str(filename) + "\n"
        )  
        f.write("Available Columns: " + ", ".join(available_columns) + "\n\n")
        f.write("LLM Plan:\n")
        f.write(json.dumps(llm_plan_response, indent=2) + "\n\n")
        f.write("Executor Console Output:\n")
        f.write(mystdout.getvalue() + "\n")
        f.write(
            "Final Returned Result (JSON/String): \n" + output_txt_final_result + "\n"
        )

    if execution_success:
        return {
            "status": "success",
            "message": "CSV processed and query executed successfully.",
            "processed_data": final_result,  
        }
    else:
        return final_result 
