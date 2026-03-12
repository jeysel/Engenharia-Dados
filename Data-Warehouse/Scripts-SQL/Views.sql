CREATE VIEW dw.VW_VendasPorProdutoCanal AS
SELECT 
    dp.nome AS Nome_Produto,
    dc.nome AS Nome_Canal,
    SUM(fv.valor_venda) AS Total_Vendas,
    SUM(fv.quantidade) AS Total_Quantidade
FROM dw.fato_venda fv
JOIN dw.dim_produto dp ON fv.sk_produto = dp.sk_produto
JOIN dw.dim_canal dc ON fv.sk_canal = dc.sk_canal
GROUP BY dp.nome, dc.nome;

CREATE VIEW dw.VW_VendasPorClientePeriodo AS
SELECT 
    dc.nome AS Nome_Cliente,
    dd.ano,
    dd.mes,
    SUM(fv.valor_venda) AS Total_Vendas,
    SUM(fv.quantidade) AS Total_Quantidade
FROM dw.fato_venda fv
JOIN dw.dim_cliente dc ON fv.sk_cliente = dc.sk_cliente
JOIN dw.dim_data dd ON fv.sk_data = dd.sk_data
GROUP BY dc.nome, dd.ano, dd.mes;

CREATE MATERIALIZED VIEW dw.MV_RelatorioVendasResumido AS
SELECT 
    dp.categoria AS Categoria,
    SUM(fv.valor_venda) AS Total_Vendas,
    SUM(fv.quantidade) AS Total_Quantidade,
    dd.Ano
FROM dw.fato_venda fv
JOIN dw.dim_produto dp ON fv.sk_produto = dp.sk_produto
JOIN dw.dim_data dd ON fv.sk_data = dd.sk_data
GROUP BY dp.categoria, dd.ano
ORDER BY dd.ano;

