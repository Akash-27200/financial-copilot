import { Component, OnInit, signal, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { ApiService, InsightsResponse } from '../../services/api.service';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit, AfterViewInit {
  @ViewChild('incomeExpenseChart') incomeExpenseChart!: ElementRef<HTMLCanvasElement>;
  @ViewChild('categoryChart') categoryChart!: ElementRef<HTMLCanvasElement>;
  @ViewChild('trendChart') trendChart!: ElementRef<HTMLCanvasElement>;

  insights = signal<InsightsResponse | null>(null);
  isLoading = signal(true);
  errorMessage = signal('');

  private charts: Chart[] = [];

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadInsights();
  }

  ngAfterViewInit() {}

  loadInsights() {
    this.isLoading.set(true);
    this.api.getInsights().subscribe({
      next: (data) => {
        this.insights.set(data);
        this.isLoading.set(false);
        // Delay chart creation to after view update
        setTimeout(() => this.createCharts(data), 100);
      },
      error: (err) => {
        this.errorMessage.set(err.error?.detail || 'Failed to load insights. Upload a PDF first.');
        this.isLoading.set(false);
      },
    });
  }

  private getThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      text: isDark ? '#e2e8f0' : '#334155',
      grid: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
      tooltipBg: isDark ? '#1e293b' : '#ffffff',
    };
  }

  createCharts(data: InsightsResponse) {
    this.charts.forEach(c => c.destroy());
    this.charts = [];
    const colors = this.getThemeColors();

    // Income vs Expense Doughnut
    if (this.incomeExpenseChart?.nativeElement) {
      const chart1 = new Chart(this.incomeExpenseChart.nativeElement, {
        type: 'doughnut',
        data: {
          labels: ['Income', 'Expenses'],
          datasets: [{
            data: [data.total_income, data.total_expenses],
            backgroundColor: ['#22c55e', '#ef4444'],
            borderWidth: 0,
            hoverOffset: 8,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '65%',
          plugins: {
            legend: { position: 'bottom', labels: { color: colors.text, padding: 16, font: { size: 13 } } },
          },
        },
      });
      this.charts.push(chart1);
    }

    // Category Breakdown
    if (this.categoryChart?.nativeElement && data.category_breakdown) {
      const cats = Object.entries(data.category_breakdown).slice(0, 8);
      const palette = ['#3b82f6','#8b5cf6','#ec4899','#f59e0b','#22c55e','#06b6d4','#ef4444','#84cc16'];
      const chart2 = new Chart(this.categoryChart.nativeElement, {
        type: 'bar',
        data: {
          labels: cats.map(([k]) => k.charAt(0).toUpperCase() + k.slice(1)),
          datasets: [{
            label: 'Spending',
            data: cats.map(([, v]) => v),
            backgroundColor: palette.slice(0, cats.length),
            borderRadius: 6,
            barThickness: 32,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          plugins: {
            legend: { display: false },
          },
          scales: {
            x: { grid: { color: colors.grid }, ticks: { color: colors.text, callback: (v) => '₹' + Number(v).toLocaleString() } },
            y: { grid: { display: false }, ticks: { color: colors.text, font: { size: 13 } } },
          },
        },
      });
      this.charts.push(chart2);
    }

    // Monthly Trend
    if (this.trendChart?.nativeElement && data.monthly_trend.length > 0) {
      const chart3 = new Chart(this.trendChart.nativeElement, {
        type: 'line',
        data: {
          labels: data.monthly_trend.map(m => m.month),
          datasets: [
            {
              label: 'Income',
              data: data.monthly_trend.map(m => m.income),
              borderColor: '#22c55e',
              backgroundColor: 'rgba(34,197,94,0.08)',
              fill: true,
              tension: 0.4,
              pointRadius: 5,
              pointBackgroundColor: '#22c55e',
            },
            {
              label: 'Expenses',
              data: data.monthly_trend.map(m => m.expenses),
              borderColor: '#ef4444',
              backgroundColor: 'rgba(239,68,68,0.08)',
              fill: true,
              tension: 0.4,
              pointRadius: 5,
              pointBackgroundColor: '#ef4444',
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { color: colors.text, padding: 16, font: { size: 13 } } },
          },
          scales: {
            x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
            y: { grid: { color: colors.grid }, ticks: { color: colors.text, callback: (v) => '₹' + Number(v).toLocaleString() } },
          },
        },
      });
      this.charts.push(chart3);
    }
  }

  get savingsRate(): number {
    const ins = this.insights();
    if (!ins || ins.total_income === 0) return 0;
    return Math.round(((ins.total_income - ins.total_expenses) / ins.total_income) * 100);
  }
}
