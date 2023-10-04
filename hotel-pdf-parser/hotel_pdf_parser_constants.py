from dataclasses import dataclass
from collections import namedtuple
DP = namedtuple("DP", ["inner", "outer"], defaults=["", ""])


@dataclass(frozen=True)
class FieldNames:
    CHARGEBACK_ID: DP = DP("chargeback_id", "chargebackId")
    VENUE_TITLE: DP = DP("vendor", "Listing/Venue Title")
    VENUE_ADDRESS: DP = DP("vendor_full_address", "Listing/venue address")
    VENDOR_PHONE: DP = DP("vendor_phone", "Vendor Phone")
    GUEST_FIRST_NAME: DP = DP("contact_first_name", "Guest First Name")
    GUEST_LAST_NAME: DP = DP("contact_last_name", "Guest Last Name")
    GUEST_FULL_NAME: DP = DP("customer_full_name", "Guest Full Name")
    BILLING_ADDRESS: DP = DP("billing_address", "Billing - Address 1")
    BILLING_CITY: DP = DP("Bellevue", "Billing - City")
    BILLING_STATE: DP = DP("billing_state", "Billing - State")
    BILLING_ZIP: DP = DP("billing_zip_code", "Billing - Zip")
    BILLING_COUNTRY: DP = DP("billing_country", "Billing - Country")
    CHECK_IN_DATE: DP = DP("check_in", "Order - Check In/entry (DateTime) start")
    CHECK_OUT_DATE: DP = DP("check_out", "Order - Check Out (DateTime)")


FIELD_NAMES = FieldNames()
