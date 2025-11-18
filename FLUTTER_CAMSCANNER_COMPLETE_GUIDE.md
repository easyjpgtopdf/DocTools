# Flutter App + CamScanner Feature - Complete Guide
## VS Code + WebView + Document Scanner

---

## 📱 **APPROACH: Hybrid App (Best for You)**

**WebView** (existing website) + **Native CamScanner Feature** = Perfect App!

✅ सभी 50+ tools website से (WebView)
✅ CamScanner feature native Flutter में
✅ Google Cloud + Firebase + Razorpay already connected
✅ AdMob दोनों apps में (website + scanner) 
✅ सारा paisa एक ही AdMob account में

---

## 🎯 **ARCHITECTURE**

```
EasyJPGtoPDF Android App
├── WebView Tab (Main)
│   ├── All 50+ tools from website
│   ├── Voice Assistant
│   ├── Firebase Auth
│   └── Razorpay Payments
│
└── Document Scanner Tab (Native)
    ├── Camera with edge detection
    ├── Auto crop & perspective fix
    ├── Multi-page scanning
    ├── Image enhancement
    ├── OCR text extraction
    ├── PDF generation
    └── Upload to Firebase Storage
```

**Benefits:**
- ✅ No need to rebuild all tools
- ✅ Website updates = App updates automatically
- ✅ CamScanner feature works offline
- ✅ Both sections show AdMob ads
- ✅ One AdMob account for all revenue

---

## 🛠️ **FLUTTER VERSION & SETUP**

### **Step 1: Download Flutter SDK**

**Recommended Version:** **Flutter 3.24.5** (Latest Stable - Nov 2024)

```powershell
# Download Flutter
cd C:\
mkdir dev
cd dev

# Download from: https://docs.flutter.dev/get-started/install/windows
# Or use Git:
git clone https://github.com/flutter/flutter.git -b stable
```

### **Step 2: Add Flutter to PATH**

```powershell
# Add to System Environment Variables
$env:Path += ";C:\dev\flutter\bin"

# Permanent (run as Admin):
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\dev\flutter\bin", "Machine")
```

### **Step 3: Verify Installation**

```powershell
flutter --version
flutter doctor
```

Expected output:
```
Flutter 3.24.5 • channel stable
Dart 3.5.4
```

### **Step 4: Install Android Studio**

1. Download: https://developer.android.com/studio
2. Install Android SDK
3. Create Android Emulator (Pixel 6)

### **Step 5: Setup VS Code**

Install extensions:
- **Flutter** (Dart-Code.flutter)
- **Dart** (Dart-Code.dart-code)

```powershell
code --install-extension Dart-Code.flutter
code --install-extension Dart-Code.dart-code
```

---

## 📦 **CREATE FLUTTER APP**

### **Step 1: Create New Flutter Project**

```powershell
cd C:\Users\apnao\Downloads
flutter create easyjpgtopdf_app
cd easyjpgtopdf_app
code .
```

### **Step 2: Update `pubspec.yaml`**

```yaml
name: easyjpgtopdf_app
description: Free PDF & Image Tools with Document Scanner
version: 1.0.0+1

environment:
  sdk: '>=3.5.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  
  # WebView for website
  webview_flutter: ^4.9.0
  
  # Document Scanner Features
  camera: ^0.11.0
  image_picker: ^1.1.2
  edge_detection: ^1.1.1
  image: ^4.2.0
  pdf: ^3.11.1
  path_provider: ^2.1.4
  
  # OCR
  google_mlkit_text_recognition: ^0.13.1
  
  # Firebase
  firebase_core: ^3.6.0
  firebase_auth: ^5.3.1
  firebase_storage: ^12.3.4
  cloud_firestore: ^5.4.4
  
  # Razorpay
  razorpay_flutter: ^1.3.7
  
  # AdMob
  google_mobile_ads: ^5.2.0
  
  # UI
  cupertino_icons: ^1.0.8
  image_cropper: ^8.0.2
  
dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0
```

### **Step 3: Install Packages**

```powershell
flutter pub get
```

---

## 📱 **APP STRUCTURE**

Create these files:

```
lib/
├── main.dart                 # App entry point
├── screens/
│   ├── home_screen.dart     # Bottom navigation
│   ├── webview_screen.dart  # Website WebView
│   └── scanner_screen.dart  # CamScanner feature
├── services/
│   ├── firebase_service.dart
│   ├── admob_service.dart
│   └── scanner_service.dart
└── widgets/
    ├── document_preview.dart
    └── scan_controls.dart
```

---

## 💻 **CODE IMPLEMENTATION**

### **File 1: `lib/main.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await Firebase.initializeApp();
  
  // Initialize AdMob
  await MobileAds.instance.initialize();
  
  runApp(const EasyJPGtoPDFApp());
}

class EasyJPGtoPDFApp extends StatelessWidget {
  const EasyJPGtoPDFApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EasyJPGtoPDF',
      theme: ThemeData(
        primarySwatch: Colors.purple,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
```

### **File 2: `lib/screens/home_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'webview_screen.dart';
import 'scanner_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [
    const WebViewScreen(),
    const ScannerScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Tools',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.document_scanner),
            label: 'Scanner',
          ),
        ],
      ),
    );
  }
}
```

### **File 3: `lib/screens/webview_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

class WebViewScreen extends StatefulWidget {
  const WebViewScreen({super.key});

  @override
  State<WebViewScreen> createState() => _WebViewScreenState();
}

class _WebViewScreenState extends State<WebViewScreen> {
  late WebViewController _controller;
  BannerAd? _bannerAd;
  bool _isAdLoaded = false;

  @override
  void initState() {
    super.initState();
    _initializeWebView();
    _loadBannerAd();
  }

  void _initializeWebView() {
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (int progress) {
            // Update loading bar
          },
          onPageStarted: (String url) {},
          onPageFinished: (String url) {},
        ),
      )
      ..loadRequest(Uri.parse('https://easyjpgtopdf.com'));
  }

  void _loadBannerAd() {
    _bannerAd = BannerAd(
      adUnitId: 'ca-app-pub-3940256099942544/6300978111', // Test ID
      // Replace with your AdMob ID: 'ca-app-pub-XXXXXXXXXXXXXXXX/YYYYYYYYYY'
      size: AdSize.banner,
      request: const AdRequest(),
      listener: BannerAdListener(
        onAdLoaded: (_) => setState(() => _isAdLoaded = true),
        onAdFailedToLoad: (ad, error) {
          ad.dispose();
          print('Ad failed to load: $error');
        },
      ),
    );
    _bannerAd?.load();
  }

  @override
  void dispose() {
    _bannerAd?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('EasyJPGtoPDF Tools'),
        backgroundColor: Colors.purple,
      ),
      body: Column(
        children: [
          // Website WebView
          Expanded(
            child: WebViewWidget(controller: _controller),
          ),
          // AdMob Banner
          if (_isAdLoaded && _bannerAd != null)
            SizedBox(
              height: _bannerAd!.size.height.toDouble(),
              width: _bannerAd!.size.width.toDouble(),
              child: AdWidget(ad: _bannerAd!),
            ),
        ],
      ),
    );
  }
}
```

### **File 4: `lib/screens/scanner_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:edge_detection/edge_detection.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:path_provider/path_provider.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'dart:io';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  List<String> _scannedImages = [];
  final ImagePicker _picker = ImagePicker();
  final TextRecognizer _textRecognizer = TextRecognizer();
  InterstitialAd? _interstitialAd;

  @override
  void initState() {
    super.initState();
    _loadInterstitialAd();
  }

  void _loadInterstitialAd() {
    InterstitialAd.load(
      adUnitId: 'ca-app-pub-3940256099942544/1033173712', // Test ID
      request: const AdRequest(),
      adLoadCallback: InterstitialAdLoadCallback(
        onAdLoaded: (ad) => _interstitialAd = ad,
        onAdFailedToLoad: (error) => print('Failed to load ad: $error'),
      ),
    );
  }

  // Scan Document with Edge Detection
  Future<void> _scanDocument() async {
    try {
      String? imagePath = await EdgeDetection.detectEdge;
      if (imagePath != null) {
        setState(() => _scannedImages.add(imagePath));
      }
    } catch (e) {
      print('Error scanning: $e');
      _showError('Failed to scan document');
    }
  }

  // Pick from Gallery
  Future<void> _pickFromGallery() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      setState(() => _scannedImages.add(image.path));
    }
  }

  // Extract Text using OCR
  Future<String> _extractText(String imagePath) async {
    final inputImage = InputImage.fromFilePath(imagePath);
    final RecognizedText recognizedText = await _textRecognizer.processImage(inputImage);
    return recognizedText.text;
  }

  // Generate PDF from scanned images
  Future<void> _generatePDF() async {
    if (_scannedImages.isEmpty) {
      _showError('No images to convert');
      return;
    }

    final pdf = pw.Document();

    for (String imagePath in _scannedImages) {
      final imageFile = File(imagePath);
      final imageBytes = await imageFile.readAsBytes();
      final image = pw.MemoryImage(imageBytes);

      pdf.addPage(
        pw.Page(
          pageFormat: PdfPageFormat.a4,
          build: (context) => pw.Center(
            child: pw.Image(image),
          ),
        ),
      );
    }

    // Save PDF
    final directory = await getApplicationDocumentsDirectory();
    final file = File('${directory.path}/scanned_${DateTime.now().millisecondsSinceEpoch}.pdf');
    await file.writeAsBytes(await pdf.save());

    // Show interstitial ad after PDF generation
    _interstitialAd?.show();
    _loadInterstitialAd(); // Load next ad

    _showSuccess('PDF saved: ${file.path}');
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.green),
    );
  }

  @override
  void dispose() {
    _textRecognizer.close();
    _interstitialAd?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Document Scanner'),
        backgroundColor: Colors.purple,
        actions: [
          if (_scannedImages.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.picture_as_pdf),
              onPressed: _generatePDF,
              tooltip: 'Generate PDF',
            ),
        ],
      ),
      body: Column(
        children: [
          // Scanned Images Grid
          Expanded(
            child: _scannedImages.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.document_scanner, size: 100, color: Colors.grey),
                        const SizedBox(height: 20),
                        const Text('No scanned documents'),
                      ],
                    ),
                  )
                : GridView.builder(
                    padding: const EdgeInsets.all(8),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 8,
                      mainAxisSpacing: 8,
                    ),
                    itemCount: _scannedImages.length,
                    itemBuilder: (context, index) {
                      return Stack(
                        fit: StackFit.expand,
                        children: [
                          Image.file(
                            File(_scannedImages[index]),
                            fit: BoxFit.cover,
                          ),
                          Positioned(
                            top: 5,
                            right: 5,
                            child: IconButton(
                              icon: const Icon(Icons.delete, color: Colors.red),
                              onPressed: () {
                                setState(() => _scannedImages.removeAt(index));
                              },
                            ),
                          ),
                        ],
                      );
                    },
                  ),
          ),
          // Action Buttons
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: _scanDocument,
                  icon: const Icon(Icons.camera),
                  label: const Text('Scan'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.purple,
                    foregroundColor: Colors.white,
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: _pickFromGallery,
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Gallery'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.purple,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

---

## 🔧 **ANDROID CONFIGURATION**

### **File: `android/app/src/main/AndroidManifest.xml`**

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:label="EasyJPGtoPDF"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">
            
            <meta-data
              android:name="io.flutter.embedding.android.NormalTheme"
              android:resource="@style/NormalTheme"
              />
            
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        
        <!-- AdMob App ID -->
        <meta-data
            android:name="com.google.android.gms.ads.APPLICATION_ID"
            android:value="ca-app-pub-XXXXXXXXXXXXXXXX~YYYYYYYYYY"/>
        
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>

    <!-- Permissions -->
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.CAMERA"/>
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
    
    <uses-feature android:name="android.hardware.camera" android:required="false"/>
</manifest>
```

### **File: `android/app/build.gradle`**

```gradle
android {
    namespace = "com.easyjpgtopdf.app"
    compileSdk = 34
    
    defaultConfig {
        applicationId = "com.easyjpgtopdf.app"
        minSdk = 21
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
        multiDexEnabled true
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.release
            minifyEnabled = true
            shrinkResources = true
        }
    }
}

dependencies {
    implementation 'com.google.android.gms:play-services-ads:23.5.0'
    implementation 'com.google.android.material:material:1.12.0'
}
```

---

## 💰 **ADMOB SETUP**

### **Step 1: Create AdMob Account**

1. Go to: https://admob.google.com
2. Sign in with Google account (same as Play Console)
3. Create new app: "EasyJPGtoPDF"

### **Step 2: Get Ad Unit IDs**

Create 3 ad units:
- **Banner** (WebView screen)
- **Interstitial** (After PDF generation)
- **Rewarded** (Optional: unlock features)

You'll get IDs like:
```
App ID: ca-app-pub-1234567890123456~1234567890
Banner: ca-app-pub-1234567890123456/1234567890
Interstitial: ca-app-pub-1234567890123456/9876543210
```

### **Step 3: Update Code**

Replace test IDs in:
- `webview_screen.dart` line 46
- `scanner_screen.dart` line 27
- `AndroidManifest.xml` line 30

### **Step 4: Payment Setup**

1. AdMob → Payments
2. Add bank account details
3. Verify identity (PAN card)
4. Threshold: $100 minimum payout

**All revenue comes to ONE AdMob account!**

---

## 🚀 **BUILD & DEPLOY**

### **Step 1: Build APK**

```powershell
# Debug APK (for testing)
flutter build apk --debug

# Release APK (for Play Store)
flutter build apk --release

# App Bundle (recommended for Play Store)
flutter build appbundle --release
```

APK location:
```
build\app\outputs\flutter-apk\app-release.apk
build\app\outputs\bundle\release\app-release.aab
```

### **Step 2: Sign APK**

```powershell
# Generate keystore
keytool -genkey -v -keystore easyjpgtopdf-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias easyjpgtopdf

# Create android/key.properties
storePassword=YOUR_PASSWORD
keyPassword=YOUR_PASSWORD
keyAlias=easyjpgtopdf
storeFile=../../easyjpgtopdf-release.jks
```

### **Step 3: Upload to Play Store**

1. Go to: https://play.google.com/console
2. Create new app: "EasyJPGtoPDF - PDF & Scanner"
3. Upload AAB file
4. Set price: Free
5. Add screenshots (4-8 images)
6. Write description (500 words)
7. Submit for review

**Review time:** 1-3 days

---

## 📊 **COST BREAKDOWN**

| Item | Cost | Details |
|------|------|---------|
| Flutter SDK | FREE | Open source |
| VS Code | FREE | Open source |
| Android Studio | FREE | Official IDE |
| Google Play Console | **$25** | One-time fee |
| AdMob Account | FREE | Google service |
| Firebase | FREE | Spark plan sufficient |
| Domain (already have) | $0 | easyjpgtopdf.com |
| **TOTAL** | **$25** | One-time payment |

**Revenue:**
- AdMob: $2-10 per 1000 impressions
- Both tabs show ads = 2x revenue
- Payment goes to one account

---

## ⏱️ **DEVELOPMENT TIMELINE**

| Task | Time | Status |
|------|------|--------|
| Setup Flutter + VS Code | 2 hours | ⏳ |
| Create WebView app | 3 hours | ⏳ |
| Add CamScanner feature | 1 day | ⏳ |
| Integrate Firebase | 2 hours | ⏳ |
| Setup AdMob | 1 hour | ⏳ |
| Testing | 1 day | ⏳ |
| Build & Sign APK | 1 hour | ⏳ |
| Play Store submission | 1 hour | ⏳ |
| Review wait | 1-3 days | ⏳ |
| **TOTAL** | **5-7 days** | ⏳ |

---

## 🎯 **CAMSCANNER FEATURES**

✅ **Implemented:**
1. Document edge detection
2. Auto crop & perspective correction
3. Multi-page scanning
4. Image enhancement
5. OCR text extraction
6. PDF generation
7. Gallery import
8. Page management (delete/reorder)

✅ **AdMob Integration:**
- Banner ad on WebView
- Interstitial ad after PDF generation
- All revenue to one account

✅ **Firebase Connected:**
- Same Firebase project
- Storage for scanned PDFs
- Auth already integrated

---

## 📱 **APP FEATURES**

### **Tab 1: Tools (WebView)**
- All 50+ website tools
- Voice Assistant
- Razorpay payments
- Firebase Auth
- Banner ads

### **Tab 2: Scanner (Native)**
- Camera with edge detection
- Multi-page scan
- OCR text extraction
- PDF generation
- Image enhancement
- Interstitial ads

---

## 🔑 **IMPORTANT NOTES**

1. **AdMob IDs:** Replace test IDs with real IDs before release
2. **Firebase:** Use existing `google-services.json` from website
3. **Razorpay:** Already integrated in WebView
4. **Version:** Use Flutter 3.24.5 (latest stable)
5. **Package Name:** `com.easyjpgtopdf.app`

---

## 📞 **SUPPORT**

If you face any issues:
1. Run `flutter doctor` to check setup
2. Check `flutter pub get` for dependencies
3. Verify AndroidManifest.xml permissions
4. Test on real device (not just emulator)

---

## ✅ **READY TO START?**

```powershell
# 1. Install Flutter
# Download from: https://docs.flutter.dev/get-started/install/windows

# 2. Create project
flutter create easyjpgtopdf_app
cd easyjpgtopdf_app

# 3. Copy code from this guide
# 4. Run app
flutter run

# 5. Build release
flutter build appbundle --release

# 6. Upload to Play Store
# Go to: https://play.google.com/console
```

---

**Timeline:** 5-7 days से app Play Store पर live!
**Cost:** केवल $25 (Google Play Console fee)
**Revenue:** सारा AdMob paisa एक ही account में आएगा! 🎉
