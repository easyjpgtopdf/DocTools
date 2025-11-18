// Voice Assistant - Free Web Speech API Implementation
// Works on Chrome, Edge, Safari (with microphone permission)

class VoiceAssistant {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.isSpeaking = false;
        this.currentLanguage = 'en-IN';
        this.detectedUserLanguage = null;
        this.commands = this.initializeCommands();
        this.knowledgeBase = this.initializeKnowledgeBase();
        this.setupRecognition();
        this.createUI();
    }

    // Website features knowledge base
    initializeKnowledgeBase() {
        return {
            // General questions
            'what is this website': {
                en: 'EasyJPGtoPDF is a free online platform offering 50+ tools for PDF conversion, image editing, document creation, and AI-powered features. All tools work directly in your browser with no software installation needed.',
                hi: 'EasyJPGtoPDF एक फ्री ऑनलाइन प्लेटफॉर्म है जो PDF conversion, image editing, document बनाने और AI features के 50+ tools देता है। सभी tools आपके browser में काम करते हैं, कोई software install नहीं करना पड़ता।'
            },
            'what can i do': {
                en: 'You can convert PDFs to Word, Excel, PowerPoint, compress images, edit photos, create resumes, generate AI images, remove backgrounds, merge PDFs, and much more - all for free!',
                hi: 'आप PDF को Word, Excel, PowerPoint में convert कर सकते हैं, images compress कर सकते हैं, photos edit कर सकते हैं, resume बना सकते हैं, AI images generate कर सकते हैं, background remove कर सकते हैं, PDFs merge कर सकते हैं - सब free में!'
            },
            'is it free': {
                en: 'Yes! All basic tools are completely free to use. You can make donations to support the service if you wish.',
                hi: 'हाँ! सभी basic tools बिलकुल free हैं। अगर चाहें तो आप service को support करने के लिए donation दे सकते हैं।'
            },
            'do i need account': {
                en: 'No account needed for basic tools! You can use them instantly. However, creating a free account gives you access to payment history and premium features.',
                hi: 'Basic tools के लिए account की जरूरत नहीं! तुरंत use कर सकते हैं। लेकिन free account बनाने से payment history और premium features मिलते हैं।'
            },
            'is it safe': {
                en: 'Yes, completely safe! All files are processed securely in your browser or on encrypted servers. Files are automatically deleted after 1 hour. We never store your personal data.',
                hi: 'हाँ, पूरी तरह safe है! सभी files आपके browser या encrypted servers पर securely process होती हैं। Files 1 घंटे बाद automatically delete हो जाती हैं। हम आपका personal data कभी store नहीं करते।'
            },
            'file size limit': {
                en: 'Most tools support files up to 15MB. Some tools like PDF processing support up to 500MB. The limit is shown on each tool page.',
                hi: '⁣अधिकतर tools 15MB तक की files support करते हैं। PDF processing जैसे कुछ tools 500MB तक support करते हैं। Limit हर tool page पर दिखाई देती है।'
            },
            'how to convert pdf': {
                en: 'Just say "PDF to Word" or choose any PDF converter from our tools. Upload your PDF, click convert, and download the result. It takes just seconds!',
                hi: 'बस बोलो "PDF to Word" या हमारे tools से कोई PDF converter चुनें। अपनी PDF upload करें, convert पर click करें, और result download करें। बस कुछ seconds लगते हैं!'
            },
            'how to compress image': {
                en: 'Say "Compress Image" to open the tool. Upload your photo, adjust quality slider, and download the compressed version. You can reduce size by up to 90%!',
                hi: '"Compress Image" बोलो tool खोलने के लिए। अपनी photo upload करें, quality slider adjust करें, और compressed version download करें। आप size 90% तक कम कर सकते हैं!'
            },
            'payment methods': {
                en: 'We accept all major payment methods through Razorpay - UPI, Credit/Debit Cards, Net Banking, and Wallets. All payments are secure and encrypted.',
                hi: 'हम Razorpay के through सभी major payment methods accept करते हैं - UPI, Credit/Debit Cards, Net Banking, और Wallets। सभी payments secure और encrypted हैं।'
            },
            'mobile support': {
                en: 'Yes! All tools work perfectly on mobile phones and tablets. The interface automatically adapts to your screen size for the best experience.',
                hi: 'हाँ! सभी tools mobile phones और tablets पर perfectly काम करते हैं। Interface automatically आपकी screen size के हिसाब से adjust हो जाता है।'
            },
            'voice commands': {
                en: 'You can use voice to navigate! Just click the mic button and say commands like "PDF to Word", "Compress Image", "Dashboard", or ask questions about features.',
                hi: 'आप voice से navigate कर सकते हैं! बस mic button पर click करें और commands बोलें जैसे "PDF to Word", "Compress Image", "Dashboard", या features के बारे में सवाल पूछें।'
            },
            'supported formats': {
                en: 'We support PDF, Word (DOC/DOCX), Excel (XLS/XLSX), PowerPoint (PPT/PPTX), Images (JPG, PNG, WEBP, BMP), and many more formats.',
                hi: 'हम PDF, Word (DOC/DOCX), Excel (XLS/XLSX), PowerPoint (PPT/PPTX), Images (JPG, PNG, WEBP, BMP), और कई formats support करते हैं।'
            },
            'background removal': {
                en: 'Our AI-powered background remover works instantly! Upload any image, and the AI automatically detects and removes the background, giving you a transparent PNG.',
                hi: 'हमारा AI-powered background remover तुरंत काम करता है! कोई भी image upload करें, और AI automatically background detect करके remove कर देता है, transparent PNG देता है।'
            },
            'resume maker': {
                en: 'Create professional resumes in minutes! Choose from multiple templates, fill in your details, and download a beautiful PDF resume ready for job applications.',
                hi: 'Minutes में professional resumes बनाएं! कई templates में से चुनें, अपनी details भरें, और job applications के लिए तैयार खूबसूरत PDF resume download करें।'
            },
            'ai features': {
                en: 'We offer AI Image Generation, OCR text extraction, Background Removal, and Smart Image Enhancement. More AI features coming soon!',
                hi: 'हम AI Image Generation, OCR text extraction, Background Removal, और Smart Image Enhancement provide करते हैं। और AI features जल्द आ रहे हैं!'
            }
        };
    }

    // Auto-detect user's preferred language
    detectLanguage() {
        const savedLang = localStorage.getItem('voiceAssistantLang');
        if (savedLang) return savedLang;
        
        // Browser language detection
        const browserLang = navigator.language || navigator.userLanguage;
        
        // Map common languages
        const langMap = {
            'hi': 'hi-IN',      // Hindi
            'en': 'en-IN',      // English (India)
            'mr': 'mr-IN',      // Marathi
            'gu': 'gu-IN',      // Gujarati
            'ta': 'ta-IN',      // Tamil
            'te': 'te-IN',      // Telugu
            'kn': 'kn-IN',      // Kannada
            'ml': 'ml-IN',      // Malayalam
            'bn': 'bn-IN',      // Bengali
            'pa': 'pa-IN',      // Punjabi
            'es': 'es-ES',      // Spanish
            'fr': 'fr-FR',      // French
            'de': 'de-DE',      // German
            'pt': 'pt-BR',      // Portuguese
            'ru': 'ru-RU',      // Russian
            'ja': 'ja-JP',      // Japanese
            'zh': 'zh-CN',      // Chinese
            'ar': 'ar-SA',      // Arabic
        };
        
        const langCode = browserLang.split('-')[0];
        return langMap[langCode] || 'en-IN';
    }

    // Detect language from spoken text
    detectSpokenLanguage(text) {
        const lowerText = text.toLowerCase();
        
        // Hindi/Devanagari detection
        if (/[\u0900-\u097F]/.test(text)) {
            return 'hi-IN';
        }
        
        // Common Hindi words in Roman script
        const hindiWords = ['pdf', 'image', 'convert', 'karo', 'kholo', 'dikhao', 'banao', 'merge', 'compress', 'dashboard', 'kar', 'de'];
        const hindiMatches = hindiWords.filter(word => lowerText.includes(word)).length;
        
        if (hindiMatches > 2) {
            return 'hi-IN';
        }
        
        return this.currentLanguage;
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
        
        // Auto-detect language or use saved preference
        this.currentLanguage = this.detectLanguage();
        this.recognition.lang = this.currentLanguage;

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
        
        // Detect user's language from speech
        this.detectedUserLanguage = this.detectSpokenLanguage(transcript);
        
        // Only check Q&A if command contains question words (not direct tool names)
        const questionWords = ['what', 'kya', 'क्या', 'how', 'kaise', 'कैसे', 'is', 'hai', 'है', 'can', 'sakta', 'सकता', 'free', 'safe', 'surakshit', 'mobile', 'phone'];
        const hasQuestionWord = questionWords.some(word => command.includes(word));
        
        if (hasQuestionWord) {
            const questionAnswer = this.checkKnowledgeBase(command);
            if (questionAnswer) {
                this.showAnswer(questionAnswer);
                return;
            }
        }
        
        // Smart search with fuzzy matching
        const results = this.smartSearch(command);
        
        if (results.length === 1) {
            // Exact match - navigate directly
            const match = results[0];
            this.speakInUserLanguage(`Opening ${match.title}`, match.title);
            setTimeout(() => {
                window.location.href = match.url;
            }, 1000);
        } else if (results.length > 1) {
            // Multiple matches - show suggestions
            this.showSuggestions(results);
            const titles = results.slice(0, 3).map(r => r.title).join(', ');
            this.speakInUserLanguage(`Found ${results.length} results: ${titles}`, `मिले ${results.length} परिणाम`);
        } else {
            // No match - helpful message
            this.speakInUserLanguage(
                'Sorry, I did not understand that. Try saying PDF to Word, Compress Image, or ask me about website features',
                'समझ नहीं आया। PDF to Word, Image Compress बोलो, या website features के बारे में पूछो'
            );
        }
    }

    // Check knowledge base for questions
    checkKnowledgeBase(query) {
        const questionKeywords = {
            'what is this': ['what is this', 'ye kya hai', 'what is easyjpgtopdf', 'about'],
            'what can i do': ['what can i do', 'kya kar sakte', 'features', 'tools available'],
            'is it free': ['free', 'cost', 'price', 'kitna paisa', 'free hai'],
            'do i need account': ['account', 'login', 'signup', 'registration', 'sign up chahiye'],
            'is it safe': ['safe', 'secure', 'privacy', 'surakshit', 'safe hai'],
            'file size limit': ['file size', 'limit', 'maximum', 'kitna bada', 'size limit'],
            'how to convert pdf': ['convert pdf', 'pdf kaise', 'pdf conversion'],
            'how to compress image': ['compress', 'image size', 'reduce size', 'chhota karo'],
            'payment methods': ['payment', 'pay kaise', 'payment method', 'razorpay'],
            'mobile support': ['mobile', 'phone', 'mobile me', 'phone me chalega'],
            'voice commands': ['voice', 'mic', 'kaise bolu', 'voice kaise use'],
            'supported formats': ['format', 'file type', 'kaunse format', 'support'],
            'background removal': ['background', 'remove background', 'background hatao'],
            'resume maker': ['resume', 'cv', 'biodata', 'resume kaise'],
            'ai features': ['ai', 'artificial intelligence', 'ai kya hai', 'ai tools']
        };

        // Find matching question
        for (const [key, keywords] of Object.entries(questionKeywords)) {
            for (const keyword of keywords) {
                if (query.includes(keyword)) {
                    return {
                        question: key,
                        answer: this.knowledgeBase[key]
                    };
                }
            }
        }

        return null;
    }

    // Show answer in panel
    showAnswer(qa) {
        const panel = document.getElementById('voice-transcript-panel');
        const content = panel.querySelector('.transcript-content');
        
        const isHindi = this.detectedUserLanguage && this.detectedUserLanguage.startsWith('hi');
        const answer = isHindi ? qa.answer.hi : qa.answer.en;
        
        content.innerHTML = `
            <div class="answer-box">
                <div class="answer-icon">💡</div>
                <div class="answer-text">${answer}</div>
                <div class="follow-up">
                    <small>Ask me more: "What can I do?", "Is it free?", "How to convert PDF?"</small>
                </div>
            </div>
        `;
        
        panel.classList.remove('hidden');
        
        // Speak the answer
        this.speak(answer);
    }

    // Smart search with fuzzy matching and workflow guidance
    smartSearch(query) {
        const results = [];
        
        // Complete tool database with step-by-step instructions
        const toolDatabase = [
            // PDF Conversion Tools
            { 
                title: 'PDF to Word', 
                url: 'pdf-to-word.html', 
                keywords: ['pdf', 'word', 'convert', 'doc', 'docx', 'pdf se word', 'pdf ko word', 'word mein', 'वर्ड', 'document'], 
                category: 'PDF Tools', 
                description: 'Convert PDF to editable Word document',
                instructions: {
                    en: '1. Click "Select PDF File" button\n2. Choose your PDF from computer\n3. Click "Convert to Word"\n4. Wait 5-10 seconds\n5. Click "Download Word File"',
                    hi: '1. "Select PDF File" button पर click करें\n2. अपने computer से PDF चुनें\n3. "Convert to Word" पर click करें\n4. 5-10 seconds wait करें\n5. "Download Word File" पर click करें'
                }
            },
            { 
                title: 'PDF to Excel', 
                url: 'pdf-to-excel.html', 
                keywords: ['pdf', 'excel', 'spreadsheet', 'xls', 'xlsx', 'pdf se excel', 'एक्सेल'], 
                category: 'PDF Tools', 
                description: 'Convert PDF to Excel spreadsheet',
                instructions: {
                    en: '1. Upload PDF file\n2. Click Convert\n3. Download Excel file',
                    hi: '1. PDF file upload करें\n2. Convert पर click करें\n3. Excel file download करें'
                }
            },
            { 
                title: 'PDF to PowerPoint', 
                url: 'pdf-to-ppt.html', 
                keywords: ['pdf', 'powerpoint', 'ppt', 'pptx', 'presentation', 'pdf se ppt', 'पीपीटी'], 
                category: 'PDF Tools', 
                description: 'Convert PDF to PowerPoint presentation',
                instructions: {
                    en: '1. Select PDF file\n2. Click Convert to PPT\n3. Download PowerPoint file',
                    hi: '1. PDF file select करें\n2. Convert to PPT पर click करें\n3. PowerPoint file download करें'
                }
            },
            { 
                title: 'PDF to JPG', 
                url: 'pdf-to-jpg.html', 
                keywords: ['pdf', 'jpg', 'jpeg', 'image', 'picture', 'photo', 'pdf se image', 'pdf se jpg', 'तस्वीर'], 
                category: 'PDF Tools', 
                description: 'Convert PDF pages to JPG images',
                instructions: {
                    en: '1. Upload PDF\n2. Select pages to convert\n3. Click Convert\n4. Download JPG images',
                    hi: '1. PDF upload करें\n2. Convert करने के pages select करें\n3. Convert पर click करें\n4. JPG images download करें'
                }
            },
            
            // PDF Editing Tools
            { title: 'Merge PDF', url: 'merge-pdf.html', keywords: ['merge', 'combine', 'join', 'pdf', 'milao', 'jodo', 'ek karo', 'मिलाओ'], category: 'PDF Tools', description: 'Combine multiple PDF files into one' },
            { title: 'Split PDF', url: 'split-pdf.html', keywords: ['split', 'divide', 'separate', 'pdf', 'todo', 'alag karo', 'विभाजित'], category: 'PDF Tools', description: 'Split PDF into multiple files' },
            { title: 'Compress PDF', url: 'compress-pdf.html', keywords: ['compress', 'reduce', 'size', 'pdf', 'chhota', 'size kam', 'छोटा'], category: 'PDF Tools', description: 'Reduce PDF file size' },
            { title: 'Protect PDF', url: 'protect-pdf.html', keywords: ['protect', 'password', 'secure', 'lock', 'pdf', 'surakshit', 'tala', 'सुरक्षित'], category: 'PDF Tools', description: 'Add password protection to PDF' },
            { title: 'Unlock PDF', url: 'unlock-pdf.html', keywords: ['unlock', 'pdf', 'password', 'remove', 'open', 'kholo', 'खोलो'], category: 'PDF Tools', description: 'Remove PDF password protection' },
            { title: 'Edit PDF', url: 'edit-pdf.html', keywords: ['edit', 'modify', 'change', 'pdf', 'sudhar', 'badlo', 'संपादित'], category: 'PDF Tools', description: 'Edit PDF content directly' },
            { title: 'Crop PDF', url: 'crop-pdf.html', keywords: ['crop', 'trim', 'cut', 'pdf', 'kaato', 'काटो'], category: 'PDF Tools', description: 'Crop PDF pages' },
            { title: 'Watermark PDF', url: 'watermark-pdf.html', keywords: ['watermark', 'pdf', 'logo', 'mark', 'stamp', 'nishaan', 'निशान'], category: 'PDF Tools', description: 'Add watermark to PDF' },
            { title: 'Add Page Numbers', url: 'add-page-numbers.html', keywords: ['page', 'number', 'pdf', 'add', 'sankhya', 'संख्या'], category: 'PDF Tools', description: 'Add page numbers to PDF' },
            
            // Image to PDF
            { title: 'JPG to PDF', url: 'jpg-to-pdf.html', keywords: ['jpg', 'jpeg', 'image', 'pdf', 'picture', 'photo', 'image se pdf', 'तस्वीर से पीडीएफ'], category: 'Image Tools', description: 'Convert images to PDF' },
            
            // Image Editing Tools
            { title: 'Compress Image', url: 'image-compressor.html', keywords: ['compress', 'image', 'reduce', 'size', 'photo', 'image chhota', 'size kam', 'छोटा'], category: 'Image Tools', description: 'Reduce image file size' },
            { title: 'Resize Image', url: 'image-resizer.html', keywords: ['resize', 'scale', 'dimension', 'image', 'photo', 'size badlo', 'आकार'], category: 'Image Tools', description: 'Change image dimensions' },
            { title: 'Image Editor', url: 'image-editor.html', keywords: ['edit', 'image', 'photo', 'editor', 'modify', 'sudhar', 'badlo', 'फोटो एडिट'], category: 'Image Tools', description: 'Professional image editing tools' },
            { title: 'Image Repair', url: 'image-repair.html', keywords: ['repair', 'fix', 'restore', 'image', 'photo', 'thik karo', 'ठीक'], category: 'Image Tools', description: 'Repair and restore damaged images' },
            { title: 'Add Watermark', url: 'image-watermark.html', keywords: ['watermark', 'logo', 'text', 'image', 'mark', 'nishaan', 'निशान'], category: 'Image Tools', description: 'Add watermark to images' },
            { title: 'Remove Background', url: 'background-remover.html', keywords: ['background', 'remove', 'transparent', 'bg', 'image', 'background hatao', 'बैकग्राउंड हटाओ'], category: 'Image Tools', description: 'Remove image background' },
            
            // Office to PDF
            { title: 'Excel to PDF', url: 'excel-to-pdf.html', keywords: ['excel', 'pdf', 'spreadsheet', 'xls', 'xlsx', 'xlsx se pdf', 'एक्सेल से पीडीएफ'], category: 'Office Tools', description: 'Convert Excel to PDF' },
            { title: 'PowerPoint to PDF', url: 'ppt-to-pdf.html', keywords: ['powerpoint', 'ppt', 'pdf', 'presentation', 'ppt se pdf', 'प्रेजेंटेशन'], category: 'Office Tools', description: 'Convert PowerPoint to PDF' },
            { title: 'Word to PDF', url: 'word-to-pdf.html', keywords: ['word', 'pdf', 'doc', 'docx', 'word se pdf', 'वर्ड से पीडीएफ'], category: 'Office Tools', description: 'Convert Word to PDF' },
            
            // Excel Tools
            { title: 'Unlock Excel', url: 'excel-unlocker.html', keywords: ['unlock', 'excel', 'password', 'remove', 'kholo', 'password hatao', 'एक्सेल खोलो'], category: 'Office Tools', description: 'Remove Excel password protection' },
            { title: 'Protect Excel', url: 'protect-excel.html', keywords: ['protect', 'excel', 'password', 'secure', 'lock', 'surakshit', 'सुरक्षित'], category: 'Office Tools', description: 'Add password to Excel file' },
            
            // AI Tools
            { title: 'OCR Image', url: 'ocr-image.html', keywords: ['ocr', 'text', 'recognition', 'read', 'image', 'scan', 'text nikalo', 'टेक्स्ट निकालो'], category: 'AI Tools', description: 'Extract text from images using AI' },
            { title: 'AI Image Generator', url: 'ai-image-generator.html', keywords: ['ai', 'generate', 'image', 'create', 'art', 'banao', 'आर्टिफिशियल', 'बनाओ'], category: 'AI Tools', description: 'Generate images using AI' },
            
            // Document Makers
            { title: 'Resume Maker', url: 'resume-maker.html', keywords: ['resume', 'cv', 'create', 'make', 'job', 'biodata', 'रिज्यूमे'], category: 'Document Tools', description: 'Create professional resume' },
            { title: 'Indian Resume Maker', url: 'Indian-style-Resume-generator.html', keywords: ['indian', 'resume', 'cv', 'bharatiya', 'भारतीय', 'रिज्यूमे'], category: 'Document Tools', description: 'Create Indian-style resume' },
            { title: 'Online Resume Maker', url: 'online_resume_maker.html', keywords: ['online', 'resume', 'cv', 'web', 'ऑनलाइन'], category: 'Document Tools', description: 'Create resume online' },
            { title: 'Biodata Maker', url: 'biodata-maker.html', keywords: ['biodata', 'create', 'make', 'personal', 'bio', 'बायोडाटा'], category: 'Document Tools', description: 'Create biodata form' },
            { title: 'Marriage Card', url: 'marriage-card.html', keywords: ['marriage', 'wedding', 'card', 'invitation', 'shadi', 'vivah', 'शादी', 'विवाह'], category: 'Document Tools', description: 'Create marriage invitation card' },
            
            // Account & Navigation
            { title: 'Dashboard', url: 'dashboard.html', keywords: ['dashboard', 'account', 'profile', 'home', 'khata', 'डैशबोर्ड'], category: 'Navigation', description: 'View your account dashboard' },
            { title: 'Login', url: 'login.html', keywords: ['login', 'signin', 'enter', 'log in', 'प्रवेश'], category: 'Navigation', description: 'Login to your account' },
            { title: 'Sign Up', url: 'signup.html', keywords: ['signup', 'register', 'create account', 'join', 'पंजीकरण'], category: 'Navigation', description: 'Create new account' },
            { title: 'Payment History', url: 'dashboard.html#payment-history', keywords: ['payment', 'history', 'transaction', 'receipt', 'bill', 'lenden', 'भुगतान'], category: 'Navigation', description: 'View payment history' },
            { title: 'Billing Details', url: 'shipping-billing.html', keywords: ['billing', 'shipping', 'address', 'details', 'पता'], category: 'Navigation', description: 'Manage billing information' },
            { title: 'Make Donation', url: 'index.html#donate', keywords: ['donate', 'donation', 'support', 'contribute', 'daan', 'दान'], category: 'Navigation', description: 'Support our service' },
            
            // Legal & Support
            { title: 'Privacy Policy', url: 'privacy-policy.html', keywords: ['privacy', 'policy', 'terms', 'गोपनीयता'], category: 'Legal', description: 'Privacy policy and data protection' },
            { title: 'Terms of Service', url: 'terms-of-service.html', keywords: ['terms', 'service', 'conditions', 'शर्तें'], category: 'Legal', description: 'Terms and conditions' },
            { title: 'Refund Policy', url: 'refund-policy.html', keywords: ['refund', 'return', 'money back', 'वापसी'], category: 'Legal', description: 'Refund and return policy' },
            { title: 'KYC Support', url: 'kyc-support.html', keywords: ['kyc', 'support', 'verification', 'help', 'सहायता'], category: 'Support', description: 'KYC verification support' },
            { title: 'Attributions', url: 'attributions.html', keywords: ['attribution', 'credit', 'acknowledgment', 'श्रेय'], category: 'Support', description: 'Third-party attributions' },
        ];
        
        // Calculate relevance score
        for (const tool of toolDatabase) {
            let score = 0;
            const queryWords = query.split(' ');
            
            // Exact title match
            if (tool.title.toLowerCase() === query) {
                score += 100;
            }
            
            // Keyword matching
            for (const keyword of tool.keywords) {
                if (query.includes(keyword)) {
                    score += 20;
                }
            }
            
            // Partial word matching
            for (const word of queryWords) {
                if (word.length > 2) {
                    for (const keyword of tool.keywords) {
                        if (keyword.includes(word) || word.includes(keyword)) {
                            score += 10;
                        }
                    }
                }
            }
            
            if (score > 0) {
                results.push({ ...tool, score });
            }
        }
        
        // Sort by relevance score
        results.sort((a, b) => b.score - a.score);
        
        return results;
    }

    // Show suggestion panel
    showSuggestions(results) {
        const panel = document.getElementById('voice-transcript-panel');
        const content = panel.querySelector('.transcript-content');
        
        content.innerHTML = `
            <div class="suggestions-list">
                <div class="suggestions-title">Did you mean:</div>
                ${results.slice(0, 5).map(result => `
                    <div class="suggestion-item" data-url="${result.url}">
                        <div class="suggestion-title">${result.title}</div>
                        <div class="suggestion-desc">${result.description}</div>
                        <div class="suggestion-category">${result.category}</div>
                    </div>
                `).join('')}
            </div>
        `;
        
        panel.classList.remove('hidden');
        
        // Add click handlers
        content.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                window.location.href = item.dataset.url;
            });
        });
    }

    // Speak in user's detected language
    speakInUserLanguage(englishText, hindiText) {
        const isHindi = this.detectedUserLanguage && this.detectedUserLanguage.startsWith('hi');
        const text = isHindi && hindiText ? hindiText : englishText;
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = this.detectedUserLanguage || this.currentLanguage;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        window.speechSynthesis.speak(utterance);
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
        
        // Close button
        transcriptPanel.querySelector('.close-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            transcriptPanel.classList.add('hidden');
        });

        // Click outside to close (overlay behavior)
        document.addEventListener('click', (e) => {
            if (!transcriptPanel.classList.contains('hidden')) {
                // Check if click is outside panel and button
                if (!transcriptPanel.contains(e.target) && !voiceBtn.contains(e.target)) {
                    transcriptPanel.classList.add('hidden');
                }
            }
        });

        // Prevent panel clicks from closing it
        transcriptPanel.addEventListener('click', (e) => {
            e.stopPropagation();
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
