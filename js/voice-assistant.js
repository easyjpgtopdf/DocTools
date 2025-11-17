// Voice Assistant - Free Web Speech API Implementation
// Works on Chrome, Edge, Safari (with microphone permission)

class VoiceAssistant {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.isSpeaking = false;
        this.commands = this.initializeCommands();
        this.setupRecognition();
        this.createUI();
    }

    setupRecognition() {
        // Check browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('Voice Assistant: Speech Recognition not supported in this browser');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-IN'; // English (India) - supports Hinglish

        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateUI('listening');
            this.showTranscript('Listening...');
        };

        this.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join('');
            
            this.showTranscript(transcript);

            if (event.results[event.results.length - 1].isFinal) {
                this.processCommand(transcript);
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.updateUI('idle');
            
            if (event.error === 'not-allowed') {
                this.speak('Please allow microphone access to use voice commands');
            } else if (event.error === 'no-speech') {
                this.speak('No speech detected. Please try again');
            }
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.updateUI('idle');
        };
    }

    initializeCommands() {
        return {
            // PDF Tools
            'pdf to word': 'pdf-to-word.html',
            'convert pdf to word': 'pdf-to-word.html',
            'pdf to excel': 'pdf-to-excel.html',
            'pdf to powerpoint': 'pdf-to-ppt.html',
            'pdf to ppt': 'pdf-to-ppt.html',
            'pdf to jpg': 'pdf-to-jpg.html',
            'pdf to image': 'pdf-to-jpg.html',
            'merge pdf': 'merge-pdf.html',
            'combine pdf': 'merge-pdf.html',
            'split pdf': 'split-pdf.html',
            'compress pdf': 'compress-pdf.html',
            'protect pdf': 'protect-pdf.html',
            'edit pdf': 'edit-pdf.html',
            'crop pdf': 'crop-pdf.html',
            
            // Image Tools
            'jpg to pdf': 'jpg-to-pdf.html',
            'image to pdf': 'jpg-to-pdf.html',
            'compress image': 'image-compressor.html',
            'resize image': 'image-resizer.html',
            'edit image': 'image-editor.html',
            'image editor': 'image-editor.html',
            'watermark': 'image-watermark.html',
            'add watermark': 'image-watermark.html',
            'remove background': 'background-remover.html',
            'background remover': 'background-remover.html',
            
            // Office Tools
            'excel to pdf': 'excel-to-pdf.html',
            'powerpoint to pdf': 'ppt-to-pdf.html',
            'ppt to pdf': 'ppt-to-pdf.html',
            'unlock excel': 'excel-unlocker.html',
            'excel unlocker': 'excel-unlocker.html',
            'protect excel': 'protect-excel.html',
            
            // Other Tools
            'ocr': 'ocr-image.html',
            'text recognition': 'ocr-image.html',
            'ai image': 'ai-image-generator.html',
            'generate image': 'ai-image-generator.html',
            'resume maker': 'resume-maker.html',
            'create resume': 'resume-maker.html',
            'biodata': 'biodata-maker.html',
            'marriage card': 'marriage-card.html',
            
            // Navigation
            'dashboard': 'dashboard.html',
            'home': 'index.html',
            'payment history': 'dashboard.html#payment-history',
            'billing': 'dashboard.html#billing',
            'donate': 'index.html#donate',
            'make donation': 'index.html#donate',
            'login': 'login.html',
            'signup': 'signup.html',
            'sign up': 'signup.html'
        };
    }

    processCommand(transcript) {
        const command = transcript.toLowerCase().trim();
        
        console.log('Voice command received:', command);
        
        // Find matching command
        let matchedUrl = null;
        let matchedCommand = null;

        for (const [key, url] of Object.entries(this.commands)) {
            if (command.includes(key)) {
                matchedUrl = url;
                matchedCommand = key;
                break;
            }
        }

        if (matchedUrl) {
            this.speak(`Opening ${matchedCommand}`);
            setTimeout(() => {
                window.location.href = matchedUrl;
            }, 1000);
        } else {
            // Smart fallback - check for keywords
            if (command.includes('convert') || command.includes('open')) {
                this.speak('Please specify which tool you want to use. For example, say PDF to Word or Compress Image');
            } else if (command.includes('upload') || command.includes('file')) {
                this.speak('Please first open the tool you want to use, then upload your file');
            } else {
                this.speak('Sorry, I did not understand that command. Try saying PDF to Word, Merge PDF, or Dashboard');
            }
        }
    }

    speak(text) {
        if (this.isSpeaking) return;

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        utterance.lang = 'en-IN';

        utterance.onstart = () => {
            this.isSpeaking = true;
        };

        utterance.onend = () => {
            this.isSpeaking = false;
        };

        window.speechSynthesis.speak(utterance);
    }

    createUI() {
        // Create floating voice button
        const voiceBtn = document.createElement('div');
        voiceBtn.id = 'voice-assistant-btn';
        voiceBtn.className = 'voice-btn';
        voiceBtn.innerHTML = `
            <svg class="mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                <line x1="12" y1="19" x2="12" y2="23"></line>
                <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
            <div class="pulse-ring"></div>
        `;

        // Create transcript panel
        const transcriptPanel = document.createElement('div');
        transcriptPanel.id = 'voice-transcript-panel';
        transcriptPanel.className = 'transcript-panel hidden';
        transcriptPanel.innerHTML = `
            <div class="transcript-header">
                <span class="status-indicator"></span>
                <span class="status-text">Ready</span>
                <button class="close-btn">&times;</button>
            </div>
            <div class="transcript-content">
                <p class="transcript-text">Click the microphone and say a command...</p>
            </div>
            <div class="command-examples">
                <div class="example-title">Try saying:</div>
                <div class="examples">
                    <span>"PDF to Word"</span>
                    <span>"Compress Image"</span>
                    <span>"Dashboard"</span>
                </div>
            </div>
        `;

        document.body.appendChild(voiceBtn);
        document.body.appendChild(transcriptPanel);

        // Event listeners
        voiceBtn.addEventListener('click', () => this.toggleListening());
        
        transcriptPanel.querySelector('.close-btn').addEventListener('click', () => {
            transcriptPanel.classList.add('hidden');
        });

        // Long press to show help
        let pressTimer;
        voiceBtn.addEventListener('mousedown', () => {
            pressTimer = setTimeout(() => {
                transcriptPanel.classList.toggle('hidden');
            }, 500);
        });
        voiceBtn.addEventListener('mouseup', () => {
            clearTimeout(pressTimer);
        });
    }

    toggleListening() {
        if (!this.recognition) {
            alert('Voice recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            try {
                this.recognition.start();
            } catch (error) {
                console.error('Failed to start recognition:', error);
            }
        }
    }

    updateUI(state) {
        const btn = document.getElementById('voice-assistant-btn');
        const panel = document.getElementById('voice-transcript-panel');
        const statusText = panel.querySelector('.status-text');

        btn.classList.remove('listening', 'speaking', 'idle');
        btn.classList.add(state);

        if (state === 'listening') {
            statusText.textContent = 'Listening...';
            panel.classList.remove('hidden');
        } else if (state === 'speaking') {
            statusText.textContent = 'Speaking...';
        } else {
            statusText.textContent = 'Ready';
        }
    }

    showTranscript(text) {
        const panel = document.getElementById('voice-transcript-panel');
        const transcriptText = panel.querySelector('.transcript-text');
        transcriptText.textContent = text;
    }
}

// Initialize Voice Assistant when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.voiceAssistant = new VoiceAssistant();
    });
} else {
    window.voiceAssistant = new VoiceAssistant();
}
