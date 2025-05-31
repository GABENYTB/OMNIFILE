import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import threading
from pathlib import Path
import google.generativeai as genai
from docx import Document
import PyPDF2
import json
import re
from datetime import datetime
from PIL import Image, ImageTk  # Para trabalhar com imagens/logos

class FileOrganizer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Organizador Inteligente de Arquivos com IA")
        self.root.geometry("800x700")
        self.root.configure(bg="#f0f0f0")
        
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Configure a API do Gemini para começar")
        
        self.gemini_api_key = ""
        self.model = None
        self.config_file = "organizer_config.json"
        
        # Variáveis para logos/imagens
        self.logo_images = {}
        self.assets_folder = "assets"  # Pasta onde ficam os logos
        
        self.create_assets_folder()
        self.load_logos()
        self.setup_ui()
        self.load_config()
    
    def create_assets_folder(self):
        """Cria pasta para assets se não existir"""
        if not os.path.exists(self.assets_folder):
            os.makedirs(self.assets_folder)
            # Cria arquivo de instruções
            instructions = """
INSTRUÇÕES PARA ADICIONAR LOGOS/IMAGENS:

1. Coloque seus arquivos de logo/imagem na pasta 'assets/'
2. Formatos suportados: PNG, JPG, JPEG, GIF, BMP
3. Nomes sugeridos para posicionamento automático:
   - logo_header.png (logo do cabeçalho)
   - logo_sidebar.png (logo lateral)
   - background.png (imagem de fundo)
   - icon_gemini.png (ícone do Gemini)
   - watermark.png (marca d'água)

4. Tamanhos recomendados:
   - Logo header: 200x60 pixels
   - Logo sidebar: 150x150 pixels
   - Ícones: 32x32 ou 64x64 pixels
   - Background: 1920x1080 pixels (será redimensionado)

5. Use PNG com transparência para melhor resultado
"""
            with open(os.path.join(self.assets_folder, "LEIA-ME.txt"), "w", encoding="utf-8") as f:
                f.write(instructions)
    
    def load_logos(self):
        """Carrega todas as imagens da pasta assets"""
        supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        
        if not os.path.exists(self.assets_folder):
            return
            
        for filename in os.listdir(self.assets_folder):
            if filename.lower().endswith(supported_formats):
                try:
                    image_path = os.path.join(self.assets_folder, filename)
                    # Carrega e processa a imagem
                    pil_image = Image.open(image_path)
                    
                    # Define tamanhos baseado no nome do arquivo
                    if 'header' in filename.lower():
                        pil_image = pil_image.resize((200, 60), Image.Resampling.LANCZOS)
                    elif 'sidebar' in filename.lower():
                        pil_image = pil_image.resize((120, 120), Image.Resampling.LANCZOS)
                    elif 'icon' in filename.lower():
                        pil_image = pil_image.resize((32, 32), Image.Resampling.LANCZOS)
                    elif 'watermark' in filename.lower():
                        pil_image = pil_image.resize((100, 100), Image.Resampling.LANCZOS)
                    elif 'background' in filename.lower():
                        pil_image = pil_image.resize((800, 700), Image.Resampling.LANCZOS)
                    
                    # Converte para PhotoImage
                    tk_image = ImageTk.PhotoImage(pil_image)
                    
                    # Armazena com nome limpo (sem extensão)
                    clean_name = os.path.splitext(filename)[0].lower()
                    self.logo_images[clean_name] = tk_image
                    
                except Exception as e:
                    print(f"Erro ao carregar {filename}: {e}")
    
    def get_logo(self, name):
        """Retorna logo específico ou None se não encontrado"""
        return self.logo_images.get(name.lower())
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.gemini_api_key = config.get('api_key', '')
                    if self.gemini_api_key:
                        self.setup_gemini()
                        self.status_var.set("API configurada - Pronto para usar!")
        except Exception as e:
            self.log(f"Erro ao carregar configurações: {str(e)}")
    
    def save_config(self):
        try:
            config = {'api_key': self.gemini_api_key}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            self.log(f"Erro ao salvar configurações: {str(e)}")
    
    def setup_gemini(self):
        try:
            if not self.gemini_api_key:
                return False
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao configurar Gemini: {str(e)}")
            return False
    
    def configure_api(self):
        api_key = simpledialog.askstring("Configurar API do Gemini", "Cole sua chave API do Gemini:", show='*')
        
        if api_key and api_key.strip():
            self.gemini_api_key = api_key.strip()
            if self.setup_gemini():
                self.save_config()
                self.status_var.set("API configurada com sucesso!")
                messagebox.showinfo("Sucesso", "API do Gemini configurada com sucesso!")
            else:
                self.gemini_api_key = ""
                self.status_var.set("Erro na configuração da API")
    
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Background da janela principal (se disponível)
        bg_image = self.get_logo('background')
        if bg_image:
            bg_label = tk.Label(self.root, image=bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Frame principal com transparência se houver background
        if bg_image:
            main_bg = "#ffffff"  # Fundo branco semi-transparente
            main_frame = tk.Frame(self.root, bg=main_bg)
        else:
            main_frame = tk.Frame(self.root, bg="#f0f0f0")
        
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # =============== CABEÇALHO COM LOGO ===============
        header_frame = tk.Frame(main_frame, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Logo do cabeçalho (lado esquerdo)
        header_logo = self.get_logo('logo_header')
        if header_logo:
            logo_label = tk.Label(header_frame, image=header_logo, bg="#2c3e50")
            logo_label.pack(side="left", padx=20, pady=10)
        
        # Título (centro)
        title_frame = tk.Frame(header_frame, bg="#2c3e50")
        title_frame.pack(side="left", expand=True, fill="both")
        
        title_label = tk.Label(title_frame, text="🤖 Organizador Inteligente de Arquivos", 
                              font=("Segoe UI", 20, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(expand=True, anchor="center")
        
        subtitle_label = tk.Label(title_frame, text="Powered by Google Gemini AI", 
                                 font=("Segoe UI", 10), fg="#bdc3c7", bg="#2c3e50")
        subtitle_label.pack(anchor="center")
        
        # Ícone do Gemini (lado direito)
        gemini_icon = self.get_logo('icon_gemini')
        if gemini_icon:
            icon_label = tk.Label(header_frame, image=gemini_icon, bg="#2c3e50")
            icon_label.pack(side="right", padx=20, pady=10)
        
        # =============== ÁREA PRINCIPAL COM SIDEBAR ===============
        content_frame = tk.Frame(main_frame, bg="#f0f0f0")
        content_frame.pack(fill="both", expand=True)
        
        # Sidebar (opcional)
        sidebar_logo = self.get_logo('logo_sidebar')
        if sidebar_logo:
            sidebar_frame = tk.Frame(content_frame, bg="#ecf0f1", width=150)
            sidebar_frame.pack(side="left", fill="y", padx=(0, 20))
            sidebar_frame.pack_propagate(False)
            
            # Logo na sidebar
            sidebar_logo_label = tk.Label(sidebar_frame, image=sidebar_logo, bg="#ecf0f1")
            sidebar_logo_label.pack(pady=20)
            
            # Informações adicionais na sidebar
            info_label = tk.Label(sidebar_frame, text="Versão 2.0\ncom Suporte\na Logos", 
                                 font=("Segoe UI", 9), bg="#ecf0f1", fg="#7f8c8d",
                                 justify="center")
            info_label.pack(pady=10)
        
        # Área principal de conteúdo
        main_content = tk.Frame(content_frame, bg="#f0f0f0")
        main_content.pack(side="left", fill="both", expand=True)
        
        # =============== BOTÕES DE CONFIGURAÇÃO ===============
        api_frame = tk.Frame(main_content, bg="#f0f0f0")
        api_frame.pack(fill="x", pady=(0, 15))
        
        api_btn = tk.Button(api_frame, text="⚙️ Configurar API do Gemini", 
                           command=self.configure_api, bg="#e74c3c", fg="white",
                           font=("Segoe UI", 11, "bold"), pady=10, relief="flat",
                           cursor="hand2")
        api_btn.pack(side="left", padx=(0, 10))
        
        help_btn = tk.Button(api_frame, text="❓ Como obter API", 
                           command=self.show_api_help, bg="#3498db", fg="white",
                           font=("Segoe UI", 11), pady=10, relief="flat",
                           cursor="hand2")
        help_btn.pack(side="left", padx=(0, 10))
        
        # Botão para gerenciar logos
        logo_btn = tk.Button(api_frame, text="🎨 Gerenciar Logos", 
                           command=self.open_assets_folder, bg="#9b59b6", fg="white",
                           font=("Segoe UI", 11), pady=10, relief="flat",
                           cursor="hand2")
        logo_btn.pack(side="left")
        
        # =============== SELEÇÃO DE PASTAS ===============
        folder_frame = tk.LabelFrame(main_content, text="📁 Seleção de Pastas", 
                                   font=("Segoe UI", 12, "bold"), bg="#f0f0f0", pady=15)
        folder_frame.pack(fill="x", pady=(0, 15))
        
        # Pasta de entrada
        tk.Label(folder_frame, text="Pasta de origem:", bg="#f0f0f0", 
                font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        input_frame = tk.Frame(folder_frame, bg="#f0f0f0")
        input_frame.pack(fill="x", pady=5, padx=15)
        
        input_entry = tk.Entry(input_frame, textvariable=self.input_folder, width=50, 
                              font=("Segoe UI", 10), relief="solid", bd=1)
        input_entry.pack(side="left", fill="x", expand=True, ipady=5)
        
        input_btn = tk.Button(input_frame, text="📂 Selecionar", command=self.select_input_folder, 
                             bg="#27ae60", fg="white", relief="flat", font=("Segoe UI", 9, "bold"),
                             cursor="hand2", padx=15)
        input_btn.pack(side="right", padx=(10, 0))
        
        # Pasta de saída
        tk.Label(folder_frame, text="Pasta de destino:", bg="#f0f0f0", 
                font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        output_frame = tk.Frame(folder_frame, bg="#f0f0f0")
        output_frame.pack(fill="x", pady=5, padx=15)
        
        output_entry = tk.Entry(output_frame, textvariable=self.output_folder, width=50, 
                               font=("Segoe UI", 10), relief="solid", bd=1)
        output_entry.pack(side="left", fill="x", expand=True, ipady=5)
        
        output_btn = tk.Button(output_frame, text="📂 Selecionar", command=self.select_output_folder,
                              bg="#27ae60", fg="white", relief="flat", font=("Segoe UI", 9, "bold"),
                              cursor="hand2", padx=15)
        output_btn.pack(side="right", padx=(10, 0))
        
        # =============== BOTÃO PROCESSAR ===============
        process_frame = tk.Frame(main_content, bg="#f0f0f0")
        process_frame.pack(pady=20)
        
        process_btn = tk.Button(process_frame, text="🚀 PROCESSAR E ORGANIZAR ARQUIVOS", 
                               command=self.start_processing, bg="#2ecc71", fg="white",
                               font=("Segoe UI", 16, "bold"), pady=20, padx=40, relief="flat",
                               cursor="hand2")
        process_btn.pack()
        
        # =============== PROGRESSO ===============
        progress_frame = tk.LabelFrame(main_content, text="📊 Progresso", 
                                     font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
        progress_frame.pack(fill="x", pady=(20, 15))
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.pack(fill="x", padx=15, pady=15)
        
        status_label = tk.Label(progress_frame, textvariable=self.status_var, 
                               wraplength=650, justify="center", bg="#f0f0f0", 
                               font=("Segoe UI", 11), fg="#2c3e50")
        status_label.pack(pady=(0, 15))
        
        # =============== LOG ===============
        log_frame = tk.LabelFrame(main_content, text="📋 Log de Atividades", 
                                font=("Segoe UI", 12, "bold"), bg="#f0f0f0")
        log_frame.pack(fill="both", expand=True)
        
        log_container = tk.Frame(log_frame, bg="#f0f0f0")
        log_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.log_text = tk.Text(log_container, wrap="word", font=("Consolas", 10),
                               bg="#2c3e50", fg="#ecf0f1", insertbackground="white",
                               relief="flat", bd=0)
        scrollbar = tk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # =============== MARCA D'ÁGUA (OPCIONAL) ===============
        watermark = self.get_logo('watermark')
        if watermark:
            watermark_label = tk.Label(self.root, image=watermark, bg="#f0f0f0")
            watermark_label.place(relx=0.95, rely=0.95, anchor="se")
    
    def open_assets_folder(self):
        """Abre a pasta de assets para o usuário gerenciar logos"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.assets_folder)
            elif os.name == 'posix':  # macOS e Linux
                os.system(f'open "{self.assets_folder}"' if os.uname().sysname == 'Darwin' 
                         else f'xdg-open "{self.assets_folder}"')
            
            messagebox.showinfo("Gerenciar Logos", 
                               f"Pasta de assets aberta!\n\n"
                               f"• Adicione seus logos na pasta '{self.assets_folder}'\n"
                               f"• Reinicie o programa para carregar novos logos\n"
                               f"• Consulte o arquivo LEIA-ME.txt para instruções")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta: {str(e)}")
    
    def show_api_help(self):
        help_text = """🔑 Como obter sua chave API do Gemini:

1. Acesse: https://makersuite.google.com/app/apikey
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie a chave gerada
5. Cole aqui no botão "Configurar API"

⚠️ Mantenha sua chave segura e não compartilhe!

🎨 Sobre os Logos:
• Use o botão "Gerenciar Logos" para adicionar suas imagens
• Formatos suportados: PNG, JPG, JPEG, GIF, BMP
• Consulte o arquivo LEIA-ME.txt na pasta assets"""
        
        messagebox.showinfo("Ajuda - API e Logos", help_text)
    
    def select_input_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta com os arquivos")
        if folder:
            self.input_folder.set(folder)
    
    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta de destino")
        if folder:
            self.output_folder.set(folder)
    
    # [RESTO DOS MÉTODOS MANTIDOS IGUAIS - extract_content, analyze_with_gemini, etc.]
    def extract_content(self, file_path):
        """Extrai conteúdo do arquivo"""
        ext = Path(file_path).suffix.lower()
        
        try:
            if ext == '.pdf':
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages[:3]:  # Apenas 3 primeiras páginas
                        text += page.extract_text() + "\n"
                    return text
            
            elif ext in ['.docx', '.doc']:
                doc = Document(file_path)
                text = ""
                for i, para in enumerate(doc.paragraphs[:20]):  # Apenas 20 primeiros parágrafos
                    text += para.text + "\n"
                return text
            
            elif ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.log']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    return file.read()[:3000]  # Apenas 3000 primeiros caracteres
            
            return ""
        except:
            return ""
    
    def analyze_with_gemini(self, content, filename):
        """Análise inteligente com categorização específica"""
        try:
            prompt = f"""
            Analise este documento e classifique em uma das categorias EXATAS abaixo:

            CATEGORIAS DISPONÍVEIS:
            - Oficios_e_Pareceres
            - Relatorios_e_Analises  
            - Processos_Judiciais
            - Ouvidoria_e_Reclamacoes
            - Contratos_e_Acordos
            - Leis_e_Normativas
            - Deliberacoes_e_Resolucoes
            - Documentos_Pessoais
            - Financeiro_e_Pagamentos
            - Correspondencias_Gerais
            - Outros_Documentos

            NOME ORIGINAL: {filename}
            CONTEÚDO: {content[:2000]}

            REGRAS DE CATEGORIZAÇÃO:
            - Ofício, parecer, memo, circular, comunicado = "Oficios_e_Pareceres"
            - E-proc, processo, sentença, decisão, acórdão, despacho = "Processos_Judiciais"
            - Ouvidoria, reclamação, denúncia, manifestação = "Ouvidoria_e_Reclamacoes"
            - Relatório, análise, levantamento, estudo = "Relatorios_e_Analises"
            - Contrato, convênio, acordo, termo = "Contratos_e_Acordos"
            - Lei, decreto, portaria, resolução normativa = "Leis_e_Normativas"
            - Deliberação, ata, resolução administrativa = "Deliberacoes_e_Resolucoes"
            - CPF, RG, certidão, comprovante residência = "Documentos_Pessoais"
            - Fatura, nota fiscal, comprovante pagamento = "Financeiro_e_Pagamentos"
            - E-mail, carta, notificação = "Correspondencias_Gerais"

            REGRAS PARA NOME:
            - SEMPRE incluir o ASSUNTO PRINCIPAL do documento
            - Se mencionar NOME DE PESSOA, incluir no título
            - Se mencionar EMPRESA/ÓRGÃO, incluir no título
            - NUNCA usar apenas datas (ex: "2024-01-15")
            - NUNCA usar nomes genéricos (ex: "Documento", "Arquivo")
            - Ser ESPECÍFICO sobre o conteúdo (ex: "Contrato Fornecimento João Silva", "Relatório Vendas Janeiro 2024")
            - Máximo 70 caracteres

            RESPOSTA FORMATO EXATO:
            CATEGORIA: [uma das categorias acima]
            NOME: [nome específico e descritivo sobre o conteúdo]
            """
            
            response = self.model.generate_content(prompt)
            return self.parse_response(response.text, filename)
            
        except Exception as e:
            self.log(f"⚠️ Erro IA para {filename}: {str(e)}")
            return self.fallback_analysis(filename)
    
    def parse_response(self, response_text, filename):
        """Extrai categoria e nome da resposta"""
        try:
            lines = response_text.strip().split('\n')
            category = "Outros_Documentos"
            name = Path(filename).stem
            
            for line in lines:
                if line.startswith('CATEGORIA:'):
                    category = line.replace('CATEGORIA:', '').strip()
                elif line.startswith('NOME:'):
                    name = line.replace('NOME:', '').strip()
            
            # Valida se o nome não é genérico demais
            name = self.validate_filename(name, filename)
            
            return {'category': category, 'name': name[:70]}
        except:
            return self.fallback_analysis(filename)
    
    def validate_filename(self, proposed_name, original_filename):
        """Valida e melhora nomes genéricos"""
        proposed_lower = proposed_name.lower().strip()
        
        # Lista de nomes genéricos para evitar
        generic_names = [
            'documento', 'arquivo', 'file', 'doc', 'pdf', 'texto',
            'untitled', 'sem titulo', 'novo', 'copia', 'copy'
        ]
        
        # Verifica se é só data (regex para formatos de data)
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # 2024-01-15
            r'^\d{2}/\d{2}/\d{4}$',  # 15/01/2024
            r'^\d{2}-\d{2}-\d{4}$',  # 15-01-2024
            r'^\d{8}$',              # 20240115
        ]
        
        is_generic = any(generic in proposed_lower for generic in generic_names)
        is_only_date = any(re.match(pattern, proposed_lower) for pattern in date_patterns)
        is_too_short = len(proposed_lower.replace(' ', '')) < 3
        
        if is_generic or is_only_date or is_too_short:
            # Tenta extrair algo melhor do nome original
            original_clean = Path(original_filename).stem.replace('_', ' ').replace('-', ' ')
            if len(original_clean) > 5:
                return f"Documento - {original_clean}"
            else:
                return f"Documento - {original_filename}"
        
        return proposed_name
    
    def fallback_analysis(self, filename):
        """Análise básica sem IA"""
        name = Path(filename).stem.replace('_', ' ').replace('-', ' ')
        ext = Path(filename).suffix.lower()
        
        # Categorização por palavras-chave
        name_lower = name.lower()
        content_lower = filename.lower()
        
        if any(word in content_lower for word in ['oficio', 'parecer', 'requer', 'solicit', 'memo', 'circular']):
            category = "Oficios_e_Pareceres"
        elif any(word in content_lower for word in ['eproc', 'processo', 'sentenca', 'decisao', 'judicial', 'acordao', 'despacho']):
            category = "Processos_Judiciais"
        elif any(word in content_lower for word in ['ouvidoria', 'reclamacao', 'denuncia', 'manifestacao']):
            category = "Ouvidoria_e_Reclamacoes"
        elif any(word in content_lower for word in ['relatorio', 'analise', 'levantamento', 'estudo']):
            category = "Relatorios_e_Analises"
        elif any(word in content_lower for word in ['contrato', 'acordo', 'convenio', 'termo']):
            category = "Contratos_e_Acordos"
        elif any(word in content_lower for word in ['lei', 'decreto', 'portaria', 'norma', 'resolucao']):
            category = "Leis_e_Normativas"
        elif any(word in content_lower for word in ['deliberacao', 'ata', 'resolucao']):
            category = "Deliberacoes_e_Resolucoes"
        elif any(word in content_lower for word in ['cpf', 'rg', 'certidao', 'identidade', 'comprovante']):
            category = "Documentos_Pessoais"
        elif any(word in content_lower for word in ['fatura', 'nota', 'pagamento', 'financeiro', 'orcamento']):
            category = "Financeiro_e_Pagamentos"
        elif any(word in content_lower for word in ['email', 'carta', 'notificacao', 'comunicacao']):
            category = "Correspondencias_Gerais"
        else:
            category = "Outros_Documentos"
        
        # Melhora o nome baseado na categoria
        improved_name = self.improve_name_by_category(name, category, filename)
        
        return {'category': category, 'name': improved_name}
    
    def improve_name_by_category(self, name, category, filename):
        """Melhora o nome baseado na categoria identificada"""
        # Se o nome é muito genérico, melhora baseado na categoria
        if len(name.strip()) < 5 or name.lower() in ['documento', 'arquivo', 'file']:
            category_prefixes = {
                "Oficios_e_Pareceres": "Ofício",
                "Processos_Judiciais": "Processo",
                "Ouvidoria_e_Reclamacoes": "Ouvidoria",
                "Relatorios_e_Analises": "Relatório",
                "Contratos_e_Acordos": "Contrato",
                "Leis_e_Normativas": "Normativa",
                "Deliberacoes_e_Resolucoes": "Deliberação",
                "Documentos_Pessoais": "Documento Pessoal",
                "Financeiro_e_Pagamentos": "Financeiro",
                "Correspondencias_Gerais": "Correspondência",
                "Outros_Documentos": "Documento"
            }
            prefix = category_prefixes.get(category, "Documento")
            
            # Tenta extrair data do nome original
            date_match = re.search(r'(\d{4}[-_]\d{2}[-_]\d{2}|\d{2}[-_]\d{2}[-_]\d{4})', filename)
            if date_match:
                return f"{prefix} - {date_match.group(1)}"
            else:
                return f"{prefix} - {Path(filename).stem}"
        
        # Valida o nome proposto
        return self.validate_filename(name, filename)
    
    def sanitize_filename(self, filename):
        """Limpa nome do arquivo"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, ' ')
        
        # Remove espaços extras e limita tamanho
        filename = ' '.join(filename.split())  # Remove espaços duplos
        return filename.strip()[:70] or "Documento"
    
    def process_file(self, file_path, output_base):
        """Processa arquivo único"""
        try:
            filename = os.path.basename(file_path)
            self.log(f"🔍 {filename}")
            
            # Análise
            content = self.extract_content(file_path)
            if content and len(content.strip()) > 50:
                result = self.analyze_with_gemini(content, filename)
            else:
                result = self.fallback_analysis(filename)
            
            # Cria pasta
            category_folder = os.path.join(output_base, result['category'])
            os.makedirs(category_folder, exist_ok=True)
            
            # Nome final
            new_name = self.sanitize_filename(result['name'])
            extension = Path(file_path).suffix
            final_name = f"{new_name}{extension}"
            
            # Evita duplicatas
            counter = 1
            final_path = os.path.join(category_folder, final_name)
            while os.path.exists(final_path):
                final_name = f"{new_name} ({counter}){extension}"
                final_path = os.path.join(category_folder, final_name)
                counter += 1
            
            # Copia arquivo
            shutil.copy2(file_path, final_path)
            
            self.log(f"   → {result['category']}/{final_name}")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro: {filename} - {str(e)}")
            return False
    
    def get_files(self, folder_path):
        """Lista arquivos suportados"""
        extensions = ['.pdf', '.docx', '.doc', '.txt', '.md', '.py', '.js', '.html', 
                     '.css', '.json', '.xml', '.csv', '.xlsx', '.xls', '.jpg', '.png']
        
        files = []
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                if Path(filename).suffix.lower() in extensions:
                    files.append(os.path.join(root, filename))
        return files
    
    def process_files(self):
        """Processamento principal"""
        try:
            if not self.model:
                messagebox.showerror("Erro", "Configure a API do Gemini!")
                return
            
            input_path = self.input_folder.get()
            output_path = self.output_folder.get()
            
            if not input_path or not output_path:
                messagebox.showerror("Erro", "Selecione as pastas!")
                return
            
            os.makedirs(output_path, exist_ok=True)
            files = self.get_files(input_path)
            
            if not files:
                messagebox.showinfo("Info", "Nenhum arquivo encontrado")
                return
            
            self.log(f"🚀 Processando {len(files)} arquivos...")
            
            processed = 0
            start_time = datetime.now()
            
            for i, file_path in enumerate(files):
                if self.process_file(file_path, output_path):
                    processed += 1
                
                progress = ((i + 1) / len(files)) * 100
                self.progress_var.set(progress)
                self.status_var.set(f"Processando {i + 1}/{len(files)}")
                self.root.update()
            
            duration = datetime.now() - start_time
            self.progress_var.set(100)
            self.status_var.set(f"✅ {processed}/{len(files)} arquivos organizados")
            
            self.log(f"🎉 Concluído! {processed}/{len(files)} em {duration.total_seconds():.1f}s")
            
            messagebox.showinfo("Sucesso!", f"✅ {processed}/{len(files)} arquivos organizados!")
            
        except Exception as e:
            self.log(f"❌ Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro: {str(e)}")
    
    def start_processing(self):
        """Inicia processamento"""
        if not self.model:
            messagebox.showerror("Erro", "Configure a API primeiro!")
            return
        
        if not self.input_folder.get() or not self.output_folder.get():
            messagebox.showerror("Erro", "Selecione as pastas!")
            return
        
        if messagebox.askyesno("Confirmar", "Iniciar processamento?"):
            self.log_text.delete(1.0, tk.END)
            self.progress_var.set(0)
            thread = threading.Thread(target=self.process_files)
            thread.daemon = True
            thread.start()
    
    def log(self, message):
        """Log simplificado"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        import google.generativeai
        import docx
        import PyPDF2
        from PIL import Image, ImageTk
    except ImportError as e:
        missing_libs = []
        try:
            import google.generativeai
        except ImportError:
            missing_libs.append("google-generativeai")
        
        try:
            import docx
        except ImportError:
            missing_libs.append("python-docx")
        
        try:
            import PyPDF2
        except ImportError:
            missing_libs.append("PyPDF2")
        
        try:
            from PIL import Image, ImageTk
        except ImportError:
            missing_libs.append("Pillow")
        
        print(f"❌ Instale as bibliotecas necessárias:")
        print(f"pip install {' '.join(missing_libs)}")
        exit(1)
    
    app = FileOrganizer()
    app.run()
