import { Component, signal, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService, ChatResponse } from '../../services/api.service';

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  meta?: { chunks_used: number; tokens_sent: number; response_time_ms: number };
}

@Component({
  selector: 'app-chat',
  imports: [FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css',
})
export class ChatComponent implements AfterViewChecked {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;

  messages = signal<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI Financial Copilot. Upload a bank statement first, then ask me anything about your finances. I can help you understand your spending patterns, find your top expenses, and more!',
      timestamp: new Date(),
    }
  ]);
  inputMessage = '';
  isLoading = signal(false);
  errorMessage = signal('');

  suggestedPrompts = [
    'How much did I spend this month?',
    'What are my top 5 expenses?',
    'Show my spending by category',
    'Do I have any unusual spending?',
    'What\'s my income vs expenses?',
    'Give me a monthly financial summary',
  ];

  private shouldScroll = false;

  constructor(private api: ApiService) {}

  ngAfterViewChecked() {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  sendMessage(content?: string) {
    const msg = (content || this.inputMessage).trim();
    if (!msg || this.isLoading()) return;

    this.inputMessage = '';
    this.errorMessage.set('');

    // Add user message
    this.messages.update(msgs => [...msgs, {
      role: 'user' as const,
      content: msg,
      timestamp: new Date(),
    }]);
    this.shouldScroll = true;

    // Send to API
    this.isLoading.set(true);
    this.api.chat(msg).subscribe({
      next: (res: ChatResponse) => {
        this.messages.update(msgs => [...msgs, {
          role: 'assistant' as const,
          content: res.reply,
          timestamp: new Date(),
          meta: {
            chunks_used: res.chunks_used,
            tokens_sent: res.tokens_sent,
            response_time_ms: res.response_time_ms,
          },
        }]);
        this.isLoading.set(false);
        this.shouldScroll = true;
      },
      error: (err) => {
        this.errorMessage.set(err.error?.detail || 'Failed to get AI response. Make sure you\'ve uploaded a PDF first.');
        this.isLoading.set(false);
        this.shouldScroll = true;
      },
    });
  }

  onKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  private scrollToBottom() {
    try {
      const el = this.messagesContainer?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    } catch {}
  }
}
