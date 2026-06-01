// frontend/src/utils/deviceCapabilities.js

class DeviceCapabilityDetector {
    static async detectAvailableMethods() {
        const methods = [];

        // 🔍 كشف الكاميرا
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                if (stream.getVideoTracks().length > 0) {
                    methods.push('face');
                    stream.getTracks().forEach(track => track.stop());
                }
            } catch (error) {
                console.log('Camera not available');
            }
        }
        
        // 🎤 كشف الميكروفون
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                if (stream.getAudioTracks().length > 0) {
                    methods.push('voice');
                    stream.getTracks().forEach(track => track.stop());
                }
            } catch (error) {
                console.log('Microphone not available');
            }
        }
        
        // 👆 كشف بصمة الإصبع (WebAuthn API)
        if (window.PublicKeyCredential) {
            try {
                const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
                if (available) {
                    methods.push('fingerprint');
                }
            } catch (error) {
                console.log('Fingerprint not available');
            }
        }
        
        // ✍ التوقيع اليدوي متاح دائماً
        methods.push('signature');
        
        return methods;
    }
    
    static getMethodDetails(method, language = 'en') {
        const details = {
            en: {
                'face': { 
                    name: 'Face Recognition', 
                    icon: '👤', 
                    description: 'Capture your face using camera', 
                    requires: 'Camera', 
                    security: 'High' 
                },
                'voice': { 
                    name: 'Voice Recognition', 
                    icon: '🎤', 
                    description: 'Record your voice using microphone', 
                    requires: 'Microphone', 
                    security: 'Medium' 
                },
                'fingerprint': { 
                    name: 'Fingerprint', 
                    icon: '👆', 
                    description: 'Use your fingerprint sensor', 
                    requires: 'Fingerprint sensor', 
                    security: 'Very High' 
                },
                'signature': { 
                    name: 'Digital Signature', 
                    icon: '✍', 
                    description: 'Draw your signature', 
                    requires: 'Mouse or touch', 
                    security: 'Medium' 
                },
            },
            ar: {
                'face': { 
                    name: 'بصمة الوجه', 
                    icon: '👤', 
                    description: 'التقط صورة لوجهك باستخدام الكاميرا', 
                    requires: 'كاميرا', 
                    security: 'عالية' 
                },
                'voice': { 
                    name: 'بصمة الصوت', 
                    icon: '🎤', 
                    description: 'سجل صوتك باستخدام الميكروفون', 
                    requires: 'ميكروفون', 
                    security: 'متوسطة' 
                },
                'fingerprint': { 
                    name: 'بصمة الإصبع', 
                    icon: '👆', 
                    description: 'استخدم مستشعر البصمة في جهازك', 
                    requires: 'مستشعر بصمة', 
                    security: 'عالية جداً' 
                },
                'signature': { 
                    name: 'التوقيع الرقمي', 
                    icon: '✍', 
                    description: 'ارسم توقيعك باستخدام الماوس أو اللمس', 
                    requires: 'ماوس أو شاشة لمس', 
                    security: 'متوسطة' 
                },
            }
        };
        
        return details[language]?.[method] || details.en[method];
    }
    
    static async getRecommendedMethod() {
        const methods = await this.detectAvailableMethods();
        const priority = ['fingerprint', 'face', 'voice', 'signature'];
        
        for (const method of priority) {
            if (methods.includes(method)) {
                return method;
            }
        }
        
        return 'signature';
    }
    
    static isMethodSupported(method) {
        const supportedMethods = {
            'face': () => {
                return navigator.mediaDevices && navigator.mediaDevices.getUserMedia;
            },
            'voice': () => {
                return navigator.mediaDevices && navigator.mediaDevices.getUserMedia;
            },
            'fingerprint': () => {
                return window.PublicKeyCredential !== undefined;
            },
            'signature': () => true,
        };
        
        return supportedMethods[method]?.() || false;
    }
    
    static async handleFingerprintAuth() {
        try {
            const publicKey = {
                challenge: new Uint8Array(32),
                rp: {
                    name: "SkillSwap Platform",
                    id: window.location.hostname
                },
                user: {
                    id: new Uint8Array(16),
                    name: "user@example.com",
                    displayName: "User"
                },
                pubKeyCredParams: [{ alg: -7, type: "public-key" }],
                timeout: 60000,
                attestation: "direct"
            };

            const credential = await navigator.credentials.create({ publicKey });
            
            const credentialData = {
                id: credential.id,
                rawId: Array.from(new Uint8Array(credential.rawId)),
                type: credential.type,
                response: {
                    attestationObject: Array.from(new Uint8Array(credential.response.attestationObject)),
                    clientDataJSON: Array.from(new Uint8Array(credential.response.clientDataJSON))
                }
            };
            
            return credentialData;
        } catch (error) {
            throw new Error("Fingerprint authentication failed: " + error.message);
        }
    }
}

export default DeviceCapabilityDetector;
