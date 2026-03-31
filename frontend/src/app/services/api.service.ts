import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Transaction {
  date: string;
  description: string;
  amount: number;
  type: 'debit' | 'credit';
  category: string;
  raw_text?: string;
}

export interface UploadResponse {
  message: string;
  total_transactions: number;
  total_income: number;
  total_expenses: number;
  file_name: string;
}

export interface ChatResponse {
  reply: string;
  chunks_used: number;
  tokens_sent: number;
  response_time_ms: number;
}

export interface TransactionsResponse {
  transactions: Transaction[];
  total_count: number;
  total_income: number;
  total_expenses: number;
}

export interface InsightsResponse {
  total_income: number;
  total_expenses: number;
  net_balance: number;
  category_breakdown: { [key: string]: number };
  monthly_trend: { month: string; income: number; expenses: number; net: number }[];
  top_expenses: { date: string; description: string; amount: number; category: string }[];
  unusual_spending: { date: string; description: string; amount: number; category: string; avg_for_category: number; deviation: number }[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  uploadPdf(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(`${this.baseUrl}/upload-pdf`, formData);
  }

  getTransactions(category?: string, type?: string): Observable<TransactionsResponse> {
    let params = new HttpParams();
    if (category) params = params.set('category', category);
    if (type) params = params.set('type', type);
    return this.http.get<TransactionsResponse>(`${this.baseUrl}/transactions`, { params });
  }

  exportCsv(): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/transactions?format=csv`, {
      responseType: 'blob',
    });
  }

  chat(message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.baseUrl}/chat`, { message });
  }

  getInsights(): Observable<InsightsResponse> {
    return this.http.get<InsightsResponse>(`${this.baseUrl}/insights`);
  }
}
