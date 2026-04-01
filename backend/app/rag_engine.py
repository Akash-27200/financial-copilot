"""RAG Engine — Chunking, retrieval, and Groq AI integration."""

import time
import re
from collections import defaultdict
from groq import Groq
from app.logger import logger
from app.config import get_settings
from app.models import Transaction


class RAGEngine:
    """Retrieval-Augmented Generation engine for financial queries."""

    def __init__(self):
        self.transactions: list[Transaction] = []
        self.chunks: list[dict] = []
        self.client = None

    def _get_client(self) -> Groq:
        """Lazy-initialize Groq client."""
        if self.client is None:
            settings = get_settings()
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            logger.info("Groq client initialized")
        return self.client

    def load_transactions(self, transactions: list[Transaction]):
        """Load transactions and create chunks for retrieval."""
        self.transactions = transactions
        self.chunks = self._create_chunks(transactions)
        logger.info(f"RAG engine loaded {len(transactions)} transactions into {len(self.chunks)} chunks")

    def _create_chunks(self, transactions: list[Transaction]) -> list[dict]:
        """Create semantic chunks from transactions for retrieval."""
        chunks = []

        if not transactions:
            return chunks

        # Chunk 1: Summary overview
        total_income = sum(t.amount for t in transactions if t.type == "credit")
        total_expenses = sum(t.amount for t in transactions if t.type == "debit")
        summary_text = (
            f"FINANCIAL SUMMARY:\n"
            f"Total transactions: {len(transactions)}\n"
            f"Total income/credits: ₹{total_income:,.2f}\n"
            f"Total expenses/debits: ₹{total_expenses:,.2f}\n"
            f"Net balance change: ₹{total_income - total_expenses:,.2f}"
        )
        chunks.append({"type": "summary", "text": summary_text, "keywords": ["total", "summary", "overall", "balance", "income", "expense", "how much", "net"]})

        # Chunk 2: Category breakdown
        category_totals = defaultdict(float)
        category_counts = defaultdict(int)
        for t in transactions:
            if t.type == "debit":
                category_totals[t.category] += t.amount
                category_counts[t.category] += 1

        cat_lines = ["SPENDING BY CATEGORY:"]
        sorted_cats = sorted(category_totals.items(), key=lambda x: -x[1])
        for cat, total in sorted_cats:
            cat_lines.append(f"  {cat}: ₹{total:,.2f} ({category_counts[cat]} transactions)")
        cat_text = "\n".join(cat_lines)
        chunks.append({"type": "categories", "text": cat_text, "keywords": ["category", "categories", "spending", "where", "breakdown", "most", "top"]})

        # Chunk 3: Top expenses
        debits = sorted([t for t in transactions if t.type == "debit"], key=lambda x: -x.amount)
        top_lines = ["TOP EXPENSES (largest transactions):"]
        for t in debits[:15]:
            top_lines.append(f"  {t.date} — {t.description}: ₹{t.amount:,.2f} [{t.category}]")
        chunks.append({"type": "top_expenses", "text": "\n".join(top_lines), "keywords": ["top", "largest", "biggest", "expensive", "highest", "most spent"]})

        # Chunk 4: Income/Credits
        credits = [t for t in transactions if t.type == "credit"]
        if credits:
            credit_lines = ["INCOME / CREDITS:"]
            for t in credits:
                credit_lines.append(f"  {t.date} — {t.description}: ₹{t.amount:,.2f} [{t.category}]")
            chunks.append({"type": "income", "text": "\n".join(credit_lines), "keywords": ["income", "salary", "credit", "deposit", "earned", "received", "paid"]})

        # Chunk 5: By-month grouping
        month_groups = defaultdict(list)
        for t in transactions:
            # Extract month from date string
            month_key = t.date[:7] if len(t.date) >= 7 else t.date[:5]
            month_groups[month_key].append(t)

        for month, txns in sorted(month_groups.items()):
            month_income = sum(t.amount for t in txns if t.type == "credit")
            month_expense = sum(t.amount for t in txns if t.type == "debit")
            lines = [f"MONTH {month}: Income=₹{month_income:,.2f}, Expenses=₹{month_expense:,.2f}, Net=₹{month_income - month_expense:,.2f}"]
            for t in txns:
                lines.append(f"  {t.date} [{t.type}] {t.description}: ₹{t.amount:,.2f}")
            chunks.append({"type": "monthly", "text": "\n".join(lines), "keywords": ["month", month, "monthly", "trend", "time", "period", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]})

        # Chunk 6: All transactions detail (for specific queries)
        all_lines = ["ALL TRANSACTIONS:"]
        for t in transactions:
            all_lines.append(f"  {t.date} [{t.type}] {t.description}: ₹{t.amount:,.2f} [{t.category}]")
        chunks.append({"type": "all_transactions", "text": "\n".join(all_lines), "keywords": ["all", "every", "list", "show", "transactions", "detail"]})

        return chunks

    def _retrieve_relevant_chunks(self, query: str, max_chunks: int = 4) -> list[dict]:
        """Retrieve the most relevant chunks for a user query."""
        if not self.chunks:
            return []

        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))

        scored_chunks = []
        for chunk in self.chunks:
            score = 0
            # Keyword matching
            for keyword in chunk["keywords"]:
                if keyword in query_lower:
                    score += 3
                if keyword in query_words:
                    score += 1

            # Boost summary chunk slightly (always somewhat relevant)
            if chunk["type"] == "summary":
                score += 1

            scored_chunks.append((score, chunk))

        # Sort by score descending, take top chunks
        scored_chunks.sort(key=lambda x: -x[0])
        selected = [c for s, c in scored_chunks[:max_chunks] if s > 0]

        # Always include summary if nothing else matched well
        if not selected:
            selected = [c for c in self.chunks if c["type"] == "summary"]

        return selected

    def chat(self, user_query: str) -> dict:
        """Process a chat query using RAG."""
        logger.info(f"Chat query received: '{user_query}'")
        start_time = time.time()

        # Retrieve relevant chunks
        relevant_chunks = self._retrieve_relevant_chunks(user_query)
        logger.info(f"Selected {len(relevant_chunks)} relevant chunks: {[c['type'] for c in relevant_chunks]}")

        # Build context from chunks
        context_parts = [chunk["text"] for chunk in relevant_chunks]
        context = "\n\n".join(context_parts)

        # Build the prompt
        system_prompt = (
            "You are an expert AI Financial Copilot. You analyze bank transaction data and provide "
            "clear, actionable financial insights. Be specific with numbers, percentages, and amounts. "
            "Format your responses with bullet points and clear sections when appropriate. "
            "If the data doesn't contain enough information to fully answer, say so honestly. "
            "Always be helpful and provide practical financial advice.If user asked about other domain like weather, news, etc. then say that you are not able to answer that question as you can help only in finance related queries."
        )

        user_prompt = f"""Based on the following financial data, answer the user's question.

FINANCIAL DATA:
{context}

USER QUESTION: {user_query}

Provide a clear, detailed, and helpful response. Use specific numbers from the data."""

        # Estimate tokens (rough: 1 token ≈ 4 chars)
        total_chars = len(system_prompt) + len(user_prompt)
        estimated_tokens = total_chars // 4
        logger.info(f"Estimated tokens to send: {estimated_tokens}")

        try:
            client = self._get_client()
            settings = get_settings()

            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1024,
            )

            reply = response.choices[0].message.content
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            logger.info(f"AI response received in {elapsed_ms}ms")
            logger.info(f"Response length: {len(reply)} chars")

            return {
                "reply": reply,
                "chunks_used": len(relevant_chunks),
                "tokens_sent": estimated_tokens,
                "response_time_ms": elapsed_ms,
            }

        except Exception as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(f"Groq API call failed after {elapsed_ms}ms: {e}")
            raise


# Singleton instance
rag_engine = RAGEngine()
