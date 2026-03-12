CREATE OR REPLACE FUNCTION dw.RelatorioVendasPorCliente(
    cliente_nome VARCHAR DEFAULT NULL, 
    relatorio_ano INT DEFAULT NULL
)
RETURNS TABLE (
    categoria VARCHAR,
    nome_produto VARCHAR,
    ano INT,
    mes INT,
    total_valor_Venda DECIMAL(10, 2),
    total_quantidade INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dp.categoria,
        dp.nome AS nome_produto,
        dd.ano,
        dd.mes,
        SUM(fv.valor_venda) AS total_valor_Venda,
        CAST(SUM(fv.quantidade) AS INTEGER) AS total_quantidade
    FROM dw.fato_venda fv
    JOIN dw.dim_produto dp ON fv.sk_produto = dp.sk_produto
    JOIN dw.dim_data dd ON fv.sk_data = dd.sk_data
    JOIN dw.dim_cliente dc ON fv.sk_cliente = dc.sk_cliente
    WHERE 
        (cliente_nome IS NULL OR dc.nome = cliente_nome) AND
        (relatorio_ano IS NULL OR dd.ano = relatorio_ano)
    GROUP BY dp.categoria, dp.nome, dd.ano, dd.mes
    ORDER BY dp.categoria, dp.nome, dd.ano, dd.mes;
END;
$$;


CREATE OR REPLACE FUNCTION dw.update_dim_produto(
    v_id_produto INT, 
    v_nome VARCHAR, 
    v_categoria VARCHAR, 
    v_data_atual DATE
)
RETURNS VOID AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM dw.dim_produto 
        WHERE id_produto = v_id_produto AND ativo
        AND (nome <> v_nome OR categoria <> v_categoria)
    ) THEN
        UPDATE dw.dim_produto 
        SET data_fim = v_data_atual, ativo = false
        WHERE id_produto = v_id_produto AND ativo;

        INSERT INTO dw.dim_produto (id_produto, nome, categoria, data_inicio, data_fim, ativo)
        VALUES (v_id_produto, v_nome, v_categoria, v_data_atual, NULL, true);
    END IF;
END;
$$ LANGUAGE plpgsql;