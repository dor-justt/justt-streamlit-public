import json
from typing import List, Dict, Any, Optional
import os

from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

from hotel_pdf_parser_constants import FIELD_NAMES
from pdf_preprocessor import PDFPreprocessor

# Load environment variables early
load_dotenv()


class JusttHotelDP(BaseModel):
    """Pydantic schema: all fields Optional[str] to match downstream post-processing/CSV."""
    chargeback_id: Optional[str] = None
    vendor: Optional[str] = None
    vendor_full_address: Optional[str] = None
    vendor_phone: Optional[str] = None
    customer_full_name: Optional[str] = None
    contact_first_name: Optional[str] = None
    contact_last_name: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_zip_code: Optional[str] = None
    billing_country: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    order_number: Optional[str] = None
    transaction_amount: Optional[str] = None
    reservation_id: Optional[str] = None
    costumer_email: Optional[str] = None
    is_checked_in: Optional[str] = None
    is_contactless_checked_in: Optional[str] = None
    number_of_guests: Optional[str] = None
    number_of_nights: Optional[str] = None
    room_features: Optional[str] = None
    cancellation_date: Optional[str] = None
    transaction_method: Optional[str] = None
    returning_customer: Optional[str] = None
    booking_channel: Optional[str] = None
    credits_used: Optional[str] = None
    cardholder_verification_method: Optional[str] = None


class DataExtractor:
    # NVIDIA API constants (used only in the "just nvidia" path)
    NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL_VLM = "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"


    FIELD_GUIDANCE = {
        "vendor": "Full hotel/listing name exactly as printed on the receipt (no slogans).",
        "vendor_full_address": "Vendor full postal address as printed; do not include URLs.",
        "vendor_phone": "Vendor phone number as printed; must contain digits.(e.g.,123.123.1234, 123-123-1234)",
        "customer_full_name": "Guest full name exactly as on the receipt.",
        "contact_first_name": "Guest/contact first name (or empty if unknown).",
        "contact_last_name": "Guest/contact last name (or empty if unknown).",
        "billing_address": "Billing street/address line (if present).",
        "billing_city": "Billing city (if present).",
        "billing_state": "Billing state/region (if present).",
        "billing_zip_code": "Billing ZIP/postcode (if present).",
        "billing_country": "Billing country (if present).",
        "check_in": "Check-in datetime in ISO 8601 (yyyy-MM-dd'T'HH:mm:ss). If only a date exists, set time to 00:00:00.",
        "check_out": "Check-out datetime in ISO 8601 (yyyy-MM-dd'T'HH:mm:ss). If only a date exists, set time to 00:00:00.",
        "order_number": "Order number if explicitly shown; else empty.",
        "transaction_amount": "Total charge amount (numeric string, e.g., 485.35),(or empty if unknown)",
        "reservation_id": "Reservation/booking/folio/confirmation ID, if present.",
        "costumer_email": "Guest email; must contain '@' or be empty. empty if you can not find the email ",
        "is_checked_in": "True if guest actually checked in; False if 'no show'/'no-show'; empty if unknown.",
        "is_contactless_checked_in": "Yes if mobile/contactless check-in; No if physical check-in; empty if unknown, yes/no",
        "number_of_guests": "Total number of guests as an integer string (e.g., '2').(or empty if unknown)",
        "number_of_nights": "Total number of nights as an integer string (e.g., '3').check_out - check_in (2023-09-30T00:00:00 - 2023-09-27T00:00:00 = 3 nights) ",
        "room_features": "Room/listing features/description if shown; else empty.",
        "cancellation_date": "Cancellation datetime in ISO 8601 if cancelled; else empty.",
        "transaction_method": "the method by which the transaction was processed",
        "returning_customer": "Indication of returning customer (string) if shown; else empty.",
        "booking_channel": "Channel/provider used to book ; else empty.",
        "credits_used": "Credits used amount (numeric string) if shown; else empty, (or empty if unknown)",
        "cardholder_verification_method": "CVM used/not used (e.g., 'PIN', 'Signature', 'None'),(or empty if unknown)",
    }

    EXAMPLE_OBJ = {
        "chargeback_id": "",
        "vendor": "Hyatt House New Orleans/Downtown",
        "vendor_full_address": "1250 Poydras Street, New Orleans, LA 70113, United States",
        "vendor_phone": "504-648-3118",
        "customer_full_name": "Cassandra Wold",
        "contact_first_name": "Cassandra",
        "contact_last_name": "Wold",
        "billing_address": "123 Main St",
        "billing_city": "New Orleans",
        "billing_state": "LA",
        "billing_zip_code": "70113",
        "billing_country": "United States",
        "check_in": "2023-09-28T00:00:00",
        "check_out": "2023-09-30T00:00:00",
        "order_number": "",
        "transaction_amount": "",
        "reservation_id": "ABC12345",
        "costumer_email": "cassandra.wold@gmail.com",
        "is_checked_in": "True",
        "is_contactless_checked_in": "no",
        "number_of_guests": "1",
        "number_of_nights": "",
        "room_features": "King suite, kitchenette",
        "cancellation_date": "",
        "transaction_method": "Card Present",
        "returning_customer": "",
        "booking_channel": "",
        "credits_used": "",
        "cardholder_verification_method": ""
    }
    # System content for the two existing OCR->LLM paths (kept as-is)
    SYSTEM_CONTENT = (
        f"You are an assistant that helps extract data from text which is parsed from PDF invoices. "
        f"You will receive a text, and return a json with the following: "
        f"{{{FIELD_NAMES.VENUE_TITLE.inner}: <the full title of the vendor>, "
        f"{FIELD_NAMES.VENUE_ADDRESS.inner}: <the full address of the vendor>, "
        f"{FIELD_NAMES.VENDOR_PHONE.inner}: <the phone number of the vendor>, "
        f"{FIELD_NAMES.GUEST_FULL_NAME.inner}: <the full name of the customer>, "
        f"{FIELD_NAMES.GUEST_FIRST_NAME.inner}: <if the customer is an organization, this is the first name of the contact "
        f"for the customer. Otherwise, it is the first name of the customer>, "
        f"{FIELD_NAMES.GUEST_LAST_NAME.inner}: <if the customer is an organization, this is the last name of the contact "
        f"for the customer. Otherwise, it is the last name of the customer>, "
        f"{FIELD_NAMES.BILLING_ADDRESS.inner}: <the billing address of the customer>, "
        f"{FIELD_NAMES.BILLING_CITY.inner}: <the billing city of the customer>, "
        f"{FIELD_NAMES.BILLING_STATE.inner}: <the billing state of the customer>, "
        f"{FIELD_NAMES.BILLING_ZIP.inner}: <the billing zip code of the customer>, "
        f"{FIELD_NAMES.BILLING_COUNTRY.inner}: <the billing country of the customer>, "
        f"{FIELD_NAMES.CHECK_IN_DATE.inner}: <date and time of the check in, in ISO format yyyy-MM-dd'T'HH:mm:ss>, "
        f"{FIELD_NAMES.CHECK_OUT_DATE.inner}: <date and time of the check out, in ISO format yyyy-MM-dd'T'HH:mm:ss>, "
        f"{FIELD_NAMES.ORDER_NUMBER.inner}: <Leave this blank>, "
        f"{FIELD_NAMES.TRANSACTION_AMOUNT.inner}: <Leave this blank>, "
        f"{FIELD_NAMES.RESERVATION_ID.inner}: <the reservation id or booking id. if this information is missing leave this blank.>, "
        f"{FIELD_NAMES.COSTUMER_EMAIL.inner}: <the email address of the guest\\customer.>, "
        f"{FIELD_NAMES.IS_CHECKED_IN.inner}: <if the costumer checked in return True if not return False. if the text contains 'no show' or 'no-show' (case insensitive), then this is False>, "
        f"{FIELD_NAMES.IS_CONTACTLESS_CHECKED_IN.inner}: <if the costumer checked in via mobile or contactless return yes if the costumer checked in phisically return no.>, "
        f"{FIELD_NAMES.NUMBER_OF_GUESTS.inner}: <the total number of guests>, "
        f"{FIELD_NAMES.NUMBER_OF_NIGHTS.inner}: <the total number of nights>, "
        f"{FIELD_NAMES.ROOM_FEATURES.inner}: <the listing or room features>, "
        f"{FIELD_NAMES.CANCELLATION_DATE.inner}: <if the order was canceled, return the cancellation date>, "
        f"{FIELD_NAMES.TRANSACTION_METHOD.inner}: <the method by which the transaction was processed>, "
        f"{FIELD_NAMES.RETURNING_CUSTOMER.inner}: <an indication if the customer is a returning customer. Will be counted as a returning guest if they made more than 1 order using the same account>, "
        f"{FIELD_NAMES.BOOKING_CHANNEL.inner}: <the channel used by the cardholder to make the purchase/booking>, "
        f"{FIELD_NAMES.CREDITS_USED.inner}: <the amount of credits the customer used in this order>, "
        f"{FIELD_NAMES.CVM.inner}: <the Cardholder Verificaiton Method used (or not used) for the payment>, "
        "For each value in the json, if you can not get the answer, return an empty string. "
        "Your returned answer must always be a json as described"
    )

    @staticmethod
    def _to_dp_output(j: Dict[str, str]) -> Dict[str, str]:
        """Map validated JusttHotelDP keys to the DP keys (FIELD_NAMES.*.inner)."""
        return {
            FIELD_NAMES.VENUE_TITLE.inner: j.get("vendor", "") or "",
            FIELD_NAMES.VENUE_ADDRESS.inner: j.get("vendor_full_address", "") or "",
            FIELD_NAMES.VENDOR_PHONE.inner: j.get("vendor_phone", "") or "",
            FIELD_NAMES.GUEST_FULL_NAME.inner: j.get("customer_full_name", "") or "",
            FIELD_NAMES.GUEST_FIRST_NAME.inner: j.get("contact_first_name", "") or "",
            FIELD_NAMES.GUEST_LAST_NAME.inner: j.get("contact_last_name", "") or "",
            FIELD_NAMES.BILLING_ADDRESS.inner: j.get("billing_address", "") or "",
            FIELD_NAMES.BILLING_CITY.inner: j.get("billing_city", "") or "",
            FIELD_NAMES.BILLING_STATE.inner: j.get("billing_state", "") or "",
            FIELD_NAMES.BILLING_ZIP.inner: j.get("billing_zip_code", "") or "",
            FIELD_NAMES.BILLING_COUNTRY.inner: j.get("billing_country", "") or "",
            FIELD_NAMES.CHECK_IN_DATE.inner: j.get("check_in", "") or "",
            FIELD_NAMES.CHECK_OUT_DATE.inner: j.get("check_out", "") or "",
            FIELD_NAMES.ORDER_NUMBER.inner: j.get("order_number", "") or "",
            FIELD_NAMES.TRANSACTION_AMOUNT.inner: j.get("transaction_amount", "") or "",
            FIELD_NAMES.RESERVATION_ID.inner: j.get("reservation_id", "") or "",
            FIELD_NAMES.COSTUMER_EMAIL.inner: j.get("costumer_email", "") or "",
            FIELD_NAMES.IS_CHECKED_IN.inner: j.get("is_checked_in", "") or "",
            FIELD_NAMES.IS_CONTACTLESS_CHECKED_IN.inner: j.get("is_contactless_checked_in", "") or "",
            FIELD_NAMES.NUMBER_OF_GUESTS.inner: j.get("number_of_guests", "") or "",
            FIELD_NAMES.NUMBER_OF_NIGHTS.inner: j.get("number_of_nights", "") or "",
            FIELD_NAMES.ROOM_FEATURES.inner: j.get("room_features", "") or "",
            FIELD_NAMES.CANCELLATION_DATE.inner: j.get("cancellation_date", "") or "",
            FIELD_NAMES.TRANSACTION_METHOD.inner: j.get("transaction_method", "") or "",
            FIELD_NAMES.RETURNING_CUSTOMER.inner: j.get("returning_customer", "") or "",
            FIELD_NAMES.BOOKING_CHANNEL.inner: j.get("booking_channel", "") or "",
            FIELD_NAMES.CREDITS_USED.inner: j.get("credits_used", "") or "",
            FIELD_NAMES.CVM.inner: j.get("cardholder_verification_method", "") or "",
        }

    @staticmethod
    def _iso_pad_date(val: Any) -> str:
        """If val is YYYY-MM-DD, pad to YYYY-MM-DDT00:00:00; otherwise return as-is if string."""
        if not isinstance(val, str) or not val:
            return ""
        if len(val) == 10 and val[4] == "-" and val[7] == "-":
            return f"{val}T00:00:00"
        return val

    @staticmethod
    def extract_data(chunks):
        """
        OpenAI path (used by Tesseract OCR and NVIDIA OCR flows):
        - Sends a single user message with the first text chunk.
        - Requests a strict JSON object and returns it as a Python dict.
        - Downstream post-processing expects the same DP key-space.
        """
        client = OpenAI()  # uses OPENAI_API_KEY from env
        messages = [
            {"role": "system", "content": DataExtractor.SYSTEM_CONTENT},
            {"role": "user", "content": chunks[0]},
        ]
        chatbot_response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            temperature=0,
            messages=messages,
        )
        output = chatbot_response.choices[0].message.content
        result = json.loads(output)
        return result

    @staticmethod
    def extract_data_nvidia_vlm(image_list: List, max_pages: int = 6) -> Dict[str, Any]:
        """
        Path #3 ("just nvidia"): Direct vision-to-JSON using NVIDIA VLM.
        - No OCR step; pages are converted to images and sent with a compact prompt.
        - Single API request to NVIDIA chat completions with text-first + images content.
        - Response is expected to be a JSON object with EXACT_KEYS (schema keys).
        - If the model returns a flat object overlapping our schema, use it directly; otherwise, map from nested hotel/guest/stay/receipt.
        - Normalize values to strings, pad dates, validate with Pydantic, then convert to DP keys for downstream consistency.
        """
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("Missing NVIDIA_API_KEY env var")
        
        schema_keys = list(JusttHotelDP.model_fields.keys())
        guidance_lines = "\n".join(
            [f"- {k}: {DataExtractor.FIELD_GUIDANCE.get(k, '')}" for k in schema_keys]
        )
        prompt_text = (
            "You will see hotel receipt images.\n"
            "Extract ONLY the following fields as a single JSON object, with EXACTLY these keys (no extra keys).\n"
            "All values must be plain strings. If a field is unknown or not visible, return an empty string! Do not make up any information!.\n"
            "Dates must be ISO 8601: yyyy-MM-dd'T'HH:mm:ss (use 00:00:00 if time not shown).\n"
            "Do NOT copy headers/footers like 'Arrival', 'Departure', 'Page No.' or any marketing text.\n"
            "Do NOT include URLs inside addresses. Use only information visible on the receipt pages.\n"
            "\n"
            "Constraints:\n"
            "- transaction_amount and credits_used must be numeric strings (e.g., 485.35).\n"
            "- number_of_guests and number_of_nights must be integer strings (e.g., '1').\n"
            "- costumer_email must contain '@' or be empty.\n"
            "- vendor_phone must include digits or be empty.\n"
            "\n"
            "Fields and how to read them:\n"
            f"{guidance_lines}\n"
            "\n"
            "Return ONLY the JSON object, without any explanations.\n"
            "For each value in the json, if you can not get the answer, return an empty string.\n"
            "empty if you can not find the answer, dont take answer from the example output if you can not find the answer, make it empty string\n"
            f"EXACT_KEYS: {json.dumps(schema_keys)}\n"
            f"EXAMPLE_OUTPUT: {json.dumps(DataExtractor.EXAMPLE_OBJ, ensure_ascii=False)}"
        )

        content = [{"type": "text", "text": prompt_text}]
        for img in image_list[:max_pages]:
            b64, mime = PDFPreprocessor._pil_image_to_base64(img)
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
        messages = [{"role": "user", "content": content}]
        # ===== DEBUG: outgoing payload summary =====
        print("[JUST_NVIDIA][DEBUG] prompt length:", len(prompt_text), flush=True)
        print("[JUST_NVIDIA][DEBUG] images sent:", sum(1 for c in content if c.get("type") == "image_url"), flush=True)
        # נסה להדפיס את ה־mime והאורך של התמונה הראשונה
        first_img = next((c for c in content if c.get("type") == "image_url"), None)
        if first_img:
            url_str = first_img["image_url"]["url"]
            print("[JUST_NVIDIA][DEBUG] first image mime:", url_str.split(";")[0].replace("data:", ""), flush=True)
            print("[JUST_NVIDIA][DEBUG] first image b64 length:", len(url_str.split(",")[1]), flush=True)
        # הדפס מבנה כללי של messages
        print("[JUST_NVIDIA][DEBUG] messages structure:", {
            "roles": [m["role"] for m in messages],
            "content_types": [[x["type"] for x in m["content"]] for m in messages]
        }, flush=True)

        # Single API request to NVIDIA chat completions endpoint
        client = OpenAI(base_url=DataExtractor.NVIDIA_BASE_URL, api_key=api_key)
        # ===== DEBUG: client config =====
        print("[JUST_NVIDIA][DEBUG] base_url:", DataExtractor.NVIDIA_BASE_URL, flush=True)
        print("[JUST_NVIDIA][DEBUG] model:", DataExtractor.NVIDIA_MODEL_VLM, flush=True)
        print("[JUST_NVIDIA][DEBUG] api_key present:", bool(api_key), flush=True)

        
        r = client.chat.completions.create(
            model=DataExtractor.NVIDIA_MODEL_VLM,
            messages=messages,
            temperature=0,
            max_tokens=900,
            stream=False,
        )
        raw = r.choices[0].message.content

        print("[JUST_NVIDIA] Branch: JSON only", flush=True)
        print("[JUST_NVIDIA] RAW from NVIDIA:", raw, flush=True)

        # Parse JSON with a minimal fallback in case of leading/trailing text noise
        try:
            data = json.loads(raw)
        except Exception:
            s, e = raw.find("{"), raw.rfind("}")
            data = json.loads(raw[s:e+1]) if (s != -1 and e != -1 and e > s) else {}

        # If we got a list, take the first dict in it
        if isinstance(data, list):
            data = next((x for x in data if isinstance(x, dict)), {})
        if not isinstance(data, dict):
            data = {}

        # 2) Prefer flat response if there is any overlap with our schema (except chargeback_id)
        schema_set = set(schema_keys) - {"chargeback_id"}
        overlap = (set(data.keys()) & schema_set) if isinstance(data, dict) else set()

        if overlap:
            # Build a flat candidate directly from model output; missing fields -> ""
            candidate = {k: ("" if data.get(k) is None else data.get(k, "")) for k in schema_keys}
            # Soften dates in flat mode as well
            for dk in ("check_in", "check_out", "cancellation_date"):
                candidate[dk] = DataExtractor._iso_pad_date(candidate.get(dk, ""))
        else:
            # 3) Otherwise, map from the common nested structure: hotel/guest/stay/receipt
            hotel_val = data.get("hotel")
            hotel = hotel_val if isinstance(hotel_val, dict) else {}

            receipt_val = data.get("receipt")
            receipt = receipt_val if isinstance(receipt_val, dict) else {}

            guest_val = data.get("guest")
            guest = guest_val if isinstance(guest_val, dict) else {}

            stay_val = data.get("stay")
            stay = stay_val if isinstance(stay_val, dict) else {}

            mapped: Dict[str, Any] = {k: "" for k in schema_keys}

            # Vendor
            vendor_name = hotel.get("name") if isinstance(hotel.get("name"), str) else ""
            if not vendor_name and isinstance(hotel_val, str):
                vendor_name = hotel_val
            mapped["vendor"] = vendor_name or ""

            # Vendor address / phone
            mapped["vendor_full_address"] = (
                hotel.get("address") if isinstance(hotel.get("address"), str) else
                (receipt.get("address") if isinstance(receipt.get("address"), str) else "")
            )
            mapped["vendor_phone"] = (
                hotel.get("phone") if isinstance(hotel.get("phone"), str) else
                (receipt.get("phone") if isinstance(receipt.get("phone"), str) else "")
            )

            # Guest full name
            full_name = guest.get("name") if isinstance(guest.get("name"), str) else ""
            if not full_name and isinstance(receipt.get("payment"), dict):
                pay = receipt["payment"]
                if isinstance(pay.get("name"), str):
                    full_name = pay["name"]
            if not full_name and isinstance(data.get("signature"), str):
                full_name = data["signature"]
            mapped["customer_full_name"] = full_name or ""
            if mapped["customer_full_name"].strip():
                parts = mapped["customer_full_name"].strip().split()
                mapped["contact_first_name"] = parts[0] if len(parts) >= 1 else ""
                mapped["contact_last_name"] = parts[-1] if len(parts) >= 2 else ""

            # Reservation / IDs
            reservation_id = ""
            if isinstance(guest, dict):
                reservation_id = guest.get("confirmation_number") or guest.get("booking_number") or ""
            if not reservation_id and isinstance(stay, dict):
                reservation_id = stay.get("folio_number") or ""
            mapped["reservation_id"] = reservation_id or ""

            # Dates
            check_in_raw = ""
            if isinstance(stay.get("check_in"), str):
                check_in_raw = stay["check_in"]
            elif isinstance(receipt.get("date"), str):
                check_in_raw = receipt["date"]

            check_out_raw = ""
            if isinstance(stay.get("check_out"), str):
                check_out_raw = stay["check_out"]
            elif isinstance(stay.get("departure"), str):
                check_out_raw = stay["departure"]

            mapped["check_in"] = DataExtractor._iso_pad_date(check_in_raw)
            mapped["check_out"] = DataExtractor._iso_pad_date(check_out_raw)

            # Transaction method / amount (best-effort)
            method = ""
            if isinstance(receipt.get("payment"), dict) and isinstance(receipt["payment"].get("method"), str):
                method = receipt["payment"]["method"]
            mapped["transaction_method"] = method or ""

            amount = None
            if isinstance(receipt.get("total"), (str, int, float)):
                amount = receipt["total"]
            elif isinstance(data.get("total"), (str, int, float)):
                amount = data["total"]
            mapped["transaction_amount"] = str(amount) if amount is not None else ""

            # Use the mapped candidate
            candidate = mapped

        # 4) Normalize all values to strings and validate with Pydantic
        normalized: Dict[str, str] = {}
        for k in schema_keys:
            v = candidate.get(k, "")
            if v is None:
                v = ""
            elif isinstance(v, str):
                pass
            elif isinstance(v, (int, float, bool)):
                v = str(v)
            elif isinstance(v, dict):
                extracted = ""
                for key in ("datetime", "date", "value", "text", "raw"):
                    if isinstance(v.get(key), str) and v.get(key):
                        extracted = v[key]
                        break
                v = extracted if extracted else json.dumps(v, ensure_ascii=False)
            elif isinstance(v, (list, tuple)):
                if not v:
                    v = ""
                elif all(isinstance(x, str) for x in v):
                    v = "; ".join(v)
                else:
                    picked = ""
                    for x in v:
                        if isinstance(x, str) and x:
                            picked = x
                            break
                        if isinstance(x, dict):
                            for key in ("datetime", "date", "value", "text", "raw"):
                                if isinstance(x.get(key), str) and x.get(key):
                                    picked = x[key]
                                    break
                            if picked:
                                break
                    v = picked if picked else json.dumps(v, ensure_ascii=False)
            else:
                v = str(v)
            normalized[k] = v

        validated = JusttHotelDP.model_validate(normalized).model_dump()

        # 5) Return in DP key-space expected by the app
        return DataExtractor._to_dp_output(validated)
