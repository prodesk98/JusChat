document.addEventListener('DOMContentLoaded', function () {
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
                uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Enviando...';
                uploadBtn.disabled = true;

                setTimeout(() => {
                    alert('Documentos enviados com sucesso! A análise será realizada em breve.');
                    uploadBtn.innerHTML = '<i class="fas fa-upload mr-2"></i> Enviar Documentos para Análise';
                    uploadBtn.disabled = false;
                    fileList.classList.add('hidden');
                    fileInput.value = '';
                    fileItems.innerHTML = '';
                }, 2000);
            } else {
                alert('Por favor, selecione pelo menos um documento para enviar.');
            }
        });
    }

    // Chat
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    if (messageInput && sendBtn && chatMessages) {
        function sendMessage() {
            const message = messageInput.value.trim();
            if (message) {
                addMessage(message, 'user');
                messageInput.value = '';
                setTimeout(() => {
                    const responses = [
                        "Entendi sua solicitação. Para documentos jurídicos como esse, recomendo verificar especialmente as cláusulas de rescisão e multas contratuais.",
                        "Com base na legislação atual, esse tipo de contrato precisa conter especificamente...",
                        "Analisando sua pergunta, encontrei precedentes jurisprudenciais relevantes que podem ajudar...",
                        "Para esse tipo de documento, é essencial verificar a conformidade com o artigo 55 do Código Civil.",
                        "Sugiro revisar as obrigações das partes e os prazos estabelecidos, que são pontos críticos nesse tipo de contrato."
                    ];
                    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
                    addMessage(randomResponse, 'bot');
                }, 1000);
            }
        }

        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${sender} mb-4`;

            messageDiv.innerHTML = sender === 'user' ?
                `
                <div class="flex items-start justify-end">
                    <div class="mr-3">
                        <div class="bg-legal-blue text-white rounded-xl p-4 shadow-sm max-w-3xl">
                            <p>${text}</p>
                        </div>
                        <span class="text-xs text-gray-500 mt-1 block text-right mr-1">Agora</span>
                    </div>
                    <div class="bg-gray-200 text-gray-800 rounded-full w-10 h-10 flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-user"></i>
                    </div>
                </div>
                `
                :
                `
                <div class="flex items-start">
                    <div class="bg-legal-blue text-white rounded-full w-10 h-10 flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-scale-balanced"></i>
                    </div>
                    <div class="ml-3">
                        <div class="bg-white rounded-xl p-4 shadow-sm max-w-3xl">
                            <p>${text}</p>
                        </div>
                        <span class="text-xs text-gray-500 mt-1 block ml-1">Agora</span>
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
});
