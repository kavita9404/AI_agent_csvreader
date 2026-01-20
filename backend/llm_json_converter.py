# llm_json_converter.py
import google.generativeai as genai
import json
import os
from typing import Any, Dict, Union
import dotenv
dotenv.load_dotenv()
model = genai.GenerativeModel("gemini-1.5-flash")

def data_to_json_with_llm(data: Any, context_description: str) -> Dict[str, Any]:
    """
    Leverages an LLM to convert arbitrary Python data into a JSON structure.

    Args:
        data: The Python object (e.g., pandas DataFrame converted to string, dict, list)
              to be converted into a JSON response.
        context_description: A natural language description or instruction for the LLM
                             on how to structure the JSON output based on the data.
                             E.g., "Convert this data into a JSON object with 'rows' and 'summary' keys."

    Returns:
        A dictionary representing the JSON output from the LLM.

    Raises:
        ValueError: If the LLM response cannot be parsed as valid JSON.
        Exception: For any other issues with LLM API call or response.
    """
    # Convert data to a string representation suitable for LLM input
    # For pandas DataFrames, to_string() is good, but for large DFs, it will hit token limits.
    # For production, you'd likely summarize large DFs or pass specific subsets.
    if hasattr(data, 'to_string') and not isinstance(data, (dict, list, str, int, float, bool)):
        data_representation = data.to_string() # Converts pandas DataFrame to string
    elif isinstance(data, (dict, list)):
        data_representation = json.dumps(data, indent=2)
    else:
        data_representation = str(data)
    prompt = f"""
    You are an expert data serializer. Your task is to convert the provided data into a JSON object.
    Strictly ensure the output is valid, well-formed JSON. Do not include any preambles,
    explanations, or markdown formatting outside of the JSON itself.

    Here is the data:
    ```
    {data_representation}
    ```

    Here are the instructions for structuring the JSON output:
    {context_description}

    Return only the JSON object.
    """

    print(f"LLM_JSON_CONVERTER: Sending data to LLM for JSON conversion (first 200 chars of data): {data_representation[:200]}...")

    try:
        response = model.generate_content(
            prompt,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            },
            generation_config=genai.GenerationConfig(
                temperature=0.1,  # Keep temperature low for deterministic output
                response_mime_type="application/json" # Request JSON output directly
            )
        )
        llm_output_text = response.text
        if llm_output_text.startswith("```json") and llm_output_text.endswith("```"):
            llm_output_text = llm_output_text[7:-3].strip()

        print("LLM_JSON_CONVERTER: Raw LLM Output (first 500 chars):", llm_output_text[:500])

        json_output = json.loads(llm_output_text)
        print("LLM_JSON_CONVERTER: Successfully parsed JSON from LLM.")
        return json_output

    except json.JSONDecodeError as e:
        print(f"LLM_JSON_CONVERTER ERROR: LLM did not return valid JSON. Error: {e}")
        print("LLM Response that caused error:", llm_output_text)
        raise ValueError(f"LLM failed to return valid JSON: {e}")
    except Exception as e:
        print(f"LLM_JSON_CONVERTER ERROR: An error occurred during LLM call: {e}")
        raise