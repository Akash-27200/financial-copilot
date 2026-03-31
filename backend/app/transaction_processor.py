"""Convert raw PDF text into structured transaction data."""

import re
import time
from typing import Optional
from app.logger import logger
from app.models import Transaction


# Category keywords mapping
CATEGORY_KEYWORDS = {
    "groceries": ["grocery", "supermarket", "walmart", "kroger", "aldi", "costco", "whole foods",
                   "trader joe", "safeway", "target", "food", "mart", "bigbasket", "blinkit",
                   "zepto", "dmart", "reliance fresh", "more supermarket", "swiggy instamart"],
    "dining": ["restaurant", "cafe", "coffee", "starbucks", "mcdonald", "pizza", "uber eats",
               "doordash", "grubhub", "dining", "eat", "lunch", "dinner", "breakfast",
               "zomato", "swiggy", "dominos", "kfc", "burger", "biryani", "sweets", "hotel",
               "dhaba", "bakery", "chai", "tea", "nasta", "nashta", "juice"],
    "transportation": ["uber", "lyft", "gas", "fuel", "parking", "toll", "metro", "transit",
                        "bus", "train", "airline", "flight", "taxi", "shell", "chevron", "bp",
                        "ola", "rapido", "irctc", "petrol", "diesel", "fastag"],
    "utilities": ["electric", "water", "gas bill", "internet", "phone", "mobile", "att",
                   "verizon", "comcast", "utility", "sewage", "trash", "jio", "airtel",
                   "vodafone", "bsnl", "broadband", "wifi", "electricity", "bijli",
                   "mahadiscom", "bescom", "tata power"],
    "entertainment": ["netflix", "spotify", "hulu", "disney", "movie", "theater", "gaming",
                       "steam", "xbox", "playstation", "youtube", "amazon prime", "hbo",
                       "hotstar", "zee5", "sonyliv", "gaana", "pvr", "inox", "bookmyshow"],
    "shopping": ["amazon", "ebay", "etsy", "mall", "store", "shop", "clothing", "nike",
                  "adidas", "zara", "h&m", "best buy", "apple store", "flipkart", "myntra",
                  "ajio", "meesho", "nykaa", "croma", "reliance digital"],
    "healthcare": ["pharmacy", "hospital", "doctor", "medical", "health", "dental", "cvs",
                    "walgreens", "insurance", "clinic", "lab", "apollo", "medplus",
                    "1mg", "pharmeasy", "netmeds", "practo"],
    "housing": ["rent", "mortgage", "property", "maintenance", "repair", "home", "apartment",
                "society", "flat", "pg"],
    "education": ["tuition", "school", "university", "college", "book", "course", "udemy",
                   "coursera", "education", "byju", "unacademy", "coaching"],
    "subscriptions": ["subscription", "membership", "monthly", "annual", "premium"],
    "transfer": ["transfer", "zelle", "venmo", "paypal", "wire", "ach", "upi", "neft",
                  "imps", "rtgs", "bhim", "paytm", "phonepe", "googlepay", "gpay"],
    "salary": ["salary", "payroll", "direct deposit", "wage", "income", "bonus"],
    "investment": ["dividend", "interest", "investment", "stock", "mutual fund", "etf",
                    "zerodha", "groww", "upstox", "sip", "fd", "fixed deposit", "sweep"],
    "atm": ["atm", "atw", "atl", "cash withdrawal", "cdm", "cash deposit"],
}


def categorize_transaction(description: str) -> str:
    """Categorize a transaction based on description keywords."""
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    return "other"


def parse_amount(amount_str: str) -> Optional[float]:
    """Parse amount string to float, handling various formats."""
    try:
        cleaned = re.sub(r'[^\d.\-,]', '', amount_str)
        cleaned = cleaned.replace(',', '')
        if cleaned and cleaned != '-' and cleaned != '.':
            return abs(float(cleaned))
    except (ValueError, TypeError):
        return None
    return None


def process_transactions(raw_text: str) -> list[Transaction]:
    """Parse raw bank statement text into structured transactions.

    Supports multiple bank statement formats:
    - Indian banks (Kotak, SBI, HDFC, ICICI): DD Mon YYYY format
    - International banks: MM/DD/YYYY, DD-MM-YYYY formats
    """
    logger.info("Transaction processing started")
    start_time = time.time()

    transactions = []
    invalid_rows = 0
    lines = raw_text.strip().split('\n')
    total_lines = len(lines)

    # ── Multiple date patterns ──────────────────────────────────────
    # Pattern 1: DD Mon YYYY (e.g., "02 Mar 2026") — Indian banks
    date_pattern_dmy_text = re.compile(
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        re.IGNORECASE
    )
    # Pattern 2: DD/MM/YYYY or MM/DD/YYYY with separators
    date_pattern_sep = re.compile(
        r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})'
    )
    # Pattern 3: YYYY-MM-DD (ISO format)
    date_pattern_iso = re.compile(
        r'(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})'
    )

    # ── Indian bank statement pattern ───────────────────────────────
    # Format: [Sr.No] [DD Mon YYYY] [Description] [Amount1] [Amount2(Balance)]
    # Example: "1 02 Mar 2026 UPI/GAURAV NITIN KA/... 4,000.00 28,508.00"
    indian_bank_pattern = re.compile(
        r'^\s*(\d{1,4})\s+'                                              # Sr.No
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s+'  # Date
        r'(.+?)\s+'                                                       # Description
        r'([\d,]+\.\d{2})\s+'                                            # Amount (Debit or Credit)
        r'([\d,]+\.\d{2})\s*$',                                          # Balance
        re.IGNORECASE
    )

    # ── Detect which column is Debit/Credit ─────────────────────────
    # Look for header row to determine column order
    has_separate_dr_cr_columns = False
    dr_col_first = True  # Default: Withdrawal(Dr.) comes before Deposit(Cr.)
    for line in lines:
        line_lower = line.lower()
        if 'withdrawal' in line_lower or 'debit' in line_lower:
            if 'deposit' in line_lower or 'credit' in line_lower:
                has_separate_dr_cr_columns = True
                # Check column order
                dr_pos = line_lower.find('withdrawal') if 'withdrawal' in line_lower else line_lower.find('debit')
                cr_pos = line_lower.find('deposit') if 'deposit' in line_lower else line_lower.find('credit')
                dr_col_first = dr_pos < cr_pos
                logger.info(f"Detected header: Dr/Cr columns, Dr-first={dr_col_first}")
                break

    # ── Skip lines patterns ─────────────────────────────────────────
    skip_patterns = [
        'account no', 'account statement', 'account summary', 'opening balance',
        'closing balance', 'statement generated', 'page', 'end of statement',
        'any discrepancy', 'system generated', 'contact us', 'remember',
        'commonly used', 'important information', 'rbi mandates', 'kotak mahindra bank',
        'registered office', 'scan for', 'never share', 'goods and service',
        'please note', 'corporate salary', 'deposits of up to', 'complimentary',
        'starting december', 'from october', 'in order to avail',
        'particulars', 'total balance', 'activmoney',
        'ap - autopay', 'atl - atm', 'atw - atm', 'bp - bill',
        'cdm - kotak', 'cms - cash', 'ib - transaction', 'imps - immediate',
        'imt - instant', 'kb - billpay', 'mb - transaction', 'nach - national',
        'neft - national', 'netcard', 'os - online', 'ot - online',
        'pb - transaction', 'pci/pcd', 'rtgs - real', 'upi - unified',
        'visaccpay', 'vmt - visa', 'wb - billpay', 'int. pd.',
        'sweep transfer to', 'sweep transfer from',
        'date', 'description', 'balance',  # generic headers
    ]

    # ── Process each line ───────────────────────────────────────────
    continuation_buffer = ""  # For multiline descriptions

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or len(line) < 5:
            continue

        # Skip header/footer/info lines
        line_lower = line.lower()
        should_skip = False
        for pattern in skip_patterns:
            if pattern in line_lower:
                should_skip = True
                break
        if should_skip:
            continue

        # ── Try Indian bank format first ────────────────────────────
        match = indian_bank_pattern.match(line)
        if match:
            sr_no = match.group(1)
            date_str = match.group(2).strip()
            description = match.group(3).strip()
            amount_str = match.group(4).strip()
            balance_str = match.group(5).strip()

            amount_val = parse_amount(amount_str)
            if amount_val is None:
                logger.warning(f"Line {line_num}: Invalid amount '{amount_str}' — '{line[:60]}'")
                invalid_rows += 1
                continue

            # Determine debit/credit based on balance change or keywords
            is_debit = _is_debit_transaction(description, amount_val, balance_str, transactions)

            txn_type = "debit" if is_debit else "credit"
            category = categorize_transaction(description)
            if txn_type == "credit" and category == "other":
                category = "income"

            transactions.append(Transaction(
                date=date_str,
                description=_clean_description(description),
                amount=amount_val,
                type=txn_type,
                category=category,
                raw_text=line,
            ))
            logger.info(f"  Txn #{sr_no}: {date_str} | {txn_type} | ₹{amount_val:,.2f} | {description[:40]}")
            continue

        # ── Try generic format with date patterns ───────────────────
        date_match = None
        for pattern in [date_pattern_dmy_text, date_pattern_sep, date_pattern_iso]:
            date_match = pattern.search(line)
            if date_match:
                break

        if not date_match:
            # This might be a continuation line for the previous transaction
            if transactions and not any(c.isdigit() for c in line[:3]):
                # Append to previous transaction's description
                prev = transactions[-1]
                transactions[-1] = Transaction(
                    date=prev.date,
                    description=_clean_description(prev.description + " " + line),
                    amount=prev.amount,
                    type=prev.type,
                    category=prev.category,
                    raw_text=prev.raw_text,
                )
            continue

        date_str = date_match.group(1)

        # Find amounts in the line
        amount_pattern = re.compile(r'[\d,]+\.\d{2}')
        amounts = amount_pattern.findall(line[date_match.end():])
        if not amounts:
            logger.warning(f"Line {line_num}: No amount found — '{line[:60]}'")
            invalid_rows += 1
            continue

        # Extract description
        remaining = line[date_match.end():].strip()
        # Remove all amounts from the text to get description
        desc = remaining
        for amt in amounts:
            desc = desc.replace(amt, '', 1).strip()
        desc = re.sub(r'\s+', ' ', desc).strip(' -,')

        if not desc:
            desc = "Unknown Transaction"

        # Use the first amount as transaction amount (last is typically balance)
        if len(amounts) >= 2:
            amount_val = parse_amount(amounts[0])
            # Balance is amounts[-1]
        else:
            amount_val = parse_amount(amounts[0])

        if amount_val is None or amount_val == 0:
            invalid_rows += 1
            continue

        is_debit = _is_debit_transaction(desc, amount_val, amounts[-1] if amounts else "0", transactions)

        txn_type = "debit" if is_debit else "credit"
        category = categorize_transaction(desc)
        if txn_type == "credit" and category == "other":
            category = "income"

        transactions.append(Transaction(
            date=date_str,
            description=_clean_description(desc),
            amount=amount_val,
            type=txn_type,
            category=category,
            raw_text=line,
        ))

    elapsed = round((time.time() - start_time) * 1000, 2)
    logger.info(f"Transaction processing completed in {elapsed}ms")
    logger.info(f"  Total records: {len(transactions)}")
    logger.info(f"  Invalid/skipped rows: {invalid_rows}")
    logger.info(f"  Lines processed: {total_lines}")

    if not transactions:
        logger.warning("No transactions could be extracted from the PDF text")

    return transactions


def _is_debit_transaction(description: str, amount: float, balance_str: str,
                           prev_transactions: list[Transaction]) -> bool:
    """Determine if a transaction is debit or credit using multiple signals."""
    desc_lower = description.lower()

    # Credit indicators (keywords)
    credit_keywords = [
        'salary', 'payroll', 'deposit', 'credit', 'refund', 'cashback',
        'interest', 'dividend', 'received', 'reversed', 'reversal',
        'int. pd', 'int.pd', 'neft cr', 'imps cr', 'by transfer',
    ]
    for kw in credit_keywords:
        if kw in desc_lower:
            return False  # It's a credit

    # Debit indicators
    debit_keywords = [
        'withdrawal', 'purchase', 'payment', 'paid', 'debit',
        'atm', 'pos', 'emi', 'bill', 'charge', 'fee',
    ]
    for kw in debit_keywords:
        if kw in desc_lower:
            return True  # It's a debit

    # Balance heuristic: if we have previous transactions, check if balance went up or down
    if prev_transactions:
        prev_balance_str = None
        # Try to parse balance from prev raw_text
        prev_raw = prev_transactions[-1].raw_text or ""
        amounts_in_prev = re.findall(r'[\d,]+\.\d{2}', prev_raw)
        if amounts_in_prev:
            prev_balance = parse_amount(amounts_in_prev[-1])
            curr_balance = parse_amount(balance_str)
            if prev_balance is not None and curr_balance is not None:
                if curr_balance > prev_balance:
                    return False  # Balance went up → credit
                elif curr_balance < prev_balance:
                    return True  # Balance went down → debit

    # Default: UPI and most transactions are debits
    return True


def _clean_description(desc: str) -> str:
    """Clean up transaction description for display."""
    # Remove extra spaces
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Remove trailing UPI reference numbers if too long
    desc = re.sub(r'\s*UPI-\d{10,}', '', desc)
    # Clean up slashes at end
    desc = desc.strip(' /')
    return desc
