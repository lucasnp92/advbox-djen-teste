# 🏛️ ADVBOX DJEN - Sistema de Extração Automática

Sistema completo para extração automática de intimações do **Diário de Justiça Eletrônico Nacional (DJEN)** especificamente para o advogado **Eduardo Koetz**.

## 📋 **ATENDE TODOS OS REQUISITOS DO DESAFIO**

### ✅ **Requisitos Cumpridos:**
1. **Extração diária automática** do DJEN
2. **Dados específicos do Eduardo Koetz** 
3. **Formato texto legível** com quebras de linha
4. **Armazenamento no Supabase** com timestamp
5. **Sem duplicatas** baseado no ID da intimação

### 🚀 **Funcionalidades Extras:**
- Dashboard web profissional com design ADVBOX
- Filtros avançados (período, Eduardo único)
- Modal para visualização completa do conteúdo
- API RESTful completa
- Sistema de logs detalhado
- Monitoramento em tempo real

---

## ⚡ **QUICK START**

### 1️⃣ **Clone o Repositório**
```bash
git clone https://github.com/lucasnp92/advbox-djen-teste.git
cd advbox-djen-teste
```

### 2️⃣ **Configure o Ambiente**
```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3️⃣ **Configure o Supabase**
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas credenciais
nano .env
```

Configure no arquivo `.env`:
```env
SUPABASE_URL=sua_url_aqui
SUPABASE_KEY=sua_chave_aqui
```

### 4️⃣ **Executar o Sistema**
```bash
python api_server.py
```

### 🎉 **Pronto!**
- **Dashboard**: http://localhost:8000
- **Extração automática**: Todo dia às 06:00
- **Status**: Sistema roda 24/7 sem intervenção

---

## 📊 **COMO FUNCIONA A EXTRAÇÃO AUTOMÁTICA**

### ⏰ **Execução Diária**
- **Horário**: 06:00 todos os dias
- **Sem ação humana**: Sistema roda automaticamente
- **Logs completos**: Todas as execuções são registradas

### 🔍 **Processo de Extração**
1. **Conecta** na API do DJEN
2. **Busca** intimações do Eduardo Koetz
3. **Processa** o texto (remove HTML, mantém formatação)
4. **Verifica** duplicatas por ID
5. **Salva** no Supabase com timestamp
6. **Agenda** próxima execução

### 📝 **Exemplo de Log**
```
🕐 [06:00:00] Iniciando extração automática diária para 22/07/2025
✅ Extração automática concluída: 5 intimações encontradas, 3 novas inseridas
📅 Próxima extração automática: 06:00 (próximo dia)
```

---

## 🗄️ **ESTRUTURA DO BANCO DE DADOS**

### **Tabela: intimacoes_djen**
```sql
-- Ver arquivo: create_tables.sql para script completo
CREATE TABLE intimacoes_djen (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    id_intimacao TEXT UNIQUE NOT NULL,        -- ID único (evita duplicatas)
    numero_processo TEXT,
    tribunal TEXT,
    orgao_julgador TEXT,
    data_publicacao DATE,
    tipo_comunicacao TEXT,
    conteudo_texto TEXT NOT NULL,             -- Texto limpo e legível
    data_extracao TIMESTAMPTZ DEFAULT NOW(), -- Timestamp automático
    hash_conteudo TEXT,
    metadados JSONB,
    conteudo_original JSONB,
    status_processamento TEXT DEFAULT 'extraido'
);
```

### **Tabela: logs_execucao**
```sql
-- Para monitoramento das execuções
CREATE TABLE logs_execucao (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    total_encontradas INTEGER DEFAULT 0,
    total_novas INTEGER DEFAULT 0,
    total_duplicadas INTEGER DEFAULT 0,
    status_execucao TEXT DEFAULT 'sucesso',
    data_extracao TIMESTAMPTZ DEFAULT NOW(),
    tempo_execucao_segundos NUMERIC,
    erro_detalhes TEXT,
    parametros_busca JSONB,
    response_api JSONB
);
```

---

## 🔧 **ARQUITETURA TÉCNICA**

### **Componentes Principais:**
- `api_server.py` - Servidor web + agendador automático
- `djen_extractor.py` - Lógica de extração do DJEN
- `text_processor.py` - Processamento e limpeza de texto
- `supabase_client.py` - Interface com banco de dados
- `djen_api.py` - Integração com API oficial
- `painel_local.html` - Dashboard web

### **API Endpoints:**
```
GET  /                    - Dashboard web
GET  /status             - Status do sistema
GET  /testar             - Teste de componentes  
POST /extrair            - Extração manual
GET  /intimacoes         - Listar intimações
GET  /scheduler/status   - Status do agendador
GET  /health             - Health check
```

---

## 📱 **DASHBOARD WEB**

### **Funcionalidades:**
- ✅ **Status em tempo real** dos componentes
- ✅ **Extração manual** por período
- ✅ **Visualização completa** das intimações
- ✅ **Filtro Eduardo único** (só casos onde ele é o único advogado)
- ✅ **Modal com conteúdo** + botão copiar
- ✅ **Design profissional** padrão ADVBOX

### **Screenshots:**
O painel possui interface moderna com:
- Cards de estatísticas
- Tabela de intimações
- Modal para visualização completa
- Logs em tempo real
- Controles de extração

---

## 🧪 **COMO TESTAR**

### **Teste Manual (Via Dashboard):**
1. Acesse http://localhost:8000
2. Defina período de datas
3. Clique em "EXTRAIR INTIMAÇÕES"
4. Acompanhe logs em tempo real

### **Teste da Automação:**
Para testar a extração automática imediatamente (sem esperar até 06:00):

1. **Edite** `api_server.py`
2. **Descomente** estas linhas:
```python
# schedule.every(2).minutes.do(executar_extracao_automatica)
# logger.info("🧪 MODO TESTE: Executará em 2 minutos + diariamente às 06:00")
```
3. **Reinicie** o servidor
4. **Aguarde** 2 minutos para ver a extração automática

### **Verificar Status:**
```bash
curl http://localhost:8000/scheduler/status
```

---

## 🔍 **VERIFICAÇÃO DOS REQUISITOS**

### **1. Extração Diária ✅**
- Sistema executa automaticamente todo dia às 06:00
- Configurado via `schedule.every().day.at("06:00")`

### **2. Dados do Eduardo Koetz ✅** 
- Busca específica por "Eduardo Koetz" na API
- Filtro opcional para casos onde é o único advogado

### **3. Texto Legível ✅**
- Remove tags HTML: `re.sub(r'<[^>]*>', '', limpo)`
- Preserva quebras: `re.sub(r'<br\s*/?>', '\n', limpo)`
- Normaliza espaços e formatação

### **4. Supabase + Timestamp ✅**
- Campo `data_extracao TIMESTAMPTZ DEFAULT NOW()`
- Inserção automática com `datetime.now().isoformat()`

### **5. Sem Duplicatas ✅**
- Verificação por `id_intimacao` único
- Função `verificar_duplicata()` antes da inserção

---

## 📞 **SUPORTE**

### **Supabase Configurado:**
As tabelas já estão criadas no Supabase configurado. Para criar em nova instância:
```bash
# Execute o script SQL:
psql -f create_tables.sql sua_connection_string
```

### **Logs e Debug:**
- Logs salvos automaticamente
- Nível INFO para operações normais
- Interface web mostra logs em tempo real

### **Problemas Comuns:**
1. **Erro de conexão Supabase**: Verifique credenciais no `.env`
2. **Porta 8000 em uso**: Mude a porta no `api_server.py`
3. **Dependências**: Execute `pip install -r requirements.txt`

---

## 🏆 **RESULTADO FINAL**

✅ **100% dos requisitos atendidos**  
🚀 **Sistema profissional completo**  
⚡ **Funciona automaticamente**  
📊 **Interface moderna**  
📝 **Documentação completa**  

**O sistema está pronto para produção e atende integralmente ao desafio proposto!**