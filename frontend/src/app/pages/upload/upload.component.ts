import { Component, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService, UploadResponse } from '../../services/api.service';

@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.css',
})
export class UploadComponent {
  isDragging = signal(false);
  isUploading = signal(false);
  uploadResult = signal<UploadResponse | null>(null);
  errorMessage = signal('');
  selectedFile = signal<File | null>(null);

  constructor(private api: ApiService, private router: Router) {}

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(false);
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.handleFile(files[0]);
    }
  }

  onFileSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFile(input.files[0]);
    }
  }

  handleFile(file: File) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      this.errorMessage.set('Please select a PDF file');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage.set('File size must be under 10MB');
      return;
    }
    this.errorMessage.set('');
    this.selectedFile.set(file);
  }

  upload() {
    const file = this.selectedFile();
    if (!file) return;

    this.isUploading.set(true);
    this.errorMessage.set('');

    this.api.uploadPdf(file).subscribe({
      next: (res) => {
        this.uploadResult.set(res);
        this.isUploading.set(false);
      },
      error: (err) => {
        this.errorMessage.set(err.error?.detail || 'Upload failed. Please try again.');
        this.isUploading.set(false);
      },
    });
  }

  goToChat() { this.router.navigate(['/chat']); }
  goToDashboard() { this.router.navigate(['/dashboard']); }

  formatBytes(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }
}
