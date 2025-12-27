from typing import Tuple, List
import re
import pdf2image
import pytesseract
import os
import requests
import io
import base64
import json
from PIL import Image
from pdf2image.exceptions import PDFPageCountError
import time

class PDFPreprocessor:
    CHUNK_SIZE = 3500
    CHUNK_OVERLAP = 300
    NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    NVIDIA_MODEL = "nvidia/nemoretriever-parse"
    NVIDIA_TOOL = "markdown_no_bbox" 

    @staticmethod
    def preprocess_pdf(pdf_file, use_nvidia: bool = False) -> Tuple[str, List[str]]:
        """
        Preprocess a PDF file to extract text and create chunks.
        
        Args:
            pdf_file: The uploaded PDF file object
            use_nvidia: Whether to use NVIDIA API for OCR (True) or local OCR (False)
            
        Returns:
            Tuple of (cleaned_text, text_chunks)
        """
        image_list = PDFPreprocessor._bytes2imagelist(pdf_file)
        if use_nvidia:
            extracted_text = PDFPreprocessor._imagelist2text_nvidia(image_list)
        else:
            extracted_text = PDFPreprocessor._imagelist2text(image_list)
        clean_text = PDFPreprocessor._clean_text(extracted_text, drop_short_lines=( not use_nvidia))
        chunks = PDFPreprocessor._get_chunks(clean_text)
        return clean_text, chunks

    @staticmethod
    def _bytes2imagelist(uploaded_file) -> List:
        """
        Return a list of PIL.Image objects from the uploaded file.
        - If it's a valid PDF (starts with %PDF-): render pages via pdf2image at 250 DPI.
        - If it's a raster image (PNG/JPEG/...): treat it as a single-page "PDF".
        - Otherwise: raise ValueError with a clear message.
        """
        buf = uploaded_file.getbuffer()
        data = buf.tobytes() if hasattr(buf, "tobytes") else buf  # Streamlit returns a memoryview

        # PDF path
        if data[:5] == b"%PDF-":
            try:
                return pdf2image.convert_from_bytes(data, dpi=250)
            except PDFPageCountError as e:
                raise ValueError("Failed to read PDF pages (file may be corrupted or encrypted).") from e
            except Exception as e:
                raise ValueError(f"Cannot load PDF: {e}") from e

        # Image path (PNG/JPEG, etc.)
        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
            return [img]
        except Exception:
            raise ValueError("Uploaded file is neither a readable PDF nor an image.")

    @staticmethod
    def _imagelist2text(image_list: List) -> str:
        """Extract text from images using local OCR (pytesseract)."""
        entire_text = ''
        for pagenumber, img in enumerate(image_list, start=1):
            detected_text = pytesseract.image_to_string(img) 
            entire_text += detected_text
        return entire_text

    @staticmethod
    def _imagelist2text_nvidia(image_list: List) -> str:
        """
        Extract text from images using NVIDIA's chat completions API.
        - Sends each page image independently using the markdown_no_bbox tool.
        - Uses JPEG at quality 95 and stable DPI (via _bytes2imagelist) to avoid overflows.
        - Implements per-page error handling: a failed page is logged and skipped, the run continues.
        - Parses response text and gently flattens LaTeX tables without aggressive deletions.
        """
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("Missing NVIDIA_API_KEY env var")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        all_pages_text = []
        for idx, img in enumerate(image_list, start=1):
            try:
                b64, mime = PDFPreprocessor._pil_image_to_base64(img)
                media_tag = f'<img src="data:{mime};base64,{b64}" />'

                # Request: single-image content with tool_choice set to markdown_no_bbox
                inputs = {
                    "model": PDFPreprocessor.NVIDIA_MODEL,  # "nvidia/nemoretriever-parse"
                    "messages": [
                        {"role": "user", "content": media_tag}
                    ],
                    "tools": [
                        {"type": "function", "function": {"name": PDFPreprocessor.NVIDIA_TOOL}}
                    ],  # first-step tool: "markdown_no_bbox"
                    "tool_choice": {
                        "type": "function",
                        "function": {"name": PDFPreprocessor.NVIDIA_TOOL},
                    },
                    "max_tokens": 2048,
                    "temperature": 0,
                }
                start_time = time.time()
                resp = requests.post(PDFPreprocessor.NVIDIA_URL, headers=headers, json=inputs, timeout=120)
                end_time = time.time()
                print(f"NVIDIA API call took {end_time - start_time} seconds", flush=True)
                if resp.status_code >= 400:
                    try:
                        print(f"NVIDIA error for page {idx} payload:", resp.json())
                    except Exception:
                        print(f"NVIDIA error for page {idx} text:", resp.text)
                    # Continue to next page instead of crashing the entire run
                    all_pages_text.append("")  # Add empty string for failed page
                    continue

                page_text = PDFPreprocessor._parse_nvidia_response_text(resp.json())

                # Loss-friendly table flattening (preserves inner text)
                page_text = PDFPreprocessor._strip_latex_tables(page_text)
                all_pages_text.append(page_text.strip())
            except Exception as e:
                print(f"Error processing page {idx}: {e}")
                # Continue to next page instead of crashing
                all_pages_text.append("")  # Add empty string for failed page

        return "\n\n".join(all_pages_text)


    @staticmethod
    def _pil_image_to_base64(pil_image) -> tuple[str, str]:
        """Convert PIL image to base64 string with JPEG quality 95."""
        buf = io.BytesIO()
        pil_image.convert("RGB").save(buf, format="jpeg", quality=95, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        mime = "image/jpeg"
        return b64, mime


    @staticmethod
    def _parse_nvidia_response_text(resp_json: dict) -> str:
        """
        Try to extract text from the response JSON.
        Handles direct message.content and tool_calls[].function.arguments
        where arguments can be str (JSON), dict, or list. Prefers plain text from
        'text'/'markdown'/'content'/'value'. Falls back to JSON string if no text found.
        """
        # 0) get the message
        try:
            msg = resp_json["choices"][0]["message"]
        except (KeyError, IndexError, TypeError):
            return ""

        # 1) direct content
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        # 2) arguments from tool_calls (keep the same structure: only the first one)
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls or not isinstance(tool_calls, list):
            return ""

        fn = (tool_calls[0] or {}).get("function") or {}
        args = fn.get("arguments")

        # ---- helpers in-line (no inner functions) ----
        def _extract_from_dict_once(d: dict):
            # search for the common keys
            for key in ("text", "markdown", "content", "value"):
                val = d.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
            return None

        # extract text from list (includes nested lists) without recursion/inner functions
        def _extract_from_list_flat(lst):
            texts = []
            stack = list(lst)
            while stack:
                item = stack.pop(0)
                if isinstance(item, dict):
                    got = _extract_from_dict_once(item)
                    if isinstance(got, str) and got:
                        texts.append(got)
                    # common containers with possible sub-items
                    for container in ("parts", "data", "items", "content"):
                        sub = item.get(container)
                        if isinstance(sub, list):
                            stack.extend(sub)
                        elif isinstance(sub, dict):
                            got2 = _extract_from_dict_once(sub)
                            if isinstance(got2, str) and got2:
                                texts.append(got2)
                elif isinstance(item, list):
                    stack.extend(item)
                elif isinstance(item, str):
                    s = item.strip()
                    if s:
                        texts.append(s)
            return texts

        # ---- process arguments ----

        # a) arguments as string (sometimes JSON as string)
        if isinstance(args, str) and args.strip():
            arg_str = args.strip()
            try:
                parsed = json.loads(arg_str)
            except Exception:
                # not valid JSON – return as text string
                return arg_str

            if isinstance(parsed, dict):
                got = _extract_from_dict_once(parsed)
                if got:
                    return got
                # try to collect text from common containers
                texts = []
                for container in ("parts", "data", "items", "content"):
                    sub = parsed.get(container)
                    if isinstance(sub, list):
                        texts.extend(_extract_from_list_flat(sub))
                    elif isinstance(sub, dict):
                        got2 = _extract_from_dict_once(sub)
                        if got2:
                            texts.append(got2)
                if texts:
                    return "\n\n".join(texts).strip()
                return json.dumps(parsed, ensure_ascii=False)

            if isinstance(parsed, list):
                texts = _extract_from_list_flat(parsed)
                if texts:
                    return "\n\n".join(texts).strip()
                return json.dumps(parsed, ensure_ascii=False)

            # other types – return the original string
            return arg_str

        # b) arguments as object (dict)
        if isinstance(args, dict):
            got = _extract_from_dict_once(args)
            if got:
                return got
            texts = []
            for container in ("parts", "data", "items", "content"):
                sub = args.get(container)
                if isinstance(sub, list):
                    texts.extend(_extract_from_list_flat(sub))
                elif isinstance(sub, dict):
                    got2 = _extract_from_dict_once(sub)
                    if got2:
                        texts.append(got2)
            if texts:
                return "\n\n".join(texts).strip()
            return json.dumps(args, ensure_ascii=False)

        # c) arguments as list (list)
        if isinstance(args, list):
            texts = _extract_from_list_flat(args)
            if texts:
                return "\n\n".join(texts).strip()
            return json.dumps(args, ensure_ascii=False)

        return ""

    @staticmethod
    def _clean_text(txt: str, drop_short_lines: bool = True) -> str:
        """Clean extracted text by removing page markers and optionally short lines."""
        res = txt
        res = re.sub('\nPage(.*?)\n', '', res)
        res = re.sub('\nDocuSign(.*?)\n', '', res)
        if drop_short_lines:
            res = re.sub('\n([^\n]{1,2})\n', '', res)
        return res

    @staticmethod
    def _get_chunks(input_string, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks for processing."""
        chunks = []
        temp_str = input_string
        while len(temp_str) > 0:
            chunks.append(temp_str[:chunk_size])
            temp_str = temp_str[chunk_size - overlap:]
        return chunks
   
    @staticmethod
    def _strip_latex_tables(s: str) -> str:
        """Gently flatten LaTeX tables to readable format without aggressive deletions."""
        if not isinstance(s, str) or not s:
            return s

        # 1) release ampersand that appeared literally in LaTeX
        s = s.replace(r'\&', '&')

        # 2) remove table wrapper (do not remove text)
        s = re.sub(r'\\begin\{tabular\*?\}\{[^}]*\}', '\n', s, flags=re.IGNORECASE)
        s = re.sub(r'\\end\{tabular\*?\}', '\n', s, flags=re.IGNORECASE)
        s = re.sub(r'\\begin\{array\}\{[^}]*\}', '\n', s, flags=re.IGNORECASE)
        s = re.sub(r'\\end\{array\}', '\n', s, flags=re.IGNORECASE)

        # 3) multicolumn/multirow – keep only the inner content
        s = re.sub(r'\\multicolumn\{\d+\}\{[^}]*\}\{([^}]*)\}', r'\1', s, flags=re.IGNORECASE)
        s = re.sub(r'\\multirow\{[^}]*\}\{[^}]*\}\{([^}]*)\}', r'\1', s, flags=re.IGNORECASE)

        # 4) rows/cells: line breaks in tables -> line break, columns & -> separator
        # first convert \\ (even if it is not at the end of the line)
        s = s.replace('\\\\\n', '\n')
        s = s.replace('\\\\', '\n')
        # convert & to separator ' | ' only when between non-empty characters (less false-positives)
        s = re.sub(r'(?m)(?<=\S)\s*&\s*(?=\S)', ' | ', s)

        # 5) remove table lines (hline/cline) only, do not remove other commands
        s = re.sub(r'\\hline', '', s, flags=re.IGNORECASE)
        s = re.sub(r'\\cline\{[^}]*\}', '', s, flags=re.IGNORECASE)

        # 6) remove common formatting wrappers but keep the text
        s = re.sub(r'\\textbf\{([^}]*)\}', r'\1', s, flags=re.IGNORECASE)
        s = re.sub(r'\\textit\{([^}]*)\}', r'\1', s, flags=re.IGNORECASE)

        # 7) align spaces and empty lines — still
        s = re.sub(r'[ \t]+\n', '\n', s)    # spaces at the end of line
        s = re.sub(r'\n{3,}', '\n\n', s)    # do not compress too much

        return s.strip()
