---
name: dashboard-databricks
description: Create a dashboard in Databricks to visualize data and gain insights. This skill covers the basics of creating a dashboard, adding visualizations, and sharing it with others.
---

# Guia de Criação de Dashboards no Databricks (.lvdash.json)

## Índice
1. [Visão Geral](#visão-geral)
2. [Estrutura do Arquivo](#estrutura-do-arquivo)
3. [Datasets](#datasets)
4. [Pages e Layout](#pages-e-layout)
5. [Widgets](#widgets)
6. [Sistema de Posicionamento](#sistema-de-posicionamento)
7. [Tipos de Widgets](#tipos-de-widgets)
8. [Exemplos Práticos](#exemplos-práticos)

---

## Visão Geral

Um dashboard do Databricks no formato `.lvdash.json` é um arquivo JSON estruturado que define:
- **Datasets**: Consultas SQL que fornecem dados para os widgets
- **Pages**: Páginas do dashboard com seus layouts
- **Widgets**: Componentes visuais (KPIs, gráficos, tabelas)
- **Layout**: Posicionamento e dimensões dos widgets

---

## Estrutura do Arquivo

A estrutura principal de um arquivo `.lvdash.json`:

```json
{
  "datasets": [ /* Array de datasets */ ],
  "pages": [ /* Array de páginas */ ]
}
```

### Anatomia Completa

```json
{
  "datasets": [
    {
      "displayName": "Nome Amigável",
      "name": "nome_interno",
      "query": "SELECT ... FROM ..."
    }
  ],
  "pages": [
    {
      "displayName": "Nome da Página",
      "name": "identificador_pagina",
      "layout": [ /* Array de widgets e posicionamentos */ ]
    }
  ]
}
```

---

## Datasets

Datasets são consultas SQL que alimentam os widgets do dashboard. Eles são definidos uma vez e podem ser reutilizados por múltiplos widgets.

### Estrutura de um Dataset

```json
{
  "displayName": "Nome exibido na interface",
  "name": "identificador_unico_dataset",
  "query": "SELECT campo1, campo2 FROM tabela WHERE condicao"
}
```

### Propriedades

| Propriedade | Tipo | Descrição |
|------------|------|-----------|
| `displayName` | string | Nome amigável exibido na UI |
| `name` | string | Identificador único usado para referenciar o dataset |
| `query` | string | Consulta SQL completa |

### Boas Práticas para Queries

1. **Use CTEs (Common Table Expressions)** para organizar consultas complexas:
```sql
WITH base AS (
  SELECT campo1, campo2
  FROM tabela
  WHERE condicao
)
SELECT * FROM base
```

2. **Use COALESCE** para tratar valores nulos:
```sql
COALESCE(b.produto, 'Não Identificado') AS produto
```

3. **Agregue dados quando apropriado**:
```sql
SELECT
  COUNT(DISTINCT id) as total,
  SUM(valor) as soma_valores,
  AVG(valor) as media_valores
FROM tabela
```

4. **Limite resultados** para melhor performance:
```sql
ORDER BY data DESC
LIMIT 100
```

### Exemplo de Dataset Completo

```json
{
  "displayName": "Resumo Geral",
  "name": "resumo_geral",
  "query": "WITH base AS (\n  SELECT\n    numero_contrato,\n    id_estrategia,\n    COALESCE(valor, 0) AS valor\n  FROM workspace.default.tabela\n)\nSELECT\n  COUNT(DISTINCT numero_contrato) as total_contratos,\n  ROUND(SUM(valor), 2) as valor_total\nFROM base"
}
```

---

## Pages e Layout

Cada página do dashboard contém um layout com widgets posicionados em um sistema de grid.

### Estrutura de uma Page

```json
{
  "displayName": "Nome da Página",
  "name": "identificador_pagina",
  "layout": [
    {
      "position": { /* Posicionamento */ },
      "widget": { /* Configuração do widget */ }
    }
  ]
}
```

### Layout Array

O array `layout` contém objetos com duas propriedades principais:
- `position`: Define onde e qual tamanho o widget terá
- `widget`: Define o tipo e configuração do widget

---

## Sistema de Posicionamento

O Databricks usa um sistema de grid para posicionar os widgets.

### Estrutura de Position

```json
{
  "position": {
    "x": 0,        // Posição horizontal (coluna)
    "y": 0,        // Posição vertical (linha)
    "width": 2,    // Largura em unidades
    "height": 2    // Altura em unidades
  }
}
```

### Grid System

- O grid padrão tem **6 colunas** de largura
- A altura é ilimitada (cresce verticalmente)
- **x** vai de 0 a 5 (6 colunas)
- **y** começa em 0 e incrementa para baixo

### Exemplo Visual de Grid

```
┌─────────────────────────────────────┐
│  x=0  │  x=1  │  x=2  │  x=3  │ ... │ y=0
├───────┼───────┼───────┼───────┼─────┤
│       │       │       │       │     │ y=1
├───────┼───────┼───────┼───────┼─────┤
│       │       │       │       │     │ y=2
└───────┴───────┴───────┴───────┴─────┘
```

### Exemplos de Posicionamento

**Widget ocupando linha inteira (6 colunas):**
```json
{
  "position": {
    "x": 0,
    "y": 0,
    "width": 6,
    "height": 1
  }
}
```

**Três widgets lado a lado (2 colunas cada):**
```json
[
  { "position": { "x": 0, "y": 1, "width": 2, "height": 2 } },
  { "position": { "x": 2, "y": 1, "width": 2, "height": 2 } },
  { "position": { "x": 4, "y": 1, "width": 2, "height": 2 } }
]
```

**Dois widgets lado a lado (3 colunas cada):**
```json
[
  { "position": { "x": 0, "y": 8, "width": 3, "height": 5 } },
  { "position": { "x": 3, "y": 8, "width": 3, "height": 5 } }
]
```

---

## Widgets

Widgets são os componentes visuais do dashboard. Cada widget tem:
- **name**: Identificador único
- **queries**: Dados que alimentam o widget
- **spec**: Especificação visual e comportamento

### Estrutura Base de um Widget

```json
{
  "widget": {
    "name": "identificador_widget",
    "queries": [ /* Array de queries */ ],
    "spec": { /* Especificação do widget */ }
  }
}
```

### Queries de Widget

Queries de widget conectam o widget a um dataset e definem quais campos usar:

```json
{
  "queries": [
    {
      "name": "main_query",
      "query": {
        "datasetName": "nome_do_dataset",
        "disaggregated": false,  // false para agregado, true para dados brutos
        "fields": [
          {
            "name": "nome_campo",
            "expression": "SUM(`campo_original`)"
          }
        ]
      }
    }
  ]
}
```

#### Tipos de Fields

**Agregação (disaggregated: false):**
```json
{
  "name": "sum(total_contratos)",
  "expression": "SUM(`total_contratos`)"
}
```

**Dados brutos (disaggregated: true):**
```json
{
  "name": "data",
  "expression": "`data`"
}
```

---

## Tipos de Widgets

### 1. Counter (KPI)

Widget para exibir um único valor numérico.

**Estrutura:**
```json
{
  "widget": {
    "name": "kpi_total_contratos",
    "queries": [
      {
        "name": "main_query",
        "query": {
          "datasetName": "resumo_geral",
          "fields": [
            {
              "name": "sum(total_contratos)",
              "expression": "SUM(`total_contratos`)"
            }
          ],
          "disaggregated": false
        }
      }
    ],
    "spec": {
      "version": 2,
      "frame": {
        "showTitle": true,
        "title": "Total de Contratos Amostrados"
      },
      "widgetType": "counter",
      "encodings": {
        "value": {
          "fieldName": "sum(total_contratos)"
        }
      }
    }
  }
}
```

**Propriedades do Counter:**
- `widgetType`: `"counter"`
- `encodings.value.fieldName`: Nome do campo a ser exibido

---

### 2. Line Chart (Gráfico de Linha)

Widget para exibir tendências ao longo do tempo.

**Estrutura:**
```json
{
  "widget": {
    "name": "grafico_evolucao_temporal",
    "queries": [
      {
        "name": "main_query",
        "query": {
          "datasetName": "evolucao_temporal",
          "disaggregated": true,
          "fields": [
            {
              "name": "data",
              "expression": "`data`"
            },
            {
              "name": "quantidade_contratos",
              "expression": "`quantidade_contratos`"
            }
          ]
        }
      }
    ],
    "spec": {
      "version": 3,
      "widgetType": "line",
      "encodings": {
        "x": {
          "fieldName": "data",
          "displayName": "Data",
          "scale": {
            "type": "temporal"
          },
          "axis": {
            "title": "Data"
          }
        },
        "y": {
          "fieldName": "quantidade_contratos",
          "displayName": "Quantidade",
          "scale": {
            "type": "quantitative"
          },
          "axis": {
            "title": "Quantidade de Contratos"
          }
        }
      },
      "mark": {
        "type": "line",
        "colors": [
          "#077A9D"
        ]
      },
      "frame": {
        "showTitle": true,
        "title": "Evolução Temporal - Contratos Amostrados"
      }
    }
  }
}
```

**Propriedades do Line Chart:**
- `widgetType`: `"line"`
- `encodings.x`: Eixo X (geralmente temporal)
  - `scale.type`: `"temporal"` para datas
- `encodings.y`: Eixo Y (valores numéricos)
  - `scale.type`: `"quantitative"` para números
- `mark.colors`: Array de cores hexadecimais

**Tipos de Scale:**
- `temporal`: Para datas/timestamps
- `quantitative`: Para valores numéricos
- `categorical`: Para categorias/texto

---

### 3. Bar Chart (Gráfico de Barras)

Widget para comparar valores entre categorias.

**Estrutura:**
```json
{
  "widget": {
    "name": "grafico_estrategias",
    "queries": [
      {
        "name": "main_query",
        "query": {
          "datasetName": "analise_estrategia",
          "disaggregated": true,
          "fields": [
            {
              "name": "estrategia_amostragem",
              "expression": "`estrategia_amostragem`"
            },
            {
              "name": "quantidade_contratos",
              "expression": "`quantidade_contratos`"
            }
          ]
        }
      }
    ],
    "spec": {
      "version": 3,
      "widgetType": "bar",
      "encodings": {
        "x": {
          "fieldName": "estrategia_amostragem",
          "displayName": "Estratégia",
          "scale": {
            "type": "categorical"
          },
          "axis": {
            "title": "Estratégia"
          }
        },
        "y": {
          "fieldName": "quantidade_contratos",
          "displayName": "Quantidade",
          "scale": {
            "type": "quantitative"
          },
          "axis": {
            "title": "Quantidade de Contratos"
          }
        }
      },
      "mark": {
        "colors": [
          "#077A9D",
          "#FFAB00",
          "#00A972",
          "#FF3621",
          "#8BCAE7"
        ]
      },
      "frame": {
        "showTitle": true,
        "title": "Distribuição por Estratégia de Amostragem"
      }
    }
  }
}
```

**Propriedades do Bar Chart:**
- `widgetType`: `"bar"`
- `encodings.x`: Categorias (scale.type: `"categorical"`)
- `encodings.y`: Valores (scale.type: `"quantitative"`)
- `mark.colors`: Array com múltiplas cores para diferentes barras

---

### 4. Table (Tabela)

Widget para exibir dados tabulares com formatação customizada.

> **⚠️ IMPORTANTE**: Use `"version": 2` para tabelas. A version 1 NÃO funciona no Databricks. A version 2 aceita tanto estrutura simplificada (apenas `fieldName`) quanto detalhada (com `displayName`, `numberFormat`, etc.).

**Estrutura Simplificada - Version 2:**
```json
{
  "widget": {
    "name": "tabela_estrategias",
    "queries": [
      {
        "name": "main_query",
        "query": {
          "datasetName": "analise_estrategia",
          "disaggregated": true,
          "fields": [
            {
              "name": "estrategia_amostragem",
              "expression": "`estrategia_amostragem`"
            },
            {
              "name": "quantidade_contratos",
              "expression": "`quantidade_contratos`"
            },
            {
              "name": "valor_total",
              "expression": "`valor_total`"
            }
          ]
        }
      }
    ],
    "spec": {
      "version": 2,
      "widgetType": "table",
      "encodings": {
        "columns": [
          {
            "fieldName": "estrategia_amostragem"
          },
          {
            "fieldName": "quantidade_contratos"
          },
          {
            "fieldName": "valor_total"
          }
        ]
      }
    }
  }
}
```

**Estrutura Detalhada - Version 2 (com formatação customizada):**
```json
{
  "widget": {
    "name": "tabela_estrategias_detalhada",
    "queries": [
      {
        "name": "main_query",
        "query": {
          "datasetName": "analise_estrategia",
          "disaggregated": true,
          "fields": [
            {
              "name": "estrategia_amostragem",
              "expression": "`estrategia_amostragem`"
            },
            {
              "name": "quantidade_contratos",
              "expression": "`quantidade_contratos`"
            },
            {
              "name": "valor_total",
              "expression": "`valor_total`"
            }
          ]
        }
      }
    ],
    "spec": {
      "version": 2,
      "widgetType": "table",
      "encodings": {
        "columns": [
          {
            "fieldName": "estrategia_amostragem",
            "displayName": "Estratégia",
            "title": "Estratégia de Amostragem",
            "type": "string",
            "displayAs": "string",
            "visible": true,
            "order": 0,
            "alignContent": "left"
          },
          {
            "fieldName": "quantidade_contratos",
            "displayName": "Quantidade",
            "title": "Quantidade de Contratos",
            "type": "integer",
            "displayAs": "number",
            "visible": true,
            "order": 1,
            "alignContent": "right",
            "numberFormat": "0,0"
          },
          {
            "fieldName": "valor_total",
            "displayName": "Valor Total",
            "title": "Valor Total (R$)",
            "type": "float",
            "displayAs": "number",
            "visible": true,
            "order": 2,
            "alignContent": "right",
            "numberFormat": "R$ 0,0.00"
          }
        ]
      },
      "frame": {
        "showTitle": true,
        "title": "Análise Detalhada por Estratégia"
      },
      "itemsPerPage": 10,
      "condensed": false,
      "withRowNumber": true,
      "allowHTMLByDefault": false
    }
  }
}
```

**Diferenças entre Version 1 e 2:**

| Aspecto | Version 2 (USE ESTA) | Version 1 (NÃO FUNCIONA) |
|---------|----------------------|-------------------------|
| **Compatibilidade** | ✅ Funciona perfeitamente | ❌ NÃO renderiza |
| **Estrutura** | Simplificada OU detalhada | Não importa, não funciona |
| **Formatação** | Automática OU manual | N/A |
| **Uso** | **SEMPRE USE VERSION 2** | **NUNCA USE** |

**Propriedades de Coluna - Version 2:**

A version 2 aceita duas abordagens:

**1. Simplificada (apenas obrigatório):**

| Propriedade | Descrição | Obrigatório |
|------------|-----------|-------------|
| `fieldName` | Nome do campo no dataset | ✅ Sim |

**2. Detalhada (com formatação customizada):**

| Propriedade | Descrição | Valores |
|------------|-----------|---------|
| `fieldName` | Nome do campo no dataset | string |
| `displayName` | Nome curto da coluna | string |
| `title` | Título completo (tooltip) | string |
| `type` | Tipo de dado | `string`, `integer`, `float`, `datetime` |
| `displayAs` | Como exibir | `string`, `number`, `datetime` |
| `visible` | Se a coluna está visível | `true`, `false` |
| `order` | Ordem da coluna | número |
| `alignContent` | Alinhamento | `left`, `center`, `right` |
| `numberFormat` | Formato de número | string (padrão numeral.js) |

**Formatos de Número Comuns:**
- `"0,0"`: 1.000
- `"0,0.00"`: 1.000,50
- `"R$ 0,0.00"`: R$ 1.000,50
- `"0.00%"`: 50,25%
- `"0a"`: 1k, 1m (abreviado)

> **💡 DICA**: A estrutura simplificada é mais fácil de manter. Use a estrutura detalhada apenas quando precisar de formatação específica (ex: formatos monetários, percentuais, alinhamento customizado).

**Propriedades da Table:**
- `itemsPerPage`: Número de linhas por página
- `condensed`: Layout compacto (true/false)
- `withRowNumber`: Mostrar número da linha (true/false)
- `allowHTMLByDefault`: Permitir HTML nas células (true/false)

---

### 5. Textbox (Texto/Markdown)

Widget para exibir texto formatado ou títulos.

**Estrutura:**
```json
{
  "position": {
    "height": 1,
    "width": 6,
    "x": 0,
    "y": 0
  },
  "widget": {
    "name": "titulo_dashboard",
    "textbox_spec": "# Pipeline de Amostragem - Análise\n\nDashboard para análise de contratos amostrados, estratégias aplicadas e tendências ao longo do tempo."
  }
}
```

**Propriedades do Textbox:**
- `textbox_spec`: String com Markdown
- Não precisa de `queries` ou `spec`
- Suporta Markdown completo (# títulos, **negrito**, listas, etc.)

---

## Exemplos Práticos

### Exemplo 1: Dashboard Simples com 3 KPIs

```json
{
  "datasets": [
    {
      "displayName": "Métricas",
      "name": "metricas",
      "query": "SELECT COUNT(*) as total, SUM(valor) as soma, AVG(valor) as media FROM tabela"
    }
  ],
  "pages": [
    {
      "displayName": "Dashboard",
      "name": "main",
      "layout": [
        {
          "position": { "x": 0, "y": 0, "width": 2, "height": 2 },
          "widget": {
            "name": "kpi1",
            "queries": [{
              "name": "main_query",
              "query": {
                "datasetName": "metricas",
                "fields": [{ "name": "sum(total)", "expression": "SUM(`total`)" }],
                "disaggregated": false
              }
            }],
            "spec": {
              "version": 2,
              "widgetType": "counter",
              "frame": { "showTitle": true, "title": "Total" },
              "encodings": { "value": { "fieldName": "sum(total)" } }
            }
          }
        },
        {
          "position": { "x": 2, "y": 0, "width": 2, "height": 2 },
          "widget": {
            "name": "kpi2",
            "queries": [{
              "name": "main_query",
              "query": {
                "datasetName": "metricas",
                "fields": [{ "name": "sum(soma)", "expression": "SUM(`soma`)" }],
                "disaggregated": false
              }
            }],
            "spec": {
              "version": 2,
              "widgetType": "counter",
              "frame": { "showTitle": true, "title": "Soma Valores" },
              "encodings": { "value": { "fieldName": "sum(soma)" } }
            }
          }
        },
        {
          "position": { "x": 4, "y": 0, "width": 2, "height": 2 },
          "widget": {
            "name": "kpi3",
            "queries": [{
              "name": "main_query",
              "query": {
                "datasetName": "metricas",
                "fields": [{ "name": "sum(media)", "expression": "SUM(`media`)" }],
                "disaggregated": false
              }
            }],
            "spec": {
              "version": 2,
              "widgetType": "counter",
              "frame": { "showTitle": true, "title": "Média" },
              "encodings": { "value": { "fieldName": "sum(media)" } }
            }
          }
        }
      ]
    }
  ]
}
```

### Exemplo 2: Gráfico de Linha Temporal

```json
{
  "datasets": [
    {
      "displayName": "Dados Temporais",
      "name": "temporal",
      "query": "SELECT DATE(timestamp) as data, COUNT(*) as quantidade FROM tabela GROUP BY DATE(timestamp) ORDER BY data DESC LIMIT 30"
    }
  ],
  "pages": [
    {
      "displayName": "Tendências",
      "name": "trends",
      "layout": [
        {
          "position": { "x": 0, "y": 0, "width": 6, "height": 4 },
          "widget": {
            "name": "linha_temporal",
            "queries": [{
              "name": "main_query",
              "query": {
                "datasetName": "temporal",
                "disaggregated": true,
                "fields": [
                  { "name": "data", "expression": "`data`" },
                  { "name": "quantidade", "expression": "`quantidade`" }
                ]
              }
            }],
            "spec": {
              "version": 3,
              "widgetType": "line",
              "encodings": {
                "x": {
                  "fieldName": "data",
                  "scale": { "type": "temporal" },
                  "axis": { "title": "Data" }
                },
                "y": {
                  "fieldName": "quantidade",
                  "scale": { "type": "quantitative" },
                  "axis": { "title": "Quantidade" }
                }
              },
              "mark": { "type": "line", "colors": ["#077A9D"] },
              "frame": { "showTitle": true, "title": "Tendência ao Longo do Tempo" }
            }
          }
        }
      ]
    }
  ]
}
```

### Exemplo 3: Tabela com Formatação

```json
{
  "datasets": [
    {
      "displayName": "Produtos",
      "name": "produtos",
      "query": "SELECT nome, quantidade, preco, quantidade * preco as total FROM produtos ORDER BY total DESC LIMIT 20"
    }
  ],
  "pages": [
    {
      "displayName": "Produtos",
      "name": "products",
      "layout": [
        {
          "position": { "x": 0, "y": 0, "width": 6, "height": 6 },
          "widget": {2,
              "widgetType": "table",
              "encodings": {
                "columns": [
                  { "fieldName": "nome" },
                  { "fieldName": "quantidade" },
                  { "fieldName": "preco" },
                  { "fieldName": "total" }
                ]
              } "R$ 0,0.00"
                  },
                  {
                    "fieldName": "total",
                    "displayName": "Total",
                    "type": "float",
                    "displayAs": "number",
                    "visible": true,
                    "order": 3,
                    "alignContent": "right",
                    "numberFormat": "R$ 0,0.00"
                  }
                ]
              },
              "frame": { "showTitle": true, "title": "Lista de Produtos" },
              "itemsPerPage": 15,
              "withRowNumber": true
            }
          }
        }
      ]
    }
  ]
}
```

---

## Checklist para Criar um Dashboard

### 1. Planejamento
- [ ] Definir objetivos do dashboard
- [ ] Identificar métricas-chave (KPIs)
- [ ] Determinar fontes de dados
- [ ] Esboçar layout (papel ou wireframe)

### 2. Datasets
- [ ] Criar queries SQL para cada dataset
- [ ] Testar queries no Databricks SQL Editor
- [ ] Otimizar queries (índices, limites, agregações)
- [ ] Dar nomes descritivos aos datasets

### 3. Layout
- [ ] Definir estrutura de grid (quantas colunas por widget)
- [ ] Posicionar KPIs no topo (geralmente y=0 ou y=1)
- [ ] Organizar gráficos e tabelas abaixo dos KPIs
- [ ] Garantir que elementos relacionados fiquem próximos

### 4. Widgets
- [ ] Criar KPIs para métricas principais
- [ ] Criar gráficos de linha para tendências temporais
- [ ] Criar gráficos de barra para comparações
- [ ] Criar tabelas para dados detalhados
- [ ] Adicionar textboxes para títulos e contexto

### 5. Refinamento
- [ ] Testar todas as queries
- [ ] Verificar cores e formatação
- [ ] Adicionar títulos claros a todos os widgets
- [ ] Validar alinhamento e espaçamento
- [ ] Testar responsividade

### 6. Performance
- [ ] Limitar resultados de queries (LIMIT)
- [ ] Usar agregações quando possível
- [ ] Considerar materializar datasets grandes
- [ ] Testar tempo de carregamento

---

## Dicas e Boas Práticas

### Performance
1. **Agregue no SQL**: Faça agregações no dataset, não no widget
2. **Use CTEs**: Organize queries complexas com Common Table Expressions
3. **Cache queries pesadas**: Considere criar tabelas temporárias

### Design
1. **KPIs no topo**: Coloque métricas principais visíveis imediatamente
2. **Cores consistentes**: Use uma paleta de cores definida
3. **Hierarquia visual**: Tamanhos e posições refletem importância
4. **Espaço em branco**: Não sobrecarregue o dashboard

### Organização
1. **Nomes descritivos**: Use nomes claros para datasets e widgets
2. **Comentários em queries**: Documente queries SQL complexas
3. **Modularize**: Separe dashboards grandes em múltiplas páginas
4. **Versionamento**: Mantenha histórico de alterações

### Dados
1. **Trate nulos**: Use `COALESCE` para valores padrão
2. **Formate números**: Use `ROUND` para limitar casas decimais
3. **Timestamps**: Use `DATE()` para agrupar por dia
4. **Joins cuidadosos**: Use LEFT JOIN quando dados podem não existir

---

## Palette de Cores Databricks Padrão

```
Azul Principal:   #077A9D
Amarelo:          #FFAB00
Verde:            #00A972
Vermelho:         #FF3621
Azul Claro:       #8BCAE7
Roxo:             #6F42C1
Laranja:          #FD7E14
Verde Escuro:     #198754
```

---

## Troubleshooting

### Erro: Widget não exibe dados
- Verifique se o `datasetName` corresponde ao `name` do dataset
- Confirme que o `fieldName` existe na query
- Teste a query SQL separadamente no editor

### Erro: Query muito lenta
- Adicione `LIMIT` para reduzir volume de dados
- Verifique se há índices nas colunas filtradas
- Simplifique agregações complexas
- Considere pré-calcular métricas

### Widget sobreposto
- Verifique as posições x, y
- Garanta que width + x ≤ 6 (não ultrapasse o grid)
- Ajuste height para evitar sobreposição vertical

### Tabela não aparece ou não renderiza
- **Use `"version": 2`** - a version 1 NÃO funciona
- Version 2 aceita tanto estrutura simplificada quanto detalhada
- Estrutura simplificada: apenas `{ "fieldName": "nome_campo" }`
- Estrutura detalhada: inclua `displayName`, `type`, `numberFormat`, `alignContent`, etc.
- Ambas funcionam perfeitamente com version 2

### Formatação incorreta na tabela
- Na version 2 simplificada: formatação é automática pelo Databricks
- Na version 2 detalhada: use `numberFormat` para customizar (ex: `"R$ 0,0.00"`, `"0.00%"`)
- Nunca use version 1 - ela não renderiza no Databricks
- Tipos comuns: `string`, `integer`, `float`, `datetime`
- Alinhamento: `left`, `center`, `right`

### Cores não aparecem
- No line/bar charts, cores vão no `mark.colors`
- Use formato hexadecimal (#077A9D)
- Forneça cores suficientes para todas as categorias

---

## Recursos Adicionais

### Documentação Oficial
- [Databricks SQL Dashboards](https://docs.databricks.com/sql/user/dashboards/index.html)
- [Dashboard Widgets](https://docs.databricks.com/sql/user/dashboards/dashboard-widgets.html)

---

## Conclusão

Criar dashboards no Databricks requer:
1. **Conhecimento SQL**: Para criar datasets eficientes
2. **Compreensão de JSON**: Para estruturar o arquivo .lvdash.json
3. **Senso de design**: Para organizar informações visualmente
4. **Iteração**: Teste, ajuste e refine continuamente

Use este guia como referência e adapte às necessidades específicas do seu projeto.