-- Carrega dim_produto
INSERT INTO dw.dim_produto (id_produto, nome, categoria)
VALUES 
    (1000, 'Laptop', 'Eletrônicos'),
    (2000, 'Tablet', 'Eletrônicos'),
    (3000, 'Café', 'Alimentos'),
    (4000, 'Smartphone', 'Eletrônicos'),
    (5000, 'Refrigerante', 'Bebidas'),
    (6000, 'Suco', 'Bebidas'),
    (7000, 'Livro', 'Educação'),
    (8000, 'Fone de Ouvido', 'Eletrônicos'),
    (9000, 'Notebook', 'Eletrônicos'),
    (10000, 'Mouse', 'Acessórios');

-- Carrega dim_canal
INSERT INTO dw.dim_canal (id_canal, nome, regiao)
VALUES 
    (100, 'E-commerce', 'Global'),
    (101, 'Loja Física', 'América do Norte'),
    (102, 'Revendedor', 'Europa'),
    (103, 'Distribuidor', 'Ásia'),
    (104, 'Marketplace', 'América do Sul'),
    (105, 'Atacado', 'África'),
    (106, 'Varejo', 'Oceania'),
    (107, 'Vendas Diretas', 'América do Norte'),
    (108, 'Parcerias', 'Europa'),
    (109, 'Telemarketing', 'América Latina');

-- Carrega dim_cliente
INSERT INTO dw.dim_cliente (id_cliente, nome, tipo, cidade, estado, pais)
VALUES 
    (1001, 'Empresa Alpha', 'Corporativo', 'São Paulo', 'SP', 'Brasil'),
    (1002, 'João Silva', 'Individual', 'Rio de Janeiro', 'RJ', 'Brasil'),
    (1003, 'Maria Oliveira', 'Individual', 'Lisboa', 'NA', 'Portugal'),
    (1004, 'Empresa Beta', 'Corporativo', 'Porto Alegre', 'RS', 'Brasil'),
    (1005, 'Carlos Mendez', 'Individual', 'Madri', 'NA', 'Espanha'),
    (1006, 'Empresa Gamma', 'Corporativo', 'Buenos Aires', '', 'Argentina'),
    (1007, 'Ana Pereira', 'Individual', 'Santiago', 'NA', 'Chile'),
    (1008, 'Empresa Delta', 'Corporativo', 'Nova York', 'NY', 'Estados Unidos'),
    (1009, 'James Brown', 'Individual', 'Londres', 'NA', 'Reino Unido'),
    (1010, 'Empresa Epsilon', 'Corporativo', 'Sydney', 'NA', 'Austrália');