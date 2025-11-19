/**
 * Cliente de Chat Seguro - WebSocket con cifrado RSA
 */

class SecureChatClient {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.authenticated = false;
        this.connecting = false;
        this.nickname = '';
        this.serverPublicKey = null;
        this.clientKeys = null;
        this.pendingResolve = null;
        this.pendingReject = null;
        
        // Elementos del DOM
        this.elements = {
            loginSection: document.getElementById('loginSection'),
            chatSection: document.getElementById('chatSection'),
            nicknameInput: document.getElementById('nicknameInput'),
            passwordInput: document.getElementById('passwordInput'),
            loginBtn: document.getElementById('loginBtn'),
            messagesContainer: document.getElementById('messages'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            statusIndicator: document.getElementById('statusIndicator'),
            statusText: document.getElementById('statusText'),
            userCount: document.getElementById('userCount'),
            currentUser: document.getElementById('currentUser')
        };
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        this.elements.loginBtn.addEventListener('click', () => this.handleLogin());
        this.elements.passwordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleLogin();
        });
        
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }
    
    async handleLogin() {
        const nickname = this.elements.nicknameInput.value.trim();
        const password = this.elements.passwordInput.value;
        
        if (!nickname || !password) {
            this.showError('Por favor ingresa nickname y contraseña');
            return;
        }
        
        // Evitar múltiples intentos de conexión simultáneos
        if (this.connecting) {
            console.log('⚠️  Ya hay una conexión en progreso');
            return;
        }
        
        this.connecting = true;
        this.nickname = nickname;
        this.elements.loginBtn.disabled = true;
        this.elements.loginBtn.textContent = 'Conectando...';
        
        try {
            await this.connect(nickname, password);
            // Conexión exitosa, no mostrar error
        } catch (error) {
            console.error('❌ Error de conexión:', error);
            // Solo mostrar error si realmente falló
            if (error.message && !this.authenticated) {
                this.showError(`Error de conexión: ${error.message}`);
            }
        } finally {
            this.connecting = false;
            if (!this.authenticated) {
                this.elements.loginBtn.disabled = false;
                this.elements.loginBtn.textContent = 'Iniciar Sesión';
            }
        }
    }
    
    async connect(nickname, password) {
        return new Promise((resolve, reject) => {
            // Cerrar cualquier conexión previa
            if (this.ws) {
                try {
                    this.ws.close();
                } catch (e) {
                    console.log('⚠️  Error cerrando WebSocket previo:', e);
                }
            }
            
            this.pendingResolve = resolve;
            this.pendingReject = reject;
            
            // Timeout de 30 segundos
            const connectionTimeout = setTimeout(() => {
                if (!this.authenticated) {
                    console.log('⏱️  Timeout de conexión');
                    reject(new Error('Timeout de conexión'));
                    if (this.ws) {
                        this.ws.close();
                    }
                }
            }, 30000);
            
            const wsUrl = `ws://${window.location.hostname}:5002`;
            console.log('🔌 Conectando a:', wsUrl);
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket conectado');
                this.updateStatus('connected', 'Conectado');
            };
            
            this.ws.onmessage = async (event) => {
                try {
                    await this.handleServerMessage(event.data, nickname, password);
                } catch (error) {
                    console.error('❌ Error manejando mensaje:', error);
                }
            };
            
            this.ws.onerror = (error) => {
                clearTimeout(connectionTimeout);
                console.error('❌ Error WebSocket:', error);
                this.updateStatus('error', 'Error de conexión');
                if (this.pendingReject && !this.authenticated) {
                    this.pendingReject(new Error('Error de conexión WebSocket'));
                    this.pendingReject = null;
                }
            };
            
            this.ws.onclose = () => {
                clearTimeout(connectionTimeout);
                console.log('🔌 WebSocket cerrado');
                if (!this.authenticated) {
                    this.updateStatus('disconnected', 'Desconectado');
                }
                this.connected = false;
            };
            
            // Limpiar timeout cuando se autentique
            const originalResolve = resolve;
            this.pendingResolve = () => {
                clearTimeout(connectionTimeout);
                originalResolve();
            };
        });
    }
    
    async handleServerMessage(message, nickname, password) {
        console.log('📥 Servidor:', message.substring(0, 100));
        
        try {
            if (message === 'PUBLIC_KEY_READY') {
                console.log('🔑 Generando claves RSA...');
                try {
                    this.clientKeys = await this.generateRSAKeys();
                    console.log('✅ Claves RSA generadas exitosamente');
                } catch (error) {
                    console.error('❌ Error generando claves:', error);
                    if (this.pendingReject) {
                        this.pendingReject(new Error('Error generando claves RSA'));
                        this.pendingReject = null;
                    }
                    this.ws.close();
                }
                
            } else if (message === 'CLIENT_PUBLIC_KEY') {
                console.log('📤 Servidor solicita clave pública del cliente');
                // Solo confirmar, esperamos recibir la clave del servidor primero
                
            } else if (message.startsWith('-----BEGIN PUBLIC KEY-----')) {
                console.log('📥 Recibiendo clave pública del servidor');
                
                // Esperar un momento si las claves aún no están listas
                let retries = 0;
                while (!this.clientKeys && retries < 50) {
                    console.log('⏳ Esperando que las claves se generen...');
                    await new Promise(r => setTimeout(r, 100));
                    retries++;
                }
                
                if (!this.clientKeys || !this.clientKeys.publicKey) {
                    console.error('❌ Las claves del cliente no están disponibles después de esperar');
                    if (this.pendingReject) {
                        this.pendingReject(new Error('Timeout generando claves del cliente'));
                        this.pendingReject = null;
                    }
                    this.ws.close();
                    return;
                }
                
                try {
                    this.serverPublicKey = await this.importPublicKey(message);
                    console.log('✅ Clave pública del servidor importada');
                    
                    // Enviar nuestra clave pública
                    const publicKeyPem = await this.exportPublicKey(this.clientKeys.publicKey);
                    const publicKeyPemBase64 = btoa(publicKeyPem);
                    
                    console.log('📤 Enviando nuestra clave pública (PEM en Base64)');
                    console.log('📄 Tamaño PEM:', publicKeyPem.length);
                    this.ws.send(publicKeyPemBase64);
                } catch (error) {
                    console.error('❌ Error procesando claves:', error);
                    if (this.pendingReject) {
                        this.pendingReject(error);
                        this.pendingReject = null;
                    }
                    this.ws.close();
                }
                
            } else if (message === 'NICK') {
                console.log('📤 Enviando nickname cifrado');
                const encryptedNick = await this.encryptWithServerKey(nickname);
                console.log('   Cifrado (primeros 50 chars):', encryptedNick.substring(0, 50));
                this.ws.send(encryptedNick);
                
            } else if (message === 'PASSWORD') {
                console.log('📤 Enviando contraseña cifrada');
                const encryptedPass = await this.encryptWithServerKey(password);
                this.ws.send(encryptedPass);
                
            } else if (message === 'AUTH_SUCCESS') {
                console.log('✅ ¡Autenticación exitosa!');
                this.authenticated = true;
                this.showChatInterface();
                this.updateStatus('authenticated', 'En línea');
                if (this.pendingResolve) {
                    this.pendingResolve();
                    this.pendingResolve = null;
                }
                
            } else if (message === 'AUTH_FAILED') {
                console.error('❌ Autenticación fallida');
                const error = new Error('Contraseña incorrecta');
                if (this.pendingReject) {
                    this.pendingReject(error);
                    this.pendingReject = null;
                }
                this.ws.close();
                
            } else if (message === 'SERVIDOR_LLENO') {
                const error = new Error('Servidor lleno');
                if (this.pendingReject) {
                    this.pendingReject(error);
                    this.pendingReject = null;
                }
                this.ws.close();
                
            } else if (this.authenticated) {
                await this.handleChatMessage(message);
            }
            
        } catch (error) {
            console.error('❌ Error procesando mensaje:', error);
            if (this.pendingReject && !this.authenticated) {
                this.pendingReject(error);
                this.pendingReject = null;
            }
        }
    }
    
    async handleChatMessage(encryptedMessage) {
        try {
            const decrypted = await this.decryptWithClientKey(encryptedMessage);
            this.displayMessage(decrypted, false);
        } catch (error) {
            console.error('❌ Error descifrando mensaje:', error);
            this.displayMessage('⚠️ [Error descifrando mensaje]', false);
        }
    }
    
    async sendMessage() {
        const text = this.elements.messageInput.value.trim();
        if (!text || !this.authenticated) return;
        
        try {
            console.log('📤 Enviando mensaje:', text);
            
            // Cifrar mensaje
            const encrypted = await this.encryptWithServerKey(text);
            console.log('   Cifrado:', encrypted.substring(0, 50) + '...');
            
            // Calcular hashes
            const sha256Hash = await this.sha256(text);
            const md5Hash = await this.md5Simple(text);
            
            console.log('   SHA256:', sha256Hash.substring(0, 32) + '...');
            console.log('   MD5:', md5Hash);
            
            // Formato: cipher|hash|md5
            const payload = `${encrypted}|${sha256Hash}|${md5Hash}`;
            
            this.ws.send(payload);
            
            // Mostrar mensaje propio
            this.displayMessage(`${this.nickname}: ${text}`, true);
            this.elements.messageInput.value = '';
            
        } catch (error) {
            console.error('❌ Error enviando mensaje:', error);
            this.showError('Error enviando mensaje');
        }
    }
    
    displayMessage(text, isOwn = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${isOwn ? 'own-message' : 'other-message'}`;
        
        if (text.includes('📢')) {
            msgDiv.className = 'message system-message';
        }
        
        msgDiv.textContent = text;
        this.elements.messagesContainer.appendChild(msgDiv);
        this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
    }
    
    showChatInterface() {
        this.elements.loginSection.style.display = 'none';
        this.elements.chatSection.style.display = 'flex';
        this.elements.currentUser.textContent = this.nickname;
        this.elements.messageInput.focus();
    }
    
    updateStatus(status, text) {
        this.elements.statusIndicator.className = `status-indicator ${status}`;
        this.elements.statusText.textContent = text;
    }
    
    showError(message) {
        alert(message);
    }
    
    // ===== CRIPTOGRAFÍA =====
    
    async generateRSAKeys() {
        return await window.crypto.subtle.generateKey(
            {
                name: 'RSA-OAEP',
                modulusLength: 2048,
                publicExponent: new Uint8Array([1, 0, 1]),
                hash: 'SHA-256'
            },
            true,
            ['encrypt', 'decrypt']
        );
    }
    
    async exportPublicKey(publicKey) {
        const exported = await window.crypto.subtle.exportKey('spki', publicKey);
        const exportedAsString = String.fromCharCode(...new Uint8Array(exported));
        const exportedAsBase64 = btoa(exportedAsString);
        return `-----BEGIN PUBLIC KEY-----\n${exportedAsBase64}\n-----END PUBLIC KEY-----`;
    }
    
    async importPublicKey(pem) {
        const pemContents = pem
            .replace('-----BEGIN PUBLIC KEY-----', '')
            .replace('-----END PUBLIC KEY-----', '')
            .replace(/\s/g, '');
        
        const binaryDer = atob(pemContents);
        const binaryDerArray = new Uint8Array(binaryDer.length);
        for (let i = 0; i < binaryDer.length; i++) {
            binaryDerArray[i] = binaryDer.charCodeAt(i);
        }
        
        return await window.crypto.subtle.importKey(
            'spki',
            binaryDerArray,
            { name: 'RSA-OAEP', hash: 'SHA-256' },
            true,
            ['encrypt']
        );
    }
    
    async encryptWithServerKey(text) {
        const encoded = new TextEncoder().encode(text);
        const encrypted = await window.crypto.subtle.encrypt(
            { name: 'RSA-OAEP' },
            this.serverPublicKey,
            encoded
        );
        return btoa(String.fromCharCode(...new Uint8Array(encrypted)));
    }
    
    async decryptWithClientKey(encryptedBase64) {
        const encrypted = Uint8Array.from(atob(encryptedBase64), c => c.charCodeAt(0));
        const decrypted = await window.crypto.subtle.decrypt(
            { name: 'RSA-OAEP' },
            this.clientKeys.privateKey,
            encrypted
        );
        return new TextDecoder().decode(decrypted);
    }
    
    async sha256(text) {
        const encoded = new TextEncoder().encode(text);
        const hash = await window.crypto.subtle.digest('SHA-256', encoded);
        return Array.from(new Uint8Array(hash))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }
    
    async md5Simple(str) {
        function rotateLeft(value, shift) {
            return (value << shift) | (value >>> (32 - shift));
        }
        
        function addUnsigned(x, y) {
            const lsw = (x & 0xFFFF) + (y & 0xFFFF);
            const msw = (x >> 16) + (y >> 16) + (lsw >> 16);
            return (msw << 16) | (lsw & 0xFFFF);
        }
        
        function F(x, y, z) { return (x & y) | ((~x) & z); }
        function G(x, y, z) { return (x & z) | (y & (~z)); }
        function H(x, y, z) { return x ^ y ^ z; }
        function I(x, y, z) { return y ^ (x | (~z)); }
        
        function FF(a, b, c, d, x, s, ac) {
            a = addUnsigned(a, addUnsigned(addUnsigned(F(b, c, d), x), ac));
            return addUnsigned(rotateLeft(a, s), b);
        }
        
        function GG(a, b, c, d, x, s, ac) {
            a = addUnsigned(a, addUnsigned(addUnsigned(G(b, c, d), x), ac));
            return addUnsigned(rotateLeft(a, s), b);
        }
        
        function HH(a, b, c, d, x, s, ac) {
            a = addUnsigned(a, addUnsigned(addUnsigned(H(b, c, d), x), ac));
            return addUnsigned(rotateLeft(a, s), b);
        }
        
        function II(a, b, c, d, x, s, ac) {
            a = addUnsigned(a, addUnsigned(addUnsigned(I(b, c, d), x), ac));
            return addUnsigned(rotateLeft(a, s), b);
        }
        
        function convertToWordArray(str) {
            let lWordCount;
            const lMessageLength = str.length;
            const lNumberOfWords_temp1 = lMessageLength + 8;
            const lNumberOfWords_temp2 = (lNumberOfWords_temp1 - (lNumberOfWords_temp1 % 64)) / 64;
            const lNumberOfWords = (lNumberOfWords_temp2 + 1) * 16;
            const lWordArray = new Array(lNumberOfWords - 1);
            let lBytePosition = 0;
            let lByteCount = 0;
            
            while (lByteCount < lMessageLength) {
                lWordCount = (lByteCount - (lByteCount % 4)) / 4;
                lBytePosition = (lByteCount % 4) * 8;
                lWordArray[lWordCount] = (lWordArray[lWordCount] | (str.charCodeAt(lByteCount) << lBytePosition));
                lByteCount++;
            }
            
            lWordCount = (lByteCount - (lByteCount % 4)) / 4;
            lBytePosition = (lByteCount % 4) * 8;
            lWordArray[lWordCount] = lWordArray[lWordCount] | (0x80 << lBytePosition);
            lWordArray[lNumberOfWords - 2] = lMessageLength << 3;
            lWordArray[lNumberOfWords - 1] = lMessageLength >>> 29;
            
            return lWordArray;
        }
        
        function wordToHex(lValue) {
            let wordToHexValue = "";
            for (let lCount = 0; lCount <= 3; lCount++) {
                const lByte = (lValue >>> (lCount * 8)) & 255;
                const wordToHexValue_temp = "0" + lByte.toString(16);
                wordToHexValue = wordToHexValue + wordToHexValue_temp.substr(wordToHexValue_temp.length - 2, 2);
            }
            return wordToHexValue;
        }
        
        const x = convertToWordArray(str);
        let a = 0x67452301, b = 0xEFCDAB89, c = 0x98BADCFE, d = 0x10325476;
        
        const S11=7, S12=12, S13=17, S14=22;
        const S21=5, S22=9, S23=14, S24=20;
        const S31=4, S32=11, S33=16, S34=23;
        const S41=6, S42=10, S43=15, S44=21;
        
        for (let k = 0; k < x.length; k += 16) {
            const AA=a, BB=b, CC=c, DD=d;
            
            a=FF(a,b,c,d,x[k+0],S11,0xD76AA478);d=FF(d,a,b,c,x[k+1],S12,0xE8C7B756);
            c=FF(c,d,a,b,x[k+2],S13,0x242070DB);b=FF(b,c,d,a,x[k+3],S14,0xC1BDCEEE);
            a=FF(a,b,c,d,x[k+4],S11,0xF57C0FAF);d=FF(d,a,b,c,x[k+5],S12,0x4787C62A);
            c=FF(c,d,a,b,x[k+6],S13,0xA8304613);b=FF(b,c,d,a,x[k+7],S14,0xFD469501);
            a=FF(a,b,c,d,x[k+8],S11,0x698098D8);d=FF(d,a,b,c,x[k+9],S12,0x8B44F7AF);
            c=FF(c,d,a,b,x[k+10],S13,0xFFFF5BB1);b=FF(b,c,d,a,x[k+11],S14,0x895CD7BE);
            a=FF(a,b,c,d,x[k+12],S11,0x6B901122);d=FF(d,a,b,c,x[k+13],S12,0xFD987193);
            c=FF(c,d,a,b,x[k+14],S13,0xA679438E);b=FF(b,c,d,a,x[k+15],S14,0x49B40821);
            
            a=GG(a,b,c,d,x[k+1],S21,0xF61E2562);d=GG(d,a,b,c,x[k+6],S22,0xC040B340);
            c=GG(c,d,a,b,x[k+11],S23,0x265E5A51);b=GG(b,c,d,a,x[k+0],S24,0xE9B6C7AA);
            a=GG(a,b,c,d,x[k+5],S21,0xD62F105D);d=GG(d,a,b,c,x[k+10],S22,0x2441453);
            c=GG(c,d,a,b,x[k+15],S23,0xD8A1E681);b=GG(b,c,d,a,x[k+4],S24,0xE7D3FBC8);
            a=GG(a,b,c,d,x[k+9],S21,0x21E1CDE6);d=GG(d,a,b,c,x[k+14],S22,0xC33707D6);
            c=GG(c,d,a,b,x[k+3],S23,0xF4D50D87);b=GG(b,c,d,a,x[k+8],S24,0x455A14ED);
            a=GG(a,b,c,d,x[k+13],S21,0xA9E3E905);d=GG(d,a,b,c,x[k+2],S22,0xFCEFA3F8);
            c=GG(c,d,a,b,x[k+7],S23,0x676F02D9);b=GG(b,c,d,a,x[k+12],S24,0x8D2A4C8A);
            
            a=HH(a,b,c,d,x[k+5],S31,0xFFFA3942);d=HH(d,a,b,c,x[k+8],S32,0x8771F681);
            c=HH(c,d,a,b,x[k+11],S33,0x6D9D6122);b=HH(b,c,d,a,x[k+14],S34,0xFDE5380C);
            a=HH(a,b,c,d,x[k+1],S31,0xA4BEEA44);d=HH(d,a,b,c,x[k+4],S32,0x4BDECFA9);
            c=HH(c,d,a,b,x[k+7],S33,0xF6BB4B60);b=HH(b,c,d,a,x[k+10],S34,0xBEBFBC70);
            a=HH(a,b,c,d,x[k+13],S31,0x289B7EC6);d=HH(d,a,b,c,x[k+0],S32,0xEAA127FA);
            c=HH(c,d,a,b,x[k+3],S33,0xD4EF3085);b=HH(b,c,d,a,x[k+6],S34,0x4881D05);
            a=HH(a,b,c,d,x[k+9],S31,0xD9D4D039);d=HH(d,a,b,c,x[k+12],S32,0xE6DB99E5);
            c=HH(c,d,a,b,x[k+15],S33,0x1FA27CF8);b=HH(b,c,d,a,x[k+2],S34,0xC4AC5665);
            
            a=II(a,b,c,d,x[k+0],S41,0xF4292244);d=II(d,a,b,c,x[k+7],S42,0x432AFF97);
            c=II(c,d,a,b,x[k+14],S43,0xAB9423A7);b=II(b,c,d,a,x[k+5],S44,0xFC93A039);
            a=II(a,b,c,d,x[k+12],S41,0x655B59C3);d=II(d,a,b,c,x[k+3],S42,0x8F0CCC92);
            c=II(c,d,a,b,x[k+10],S43,0xFFEFF47D);b=II(b,c,d,a,x[k+1],S44,0x85845DD1);
            a=II(a,b,c,d,x[k+8],S41,0x6FA87E4F);d=II(d,a,b,c,x[k+15],S42,0xFE2CE6E0);
            c=II(c,d,a,b,x[k+6],S43,0xA3014314);b=II(b,c,d,a,x[k+13],S44,0x4E0811A1);
            a=II(a,b,c,d,x[k+4],S41,0xF7537E82);d=II(d,a,b,c,x[k+11],S42,0xBD3AF235);
            c=II(c,d,a,b,x[k+2],S43,0x2AD7D2BB);b=II(b,c,d,a,x[k+9],S44,0xEB86D391);
            
            a=addUnsigned(a,AA);b=addUnsigned(b,BB);
            c=addUnsigned(c,CC);d=addUnsigned(d,DD);
        }
        
        return (wordToHex(a)+wordToHex(b)+wordToHex(c)+wordToHex(d)).toLowerCase();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.chatClient = new SecureChatClient();
    console.log('✅ Cliente de chat inicializado');
});