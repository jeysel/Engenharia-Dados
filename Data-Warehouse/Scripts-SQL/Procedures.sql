CREATE OR REPLACE PROCEDURE dw.sp_popula_dim_data()
LANGUAGE plpgsql
AS $$
DECLARE
    v_data_inicial DATE := '2021-01-01';
    v_data_final DATE := '2031-12-31';
BEGIN
    WHILE v_data_inicial <= v_data_final LOOP
        INSERT INTO dw.dim_data (dia, mes, ano, data_completa)
        VALUES (
            EXTRACT(DAY FROM v_data_inicial),
            EXTRACT(MONTH FROM v_data_inicial),
            EXTRACT(YEAR FROM v_data_inicial),
            v_data_inicial
        );
        v_data_inicial := v_data_inicial + INTERVAL '1 day';
    END LOOP;
END;
$$;

CALL dw.sp_popula_dim_data();



CREATE OR REPLACE PROCEDURE dw.sp_carrega_tabela_fato()
LANGUAGE plpgsql
AS $$
DECLARE
    i INT := 1;
    v_sk_produto INT;
    v_sk_canal INT;
    v_sk_data INT;
    v_sk_cliente INT;
BEGIN
    WHILE i <= 1000 LOOP
        v_sk_produto := (SELECT sk_produto FROM dw.dim_produto ORDER BY RANDOM() LIMIT 1);
        v_sk_canal := (SELECT sk_canal FROM dw.dim_canal ORDER BY RANDOM() LIMIT 1);
        v_sk_data := (SELECT sk_data FROM dw.dim_data WHERE ano <= 2025 ORDER BY RANDOM() LIMIT 1);
        v_sk_cliente := (SELECT sk_cliente FROM dw.dim_cliente ORDER BY RANDOM() LIMIT 1);

        BEGIN
            INSERT INTO dw.fato_venda (sk_produto, sk_canal, sk_data, sk_cliente, quantidade, valor_venda)
            VALUES (
                v_sk_produto,
                v_sk_canal,
                v_sk_data,
                v_sk_cliente,
                FLOOR(1 + RANDOM() * 125),
                ROUND(CAST(RANDOM() * 1000 AS numeric), 2)
            );
            i := i + 1;
        EXCEPTION WHEN unique_violation THEN
            CONTINUE;
        END;
    END LOOP;
END;
$$;

CALL dw.sp_carrega_tabela_fato();


