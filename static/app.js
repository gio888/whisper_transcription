class TranscriptionApp {
    constructor() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.progressSection = document.getElementById('progressSection');
        this.resultSection = document.getElementById('resultSection');
        this.errorSection = document.getElementById('errorSection');
        this.progressBar = document.getElementById('progressBar');
        this.progressContainer = document.querySelector('.progress-container');
        this.statusMessage = document.getElementById('statusMessage');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.transcriptPreview = document.getElementById('transcriptPreview');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.newFileBtn = document.getElementById('newFileBtn');
        this.retryBtn = document.getElementById('retryBtn');
        this.errorMessage = document.getElementById('errorMessage');
        this.errorHelp = document.getElementById('errorHelp');
        this.timeEstimate = document.getElementById('timeEstimate');
        
        this.currentSessionId = null;
        this.ws = null;
        this.uploadStartTime = null;
        this.audioDuration = null;
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Keyboard navigation for drop zone
        this.dropZone.addEventListener('keydown', (e) => {
            if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                this.fileInput.click();
            }
        });
        
        // Drag and drop events
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));
        
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('dragover');
        });
        
        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('dragover');
        });
        
        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) this.handleFileSelect(file);
        });
        
        // Button events
        this.downloadBtn.addEventListener('click', () => this.downloadTranscript());
        this.newFileBtn.addEventListener('click', () => this.reset());
        this.retryBtn.addEventListener('click', () => this.reset());
    }
    
    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
    
    async handleFileSelect(file) {
        if (!file) return;
        
        // Validate file type
        const validTypes = ['.m4a', '.mp3', '.wav', '.aac', '.mp4'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(fileExt)) {
            this.showError(
                `Invalid file type: ${fileExt}`,
                `Please upload an audio file in one of these formats: ${validTypes.join(', ')}. You can convert your file using online tools or audio editing software.`
            );
            return;
        }
        
        // Validate file size (500MB max)
        if (file.size > 500 * 1024 * 1024) {
            const actualSize = this.formatFileSize(file.size);
            this.showError(
                `File too large: ${actualSize}`,
                'Maximum file size is 500MB. Try compressing the audio or splitting it into smaller segments.'
            );
            return;
        }
        
        // Update UI
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        
        // Upload file
        await this.uploadFile(file);
    }
    
    async uploadFile(file) {
        this.showProgress();
        this.updateStatus('Uploading file...');
        this.uploadStartTime = Date.now();
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                if (response.status === 413) {
                    throw new Error('FILE_TOO_LARGE');
                } else if (response.status === 400) {
                    throw new Error('INVALID_FORMAT');
                }
                throw new Error(error.detail || 'Upload failed');
            }
            
            const data = await response.json();
            this.currentSessionId = data.session_id;
            
            // Estimate processing time
            this.estimateProcessingTime(file);
            
            // Connect WebSocket for progress updates
            this.connectWebSocket();
            
        } catch (error) {
            if (error.message === 'FILE_TOO_LARGE') {
                this.showError(
                    'File too large',
                    'Please upload a file smaller than 500MB. You can split long recordings into parts.'
                );
            } else if (error.message === 'INVALID_FORMAT') {
                this.showError(
                    'Invalid file format',
                    'Please upload an M4A, MP3, WAV, AAC, or MP4 audio file.'
                );
            } else if (error.message.includes('Failed to fetch')) {
                this.showError(
                    'Connection error',
                    'Could not connect to the server. Make sure the transcription service is running.'
                );
            } else {
                this.showError(
                    'Upload failed',
                    error.message
                );
            }
        }
    }
    
    connectWebSocket() {
        // Use dynamic host detection for production compatibility
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.currentSessionId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.updateStatus('Connected. Starting transcription...');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleProgressUpdate(data);
        };
        
        this.ws.onerror = (error) => {
            this.showError(
                'Connection lost',
                'Could not maintain connection to the server. Please check your network and try again.'
            );
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket connection closed');
        };
    }
    
    handleProgressUpdate(data) {
        switch (data.status) {
            case 'converting':
                this.updateStatus('Converting audio format...');
                this.updateProgress(data.progress * 0.1); // Show 0-10% for conversion
                break;
                
            case 'transcribing':
                const progress = 10 + data.progress * 0.9;
                this.updateProgress(progress);
                
                // Calculate time remaining
                if (this.uploadStartTime && data.progress > 0) {
                    const elapsed = (Date.now() - this.uploadStartTime) / 1000;
                    const estimatedTotal = (elapsed / (progress / 100));
                    const remaining = Math.max(0, estimatedTotal - elapsed);
                    
                    if (remaining > 60) {
                        const minutes = Math.ceil(remaining / 60);
                        this.updateStatus(`Transcribing... (about ${minutes} minute${minutes > 1 ? 's' : ''} remaining)`);
                    } else if (remaining > 10) {
                        this.updateStatus(`Transcribing... (less than a minute remaining)`);
                    } else {
                        this.updateStatus('Transcribing... (almost done)');
                    }
                } else {
                    this.updateStatus(data.message || 'Transcribing audio...');
                }
                break;
                
            case 'completed':
                this.updateProgress(100);
                this.updateStatus('Transcription complete!');
                this.showResult(data.transcript);
                break;
                
            case 'error':
                const errorMsg = data.error || 'Transcription failed';
                if (errorMsg.includes('model') || errorMsg.includes('whisper')) {
                    this.showError(
                        'Transcription engine error',
                        'The Whisper model may not be properly installed. Please run setup.sh to download the required model.'
                    );
                } else {
                    this.showError('Transcription failed', errorMsg);
                }
                break;
        }
    }
    
    updateStatus(message) {
        this.statusMessage.textContent = message;
    }
    
    updateProgress(percent) {
        this.progressBar.style.width = `${percent}%`;
        // Update ARIA attributes
        if (this.progressContainer) {
            this.progressContainer.setAttribute('aria-valuenow', Math.round(percent));
        }
    }
    
    showProgress() {
        this.dropZone.style.display = 'none';
        this.progressSection.style.display = 'block';
        this.resultSection.style.display = 'none';
        this.errorSection.style.display = 'none';
    }
    
    showResult(transcript) {
        this.progressSection.style.display = 'none';
        this.resultSection.style.display = 'block';
        
        // Show preview (first 500 chars)
        const preview = transcript.length > 500 
            ? transcript.substring(0, 500) + '...\n\n[Full transcript available in download]'
            : transcript;
        
        this.transcriptPreview.textContent = preview;
    }
    
    showError(title, helpText = '') {
        this.dropZone.style.display = 'none';
        this.progressSection.style.display = 'none';
        this.resultSection.style.display = 'none';
        this.errorSection.style.display = 'block';
        this.errorMessage.textContent = title;
        
        if (this.errorHelp && helpText) {
            this.errorHelp.textContent = helpText;
            this.errorHelp.style.display = 'block';
        } else if (this.errorHelp) {
            this.errorHelp.style.display = 'none';
        }
    }
    
    async downloadTranscript() {
        if (!this.currentSessionId) return;
        
        const url = `/download/${this.currentSessionId}`;
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcript_${this.currentSessionId}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
    
    reset() {
        this.dropZone.style.display = 'block';
        this.progressSection.style.display = 'none';
        this.resultSection.style.display = 'none';
        this.errorSection.style.display = 'none';
        
        this.fileInput.value = '';
        this.progressBar.style.width = '0%';
        this.currentSessionId = null;
        this.uploadStartTime = null;
        this.audioDuration = null;
        
        if (this.timeEstimate) {
            this.timeEstimate.textContent = '';
        }
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    estimateProcessingTime(file) {
        // Rough estimate: processing takes about the same time as audio duration
        // For M4A files, estimate ~1MB per minute of audio
        const estimatedMinutes = Math.ceil(file.size / (1024 * 1024));
        
        if (this.timeEstimate) {
            if (estimatedMinutes > 1) {
                this.timeEstimate.textContent = `Estimated processing time: ${estimatedMinutes} minutes (processing speed ≈ audio duration)`;
            } else {
                this.timeEstimate.textContent = 'Processing time: Less than a minute';
            }
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TranscriptionApp();
});