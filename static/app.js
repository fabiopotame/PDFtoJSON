// JavaScript para PDF to JSON Converter
class PDFConverter {
    constructor() {
        this.API_BASE_URL = 'http://192.168.50.91:8085';
        this.initializeElements();
        this.setupEventListeners();
        this.checkApiStatus();
        this.startStatusInterval();
    }

    initializeElements() {
        this.fileInput = document.getElementById('fileInput');
        this.selectFileBtn = document.getElementById('selectFileBtn');
        this.uploadArea = document.getElementById('uploadArea');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.loading = document.getElementById('loading');
        this.result = document.getElementById('result');
        this.error = document.getElementById('error');
        this.jsonOutput = document.getElementById('jsonOutput');
        this.errorMessage = document.getElementById('errorMessage');
        this.apiStatus = document.getElementById('api-status');
    }

    setupEventListeners() {
        // Eventos de drag and drop
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', () => this.handleDragLeave());
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        
        // Evento de clique na área de upload (apenas se não for um botão)
        this.uploadArea.addEventListener('click', (e) => {
            // Evitar abrir o file input se o clique foi em um botão ou elemento com onclick
            if (e.target.tagName === 'BUTTON' || e.target.onclick || e.target.closest('button')) {
                return;
            }
            this.fileInput.click();
        });

        // Evento do botão "Selecionar PDF"
        this.selectFileBtn.addEventListener('click', () => {
            this.fileInput.click();
        });

        // Evento de seleção de arquivo
        this.fileInput.addEventListener('change', (e) => this.handleFileInputChange(e));
    }

    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }

    handleDragLeave() {
        this.uploadArea.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFileSelect(files[0]);
        }
    }

    handleFileInputChange(e) {
        if (e.target.files.length > 0) {
            this.handleFileSelect(e.target.files[0]);
        }
    }

    handleFileSelect(file) {
        // Validar tipo de arquivo
        if (file.type !== 'application/pdf') {
            this.showError('Por favor, selecione apenas arquivos PDF.');
            return;
        }

        // Validar tamanho do arquivo (16MB máximo)
        const maxSize = 16 * 1024 * 1024; // 16MB
        if (file.size > maxSize) {
            this.showError('O arquivo é muito grande. Tamanho máximo permitido: 16MB.');
            return;
        }

        // Exibir informações do arquivo
        this.fileName.textContent = `Nome: ${file.name}`;
        this.fileSize.textContent = `Tamanho: ${this.formatFileSize(file.size)}`;
        this.fileInfo.style.display = 'block';
        this.fileInfo.classList.add('fade-in');
        this.uploadBtn.style.display = 'inline-block';
        
        // Limpar resultados anteriores
        this.hideResultsAndErrors();
        
        // Configurar evento do botão
        this.uploadBtn.onclick = () => this.uploadFile(file);
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        // Mostrar estado de carregamento
        this.showLoading();
        this.uploadBtn.disabled = true;

        try {
            const response = await fetch(`${this.API_BASE_URL}/document`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                this.showSuccess(data);
                this.showToast('Arquivo convertido com sucesso!', 'success');
            } else {
                this.showError(data.error || 'Erro ao processar o arquivo.');
                // Mostrar detalhes do erro se disponível
                if (data.document_title || data.supported_types) {
                    this.showErrorDetails(data);
                }
            }
        } catch (err) {
            this.showError('Erro de conexão com a API. Verifique se o servidor está rodando.');
            console.error('Erro na requisição:', err);
        } finally {
            this.hideLoading();
            this.uploadBtn.disabled = false;
        }
    }

    showLoading() {
        this.loading.style.display = 'block';
        this.hideResultsAndErrors();
    }

    hideLoading() {
        this.loading.style.display = 'none';
    }

    showSuccess(data) {
        this.jsonOutput.textContent = JSON.stringify(data, null, 2);
        this.result.style.display = 'block';
        this.result.classList.add('fade-in');
        this.addCopyButton();
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.error.style.display = 'block';
        this.error.classList.add('fade-in');
        this.result.style.display = 'none';
    }

    showErrorDetails(errorData) {
        let details = '';
        if (errorData.document_title) {
            details += `Documento encontrado: ${errorData.document_title}\n`;
        }
        if (errorData.supported_types) {
            details += `Tipos suportados:\n${errorData.supported_types.map(type => `- ${type}`).join('\n')}`;
        }
        
        if (details) {
            const errorDetails = document.createElement('div');
            errorDetails.className = 'error-details';
            errorDetails.textContent = details;
            this.error.appendChild(errorDetails);
        }
    }

    hideResultsAndErrors() {
        this.result.style.display = 'none';
        this.error.style.display = 'none';
        // Remover detalhes de erro anteriores
        const existingDetails = this.error.querySelector('.error-details');
        if (existingDetails) {
            existingDetails.remove();
        }
    }

    addCopyButton() {
        // Remover botão anterior se existir
        const existingButton = this.result.querySelector('.copy-button');
        if (existingButton) {
            existingButton.remove();
        }

        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.innerHTML = '<i class="fas fa-copy"></i> Copiar';
        copyButton.onclick = () => this.copyToClipboard();
        this.result.appendChild(copyButton);
    }

    async copyToClipboard() {
        try {
            // Primeiro, tentar usar a API moderna do clipboard
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(this.jsonOutput.textContent);
                this.showToast('JSON copiado para a área de transferência!', 'success');
                return;
            }
            
            // Fallback: usar o método mais antigo e compatível
            this.fallbackCopyToClipboard();
            
        } catch (err) {
            console.error('Erro ao copiar com clipboard API:', err);
            // Se a API clipboard falhar, tentar o fallback
            this.fallbackCopyToClipboard();
        }
    }

    fallbackCopyToClipboard() {
        try {
            // Criar um elemento de texto temporário
            const textArea = document.createElement('textarea');
            textArea.value = this.jsonOutput.textContent;
            
            // Adicionar ao DOM temporariamente
            document.body.appendChild(textArea);
            
            // Selecionar o texto
            textArea.select();
            textArea.setSelectionRange(0, 99999); // Para mobile
            
            // Copiar usando o comando execCommand
            const successful = document.execCommand('copy');
            
            // Remover o elemento temporário
            document.body.removeChild(textArea);
            
            if (successful) {
                this.showToast('JSON copiado para a área de transferência!', 'success');
            } else {
                throw new Error('execCommand falhou');
            }
            
        } catch (err) {
            console.error('Erro ao copiar com fallback:', err);
            this.showToast('Erro ao copiar para a área de transferência.', 'error');
        }
    }

    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Mostrar toast
        setTimeout(() => toast.classList.add('show'), 100);

        // Remover toast após 3 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }

    async checkApiStatus() {
        this.apiStatus.textContent = '🔄 Verificando...';
        this.apiStatus.className = 'status-indicator status-checking';

        try {
            const response = await fetch(`${this.API_BASE_URL}/health`);
            const data = await response.json();
            
            if (response.ok && data.status === 'healthy') {
                this.apiStatus.textContent = '✅ API Online';
                this.apiStatus.className = 'status-indicator status-healthy';
            } else {
                throw new Error('API não está saudável');
            }
        } catch (err) {
            this.apiStatus.textContent = '❌ API Offline';
            this.apiStatus.className = 'status-indicator status-error';
            console.error('Erro ao verificar status da API:', err);
        }
    }

    startStatusInterval() {
        // Verificar status a cada 30 segundos
        setInterval(() => this.checkApiStatus(), 30000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Inicializar a aplicação quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    new PDFConverter();
});

// Adicionar algumas funcionalidades extras
document.addEventListener('DOMContentLoaded', () => {
    // Adicionar animação de entrada
    const mainContainer = document.querySelector('.main-container');
    if (mainContainer) {
        mainContainer.classList.add('fade-in');
    }

    // Adicionar atalhos de teclado
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            document.getElementById('fileInput').click();
        }
    });
}); 