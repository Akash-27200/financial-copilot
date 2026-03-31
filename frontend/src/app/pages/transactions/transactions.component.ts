import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TitleCasePipe } from '@angular/common';
import { ApiService, Transaction } from '../../services/api.service';

@Component({
  selector: 'app-transactions',
  imports: [FormsModule, TitleCasePipe],
  templateUrl: './transactions.component.html',
  styleUrl: './transactions.component.css',
})
export class TransactionsComponent implements OnInit {
  transactions = signal<Transaction[]>([]);
  filteredTransactions = signal<Transaction[]>([]);
  isLoading = signal(true);
  errorMessage = signal('');
  searchQuery = '';
  categoryFilter = '';
  typeFilter = '';
  totalIncome = signal(0);
  totalExpenses = signal(0);

  categories = signal<string[]>([]);

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadTransactions();
  }

  loadTransactions() {
    this.isLoading.set(true);
    this.api.getTransactions().subscribe({
      next: (data) => {
        this.transactions.set(data.transactions);
        this.filteredTransactions.set(data.transactions);
        this.totalIncome.set(data.total_income);
        this.totalExpenses.set(data.total_expenses);

        const cats = [...new Set(data.transactions.map(t => t.category))].sort();
        this.categories.set(cats);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.errorMessage.set(err.error?.detail || 'Failed to load transactions. Upload a PDF first.');
        this.isLoading.set(false);
      },
    });
  }

  applyFilters() {
    let result = this.transactions();
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase();
      result = result.filter(t => t.description.toLowerCase().includes(q) || t.date.includes(q));
    }
    if (this.categoryFilter) {
      result = result.filter(t => t.category === this.categoryFilter);
    }
    if (this.typeFilter) {
      result = result.filter(t => t.type === this.typeFilter);
    }
    this.filteredTransactions.set(result);
  }

  exportCsv() {
    this.api.exportCsv().subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'transactions.csv';
        a.click();
        URL.revokeObjectURL(url);
      },
      error: () => {
        this.errorMessage.set('Failed to export CSV');
      },
    });
  }

  clearFilters() {
    this.searchQuery = '';
    this.categoryFilter = '';
    this.typeFilter = '';
    this.filteredTransactions.set(this.transactions());
  }
}
