tailwind.config = {
    theme: {
        extend: {
            colors: {
                'legal-blue': '#2548bf',
                'legal-dark': '#0f172a',
                'legal-light': '#f1f5f9'
            }
        }
    }
}
// Socket.IO
const socket = io();

const markdownConverter = new showdown.Converter();
const uuid = () => {
    return crypto.randomUUID()
}
const storage = {
    set(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    },

    get(key) {
        const item = localStorage.getItem(key);
        try {
            return JSON.parse(item);
        } catch {
            return item;
        }
    },

    remove(key) {
        localStorage.removeItem(key);
    },

    has(key) {
        return localStorage.getItem(key) !== null;
    }
};

// Tabs
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));

        btn.classList.add('active');

        const contentId = btn.dataset.target || btn.id.replace('-tab', '-content');
        const contentEl = document.getElementById(contentId);
        if (contentEl) {
            contentEl.classList.add('active');
        }
    });
});

// File Upload
const fileDropArea = document.getElementById('file-drop-area');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const fileItems = document.getElementById('file-items');
const uploadBtn = document.getElementById('upload-btn');

if (fileDropArea && fileInput && fileList && fileItems && uploadBtn) {
    fileDropArea.addEventListener('click', () => fileInput.click());

    fileDropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileDropArea.classList.add('active');
    });

    fileDropArea.addEventListener('dragleave', () => {
        fileDropArea.classList.remove('active');
    });

    fileDropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileDropArea.classList.remove('active');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', () => {
        handleFiles(fileInput.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            fileList.classList.remove('hidden');
            fileItems.innerHTML = '';

            Array.from(files).forEach((file, i) => {
                const listItem = document.createElement('li');
                listItem.className = 'flex items-center justify-between bg-gray-50 p-2 rounded';
                listItem.innerHTML = `
                        <div class="flex items-center">
                            <i class="fas fa-file text-gray-500 mr-3"></i>
                            <div>
                                <p class="text-sm font-medium truncate max-w-xs">${file.name}</p>
                                <p class="text-xs text-gray-500">${formatFileSize(file.size)}</p>
                            </div>
                        </div>
                        <button class="text-red-500 hover:text-red-700 remove-file" type="button" data-index="${i}">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                fileItems.appendChild(listItem);
            });

            // Delegate remove buttons (using event delegation for dynamic items)
            fileItems.querySelectorAll('.remove-file').forEach(btn => {
                btn.addEventListener('click', function () {
                    this.closest('li').remove();
                    if (!fileItems.children.length) {
                        fileList.classList.add('hidden');
                    }
                });
            });
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    uploadBtn.addEventListener('click', () => {
        if (fileInput.files.length > 0) {
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
            uploadBtn.disabled = true;

            const formData = new FormData();
            Array.from(fileInput.files).forEach(file => {
                formData.append('files', file);
            });

            let alertError = document.getElementById('document-uploaded-error');
            let alertSuccess = document.getElementById('document-uploaded-success');

            if (alertError !== null) alertError.innerHTML = '';
            if (alertSuccess !== null) alertSuccess.innerHTML = '';

            fetch('/knowledge/update', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    console.log('Resposta do servidor:', data);
                    uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Enviar Documentos para Análise';
                    uploadBtn.disabled = false;
                    fileList.classList.add('hidden');
                    if (!data.success && alertError !== null) alertError.innerHTML = data.message;
                    else if (data.success && alertSuccess !== null) alertSuccess.innerHTML = data.message;
                })
                .catch(error => {
                    console.error('Erro no envio:', error);
                    uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Enviar Documentos para Análise';
                    uploadBtn.disabled = false;
                    if (alertError !== null) alertError.innerHTML = JSON.stringify(error);
                });

            console.log('FormData construído:', Array.from(formData.entries()));

        } else {
            alert('Por favor, selecione pelo menos um documento para enviar.');
        }
    });
}

function renderChatHistory(messages) {
    chatMessages.innerHTML = '';

    messages.forEach(msg => {
        const sender = msg.role === 'user' ? 'user' : 'bot';
        addMessage(msg.content, sender);
    });
}

function toast(message, type = 'info') {
    let style = 'linear-gradient(to right, #00b09b, #96c93d)';
    if (type === 'error') {
        style = 'linear-gradient(to right, #ff5f6d, #ffc371)';
    } else if (type === 'success') {
        style = 'linear-gradient(to right, #00c6ff, #0072ff)';
    }
    Toastify({
        text: message,
        className: type,
        style: {
            background: style,
        },
    }).showToast();
}

// Chat
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');

const defaultBtnText = sendBtn.innerHTML;
const btnLoadingText = '<i class="fas fa-spinner fa-spin"></i>';

function sendMessage() {
    const message = messageInput.value.trim();
    if (message) {
        const messageId = uuid();
        storage.set("currentMessageId", messageId);
        addMessage(message, 'user');
        addMessage('...', 'assistant', messageId);
        socket.emit('invoke_agent', {chat_id: getChatId(), question: message});
        messageInput.value = '';
        messageInput.disabled = true;
        sendBtn.disabled = true;
        sendBtn.innerHTML = btnLoadingText;
    }
}

if (messageInput && sendBtn && chatMessages) {

    function getChatId() {
        if (storage.has('chatId')) return storage.get('chatId');
        const chatId = uuid();
        storage.set('chatId', chatId);
        return chatId;
    }

    function addMessage(text, sender, id = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender} mb-4`;

        messageDiv.innerHTML = sender === 'user' ?
            `
                <div class="flex items-start justify-end" id="message-${id || uuid()}">
                    <div class="mr-3">
                        <div class="bg-legal-dark text-white rounded-xl p-4 shadow-sm max-w-3xl" id="${id || uuid()}">
                            <p>${markdownConverter.makeHtml(text)}</p>
                        </div>
                    </div>
                    <div class="bg-gray-200 text-gray-800 rounded-full w-10 h-10 flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-user"></i>
                    </div>
                </div>
                `
            :
            `
                <div class="flex items-start" id="message-${id || uuid()}">
                    <div class="bg-legal-dark text-white rounded-full w-10 h-10 flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-scale-balanced"></i>
                    </div>
                    <div class="ml-3">
                        <div class="bg-white rounded-xl p-4 shadow-sm max-w-3xl" id="${id || uuid()}">
                            <p>${markdownConverter.makeHtml(text)}</p>
                        </div>
                    </div>
                </div>
                `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    messageInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = `${this.scrollHeight}px`;
    });
}

function newChat() {
    messageInput.value = '';
    chatMessages.innerHTML = '';
    chatMessages.scrollTop = 0;
    storage.remove('chatId');
    socket.emit('chat_history', {chat_id: getChatId()});
    toast('Novo chat iniciado', 'success');
}


// WebSocket Events
socket.on('history_updated', (data) => {
    const history = data.history || [];
    renderChatHistory(history);
});
socket.on('agent_response', (data) => {
    const response = data.result || '';
    addMessage(response, 'assistant');
    messageInput.disabled = false;
    sendBtn.disabled = false;
    messageInput.focus();
    chatMessages.scrollTop = chatMessages.scrollHeight;
    sendBtn.innerHTML = defaultBtnText;
    const message = document.getElementById(`message-${storage.get("currentMessageId")}`);
    if (message) {
        message.remove();
        storage.remove('currentMessageId');
    }
});
socket.on('agent_updated', (data) => {
    const response = data.status || '';
    const messageContent = document.getElementById(storage.get("currentMessageId"));
    if (messageContent) messageContent.innerHTML = markdownConverter.makeHtml(response);
});
socket.on('error', (data) => {
    console.error('WebSocket error:', data.message);
    toast(data.message, 'error');
});
socket.on('connect', () => {
    console.log('Connected to WebSocket server');
    socket.emit('chat_history', {chat_id: getChatId()});
});
socket.on('disconnect', () => {
    console.log('Disconnected from WebSocket server');
});

//
