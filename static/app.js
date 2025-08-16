class TranscriptionApp {
    constructor() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        
        // Single file elements (legacy support)
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
        
        // Batch elements
        this.batchSection = document.getElementById('batchSection');
        this.batchTotal = document.getElementById('batchTotal');
        this.batchCompleted = document.getElementById('batchCompleted');
        this.batchFailed = document.getElementById('batchFailed');
        this.batchProgressBar = document.getElementById('batchProgressBar');
        this.batchStatus = document.getElementById('batchStatus');
        this.currentFileSection = document.getElementById('currentFileSection');
        this.currentFileName = document.getElementById('currentFileName');
        this.currentFileProgress = document.getElementById('currentFileProgress');
        this.currentFileProgressBar = document.getElementById('currentFileProgressBar');
        this.currentFileStatus = document.getElementById('currentFileStatus');
        this.toggleQueue = document.getElementById('toggleQueue');
        this.fileQueue = document.getElementById('fileQueue');
        
        // Processing folder elements
        this.processingFolderSection = document.getElementById('processingFolderSection');
        this.chooseFolderBtn = document.getElementById('chooseFolderBtn');
        this.selectedFolder = document.getElementById('selectedFolder');
        this.selectedFolderPath = document.getElementById('selectedFolderPath');
        this.folderStatus = document.getElementById('folderStatus');
        
        // State management
        this.currentSessionId = null;
        this.currentBatchId = null;
        this.ws = null;
        this.uploadStartTime = null;
        this.isBatchMode = false;
        this.batchFiles = [];
        this.outputFolderHandle = null;
        
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
        this.fileInput.addEventListener('change', (e) => this.handleFilesSelect(e.target.files));
        
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
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                // Access original file paths for batch processing
                const fileData = Array.from(files).map(file => {
                    // Try to get original path from file system access
                    const originalPath = file.path || file.webkitRelativePath || null;
                    return {
                        file: file,
                        originalPath: originalPath
                    };
                });
                this.handleFilesSelect(files, fileData);
            }
        });
        
        // Button events
        this.downloadBtn?.addEventListener('click', () => this.downloadTranscript());
        this.newFileBtn?.addEventListener('click', () => this.reset());
        this.retryBtn?.addEventListener('click', () => this.reset());
        
        // Batch UI events
        this.toggleQueue?.addEventListener('click', () => this.toggleQueueVisibility());
        
        // Processing folder events
        this.chooseFolderBtn?.addEventListener('click', () => this.chooseFolderHandler());
    }
    
    handleFilesSelect(files, fileData = null) {
        if (!files || files.length === 0) return;
        
        const fileArray = Array.from(files);
        
        // Determine if this is batch mode
        this.isBatchMode = fileArray.length > 1;
        
        if (this.isBatchMode) {
            this.handleBatchUpload(fileArray, fileData);
        } else {
            // Single file mode (legacy)
            this.handleSingleFileUpload(fileArray[0]);
        }
    }
    
    async handleSingleFileUpload(file) {
        // Validate file
        const validTypes = ['.m4a', '.mp3', '.wav', '.aac', '.mp4'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(fileExt)) {
            this.showError(
                `Invalid file type: ${fileExt}`,
                `Please upload an audio file in one of these formats: ${validTypes.join(', ')}.`
            );
            return;
        }
        
        if (file.size > 500 * 1024 * 1024) {
            const actualSize = this.formatFileSize(file.size);
            this.showError(
                `File too large: ${actualSize}`,
                'Maximum file size is 500MB. Try compressing the audio.'
            );
            return;
        }
        
        // Update UI for single file
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        
        // Upload single file
        await this.uploadSingleFile(file);
    }
    
    async handleBatchUpload(files, fileData = null) {
        // Validate all files
        const validFiles = [];
        const validTypes = ['.m4a', '.mp3', '.wav', '.aac', '.mp4'];
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileExt = '.' + file.name.split('.').pop().toLowerCase();
            
            if (validTypes.includes(fileExt) && file.size <= 500 * 1024 * 1024) {
                validFiles.push({
                    file: file,
                    originalPath: fileData ? fileData[i]?.originalPath : null
                });
            }
        }
        
        if (validFiles.length === 0) {
            this.showError(
                'No valid files',
                'Please upload audio files in supported formats (M4A, MP3, WAV, AAC, MP4) under 500MB each.'
            );
            return;
        }
        
        // Show batch interface
        this.showBatchInterface();
        
        // Upload batch
        await this.uploadBatchFiles(validFiles);
    }
    
    async uploadSingleFile(file) {
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
                throw new Error('Upload failed');
            }
            
            const data = await response.json();
            this.currentSessionId = data.session_id;
            
            // Connect WebSocket for single file progress
            this.connectSingleFileWebSocket();
            
        } catch (error) {
            this.showError('Upload failed', error.message);
        }
    }
    
    async uploadBatchFiles(validFiles) {
        this.updateBatchStatus('Uploading files...');
        this.uploadStartTime = Date.now();
        
        const formData = new FormData();
        validFiles.forEach(fileData => {
            formData.append('files', fileData.file);
        });
        
        try {
            const response = await fetch('/batch-upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Batch upload failed');
            }
            
            const data = await response.json();
            this.currentBatchId = data.batch_id;
            this.batchFiles = data.files.map((file, index) => ({
                ...file,
                originalPath: validFiles[index]?.originalPath
            }));
            
            // Update batch UI
            this.updateBatchStats(data.files_count, 0, 0);
            this.populateFileQueue();
            
            // Show folder selection during processing
            this.processingFolderSection.style.display = 'block';
            
            // Auto-start processing
            this.updateBatchStatus('Processing files...');
            this.connectBatchWebSocket();
            
        } catch (error) {
            this.showError('Batch upload failed', error.message);
        }
    }
    
    connectSingleFileWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.currentSessionId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.updateStatus('Connected. Starting transcription...');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleSingleFileProgress(data);
        };
        
        this.ws.onerror = () => {
            this.showError('Connection lost', 'Could not connect to the server.');
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket connection closed');
        };
    }
    
    connectBatchWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/batch/${this.currentBatchId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.updateBatchStatus('Connected. Starting batch transcription...');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleBatchProgress(data);
        };
        
        this.ws.onerror = () => {
            this.showError('Connection lost', 'Could not connect to the server.');
        };
        
        this.ws.onclose = () => {
            console.log('Batch WebSocket connection closed');
        };
    }
    
    handleSingleFileProgress(data) {
        // Handle single file progress (legacy behavior)
        switch (data.status) {
            case 'converting':
                this.updateStatus('Converting audio format...');
                this.updateProgress(data.progress * 0.1);
                break;
                
            case 'transcribing':
                const progress = 10 + data.progress * 0.9;
                this.updateProgress(progress);
                this.updateStatus(data.message || 'Transcribing audio...');
                break;
                
            case 'completed':
                this.updateProgress(100);
                this.updateStatus('Transcription complete!');
                this.showResult(data.transcript);
                break;
                
            case 'error':
                this.showError('Transcription failed', data.error);
                break;
        }
    }
    
    handleBatchProgress(data) {
        switch (data.type) {
            case 'batch_status':
                this.updateBatchStats(data.total_files, data.completed_files, data.failed_files);
                break;
                
            case 'file_start':
                this.updateCurrentFile(data.file_name, data.file_index);
                this.updateFileStatus(data.file_id, 'processing', 0);
                break;
                
            case 'file_progress':
                if (data.file_id) {
                    this.updateFileStatus(data.file_id, data.status, data.progress || 0);
                    this.updateCurrentFileProgress(data.progress || 0, data.message);
                }
                break;
                
            case 'file_complete':
                this.updateFileStatus(data.file_id, data.status, 100, data.error_message);
                
                // Store transcript content and save immediately if completed
                const batchFile = this.batchFiles.find(f => f.id === data.file_id);
                if (batchFile && data.status === 'completed' && data.transcript) {
                    batchFile.transcript = data.transcript;
                    batchFile.status = data.status;
                    
                    // Save file immediately - either to folder or download
                    this.saveCompletedTranscript(batchFile.name, data.transcript);
                }
                break;
                
            case 'batch_complete':
                this.updateBatchStats(data.total_files, data.completed_files, data.failed_files);
                this.updateBatchStatus(`Batch complete! ${data.completed_files} of ${data.total_files} files processed successfully.`);
                this.currentFileSection.style.display = 'none';
                
                // Hide folder selection since processing is done
                if (this.processingFolderSection) {
                    this.processingFolderSection.style.display = 'none';
                }
                break;
        }
    }
    
    // UI Update Methods
    showProgress() {
        this.dropZone.style.display = 'none';
        this.progressSection.style.display = 'block';
        this.resultSection.style.display = 'none';
        this.errorSection.style.display = 'none';
        this.batchSection.style.display = 'none';
    }
    
    showBatchInterface() {
        this.dropZone.style.display = 'none';
        this.progressSection.style.display = 'none';
        this.resultSection.style.display = 'none';
        this.errorSection.style.display = 'none';
        this.batchSection.style.display = 'block';
    }
    
    showResult(transcript) {
        this.progressSection.style.display = 'none';
        this.batchSection.style.display = 'none';
        this.resultSection.style.display = 'block';
        
        const preview = transcript.length > 500 
            ? transcript.substring(0, 500) + '...\n\n[Full transcript available in download]'
            : transcript;
        
        this.transcriptPreview.textContent = preview;
    }
    
    showError(title, helpText = '') {
        this.dropZone.style.display = 'none';
        this.progressSection.style.display = 'none';
        this.resultSection.style.display = 'none';
        this.batchSection.style.display = 'none';
        this.errorSection.style.display = 'block';
        this.errorMessage.textContent = title;
        
        if (this.errorHelp && helpText) {
            this.errorHelp.textContent = helpText;
            this.errorHelp.style.display = 'block';
        } else if (this.errorHelp) {
            this.errorHelp.style.display = 'none';
        }
    }
    
    updateStatus(message) {
        if (this.statusMessage) {
            this.statusMessage.textContent = message;
        }
    }
    
    updateProgress(percent) {
        if (this.progressBar) {
            this.progressBar.style.width = `${percent}%`;
        }
        if (this.progressContainer) {
            this.progressContainer.setAttribute('aria-valuenow', Math.round(percent));
        }
    }
    
    updateBatchStatus(message) {
        if (this.batchStatus) {
            this.batchStatus.textContent = message;
        }
    }
    
    updateBatchStats(total, completed, failed) {
        if (this.batchTotal) this.batchTotal.textContent = total;
        if (this.batchCompleted) this.batchCompleted.textContent = completed;
        if (this.batchFailed) this.batchFailed.textContent = failed;
        
        const progress = total > 0 ? ((completed + failed) / total) * 100 : 0;
        if (this.batchProgressBar) {
            this.batchProgressBar.style.width = `${progress}%`;
        }
    }
    
    updateCurrentFile(fileName, fileIndex) {
        if (this.currentFileName) {
            this.currentFileName.textContent = fileName;
        }
        if (this.currentFileSection) {
            this.currentFileSection.style.display = 'block';
        }
    }
    
    updateCurrentFileProgress(progress, message) {
        if (this.currentFileProgress) {
            this.currentFileProgress.textContent = `${progress}%`;
        }
        if (this.currentFileProgressBar) {
            this.currentFileProgressBar.style.width = `${progress}%`;
        }
        if (this.currentFileStatus && message) {
            this.currentFileStatus.textContent = message;
        }
    }
    
    updateFileStatus(fileId, status, progress, errorMessage = null) {
        const fileItem = document.querySelector(`[data-file-id="${fileId}"]`);
        if (!fileItem) return;
        
        // Update status class
        fileItem.className = `file-item ${status}`;
        
        // Update status icon
        const statusIcon = fileItem.querySelector('.file-status-icon');
        const progressText = fileItem.querySelector('.file-progress-text');
        
        if (statusIcon) {
            statusIcon.className = `file-status-icon ${status}`;
            
            // Update icon content based on status
            switch (status) {
                case 'queued':
                    statusIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`;
                    break;
                case 'processing':
                    statusIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 11-6.219-8.56"></path></svg>`;
                    break;
                case 'completed':
                    statusIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="m9 12 2 2 4-4"></path></svg>`;
                    break;
                case 'error':
                    statusIcon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
                    break;
            }
        }
        
        if (progressText) {
            if (status === 'completed') {
                progressText.textContent = 'Completed';
            } else if (status === 'error') {
                progressText.textContent = 'Failed';
            } else {
                progressText.textContent = `${progress}%`;
            }
        }
        
        // Add error message if present
        let errorDiv = fileItem.querySelector('.file-error');
        if (errorMessage) {
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'file-error';
                fileItem.querySelector('.file-details').appendChild(errorDiv);
            }
            errorDiv.textContent = errorMessage;
        } else if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    populateFileQueue() {
        if (!this.fileQueue || !this.batchFiles) return;
        
        this.fileQueue.innerHTML = '';
        
        this.batchFiles.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item queued';
            fileItem.setAttribute('data-file-id', file.id);
            
            fileItem.innerHTML = `
                <div class="file-status-icon queued">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                </div>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-meta">
                        <span>Size: ${this.formatFileSize(file.size)}</span>
                        <span>Status: Queued</span>
                    </div>
                </div>
                <div class="file-progress">
                    <div class="file-progress-text">0%</div>
                </div>
            `;
            
            this.fileQueue.appendChild(fileItem);
        });
    }
    
    toggleQueueVisibility() {
        if (!this.fileQueue || !this.toggleQueue) return;
        
        const isVisible = this.fileQueue.style.display !== 'none';
        this.fileQueue.style.display = isVisible ? 'none' : 'block';
        
        const toggleText = this.toggleQueue.querySelector('.queue-toggle-text');
        const toggleIcon = this.toggleQueue.querySelector('.queue-toggle-icon');
        
        if (toggleText) {
            toggleText.textContent = isVisible ? 'Show Details' : 'Hide Details';
        }
        
        if (toggleIcon) {
            this.toggleQueue.classList.toggle('expanded', !isVisible);
        }
    }
    
    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
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
    
    // Processing Folder Selection Methods
    async chooseFolderHandler() {
        try {
            // Check if File System Access API is supported
            if (!('showDirectoryPicker' in window)) {
                this.folderStatus.textContent = 'Folder selection not supported. Files will download individually.';
                return;
            }
            
            // Request directory access
            this.outputFolderHandle = await window.showDirectoryPicker();
            
            // Update UI to show selected folder
            this.selectedFolderPath.textContent = this.outputFolderHandle.name;
            this.selectedFolder.style.display = 'flex';
            this.folderStatus.textContent = `Completed files will save to: ${this.outputFolderHandle.name}`;
            
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Error choosing folder:', error);
                this.folderStatus.textContent = 'Folder selection failed. Files will download individually.';
            }
        }
    }
    
    async saveTranscriptToFolder(fileName, content) {
        if (!this.outputFolderHandle) {
            return false; // Fall back to download
        }
        
        try {
            // Create transcript file name
            const transcriptName = fileName.replace(/\.[^/.]+$/, '') + '.txt';
            
            // Get file handle
            const fileHandle = await this.outputFolderHandle.getFileHandle(transcriptName, {
                create: true
            });
            
            // Write content
            const writable = await fileHandle.createWritable();
            await writable.write(content);
            await writable.close();
            
            return true;
        } catch (error) {
            console.error('Error saving to folder:', error);
            return false; // Fall back to download
        }
    }
    
    async saveCompletedTranscript(originalFileName, transcriptContent) {
        const transcriptName = originalFileName.replace(/\.[^/.]+$/, '') + '.txt';
        
        // Try to save to selected folder first
        if (this.outputFolderHandle) {
            try {
                const fileHandle = await this.outputFolderHandle.getFileHandle(transcriptName, {
                    create: true
                });
                
                const writable = await fileHandle.createWritable();
                await writable.write(transcriptContent);
                await writable.close();
                
                console.log(`✅ Saved ${transcriptName} to folder`);
                return;
                
            } catch (error) {
                console.error(`Failed to save ${transcriptName} to folder:`, error);
                // Fall through to download
            }
        }
        
        // Fallback to individual download
        this.downloadTranscriptFile(transcriptName, transcriptContent);
    }
    
    downloadTranscriptFile(fileName, content) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log(`📥 Downloaded ${fileName}`);
    }
    
    reset() {
        this.dropZone.style.display = 'block';
        this.progressSection.style.display = 'none';
        this.resultSection.style.display = 'none';
        this.errorSection.style.display = 'none';
        this.batchSection.style.display = 'none';
        
        this.fileInput.value = '';
        if (this.progressBar) this.progressBar.style.width = '0%';
        if (this.batchProgressBar) this.batchProgressBar.style.width = '0%';
        
        this.currentSessionId = null;
        this.currentBatchId = null;
        this.uploadStartTime = null;
        this.isBatchMode = false;
        this.batchFiles = [];
        this.outputFolderHandle = null;
        
        // Reset processing folder UI
        if (this.selectedFolder) this.selectedFolder.style.display = 'none';
        if (this.processingFolderSection) this.processingFolderSection.style.display = 'none';
        if (this.folderStatus) this.folderStatus.textContent = 'Files will download individually if no folder is selected';
        
        if (this.timeEstimate) this.timeEstimate.textContent = '';
        if (this.currentFileSection) this.currentFileSection.style.display = 'none';
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TranscriptionApp();
});