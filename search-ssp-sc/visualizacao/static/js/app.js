// Configurações globais
const API_BASE_URL = '';

// Estado da aplicação
let dadosAtuais = [];
let filtrosAtuais = {};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    carregarFiltros();
    carregarDados();
    configurarEventos();
});

// Configurar eventos
function configurarEventos() {
    // Formulário de filtros
    document.getElementById('filtrosForm').addEventListener('submit', function(e) {
        e.preventDefault();
        aplicarFiltros();
    });

    // Botão limpar filtros
    document.getElementById('limparFiltros').addEventListener('click', function() {
        document.getElementById('filtrosForm').reset();
        filtrosAtuais = {};
        carregarDados();
    });

    // Botão atualizar
    document.getElementById('atualizarDados').addEventListener('click', function(e) {
        e.preventDefault();
        carregarDados();
    });

    // Botão exportar CSV
    document.getElementById('exportarCSV').addEventListener('click', exportarCSV);
}

// Carregar opções de filtros
async function carregarFiltros() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/filtros`);
        const data = await response.json();

        if (data.success) {
            // Preencher select de tipos de ocorrência
            const selectTipo = document.getElementById('filtroTipo');
            data.filtros.tipos_ocorrencia.forEach(tipo => {
                const option = document.createElement('option');
                option.value = tipo;
                option.textContent = tipo;
                selectTipo.appendChild(option);
            });

            // Preencher select de municípios
            const selectMunicipio = document.getElementById('filtroMunicipio');
            data.filtros.municipios.forEach(municipio => {
                const option = document.createElement('option');
                option.value = municipio;
                option.textContent = municipio;
                selectMunicipio.appendChild(option);
            });

            // Preencher select de regiões
            const selectRegiao = document.getElementById('filtroRegiao');
            data.filtros.regioes.forEach(regiao => {
                const option = document.createElement('option');
                option.value = regiao;
                option.textContent = regiao;
                selectRegiao.appendChild(option);
            });

            // Preencher select de anos
            const selectAno = document.getElementById('filtroAno');
            data.filtros.anos.forEach(ano => {
                const option = document.createElement('option');
                option.value = ano;
                option.textContent = ano;
                selectAno.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar filtros:', error);
        mostrarErro('Erro ao carregar filtros');
    }
}

// Aplicar filtros
function aplicarFiltros() {
    const formData = new FormData(document.getElementById('filtrosForm'));
    filtrosAtuais = {};

    for (let [key, value] of formData.entries()) {
        if (value) {
            filtrosAtuais[key] = value;
        }
    }

    carregarDados();
}

// Carregar dados
async function carregarDados() {
    mostrarLoading(true);

    try {
        // Construir query string
        const params = new URLSearchParams(filtrosAtuais);

        // Carregar estatísticas
        const responseStats = await fetch(`${API_BASE_URL}/api/estatisticas?${params}`);
        const dataStats = await responseStats.json();

        if (dataStats.success) {
            atualizarEstatisticas(dataStats.estatisticas);
        }

        // Carregar dados
        const responseDados = await fetch(`${API_BASE_URL}/api/dados?${params}`);
        const dataDados = await responseDados.json();

        if (dataDados.success) {
            dadosAtuais = dataDados.dados;
            atualizarTabela(dadosAtuais);
        }

        // Carregar gráficos
        await carregarGraficos();

    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        mostrarErro('Erro ao carregar dados');
    } finally {
        mostrarLoading(false);
    }
}

// Atualizar estatísticas
function atualizarEstatisticas(stats) {
    document.getElementById('statTotalOcorrencias').textContent =
        formatarNumero(stats.total_ocorrencias);
    document.getElementById('statTotalRegistros').textContent =
        formatarNumero(stats.total_registros);
    document.getElementById('statMunicipios').textContent =
        formatarNumero(stats.municipios_afetados);
    document.getElementById('statMediaMunicipio').textContent =
        formatarNumero(stats.media_por_municipio.toFixed(1));
}

// Atualizar tabela
function atualizarTabela(dados) {
    const tbody = document.getElementById('tabelaDadosBody');
    tbody.innerHTML = '';

    if (dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum dado encontrado</td></tr>';
        return;
    }

    // Limitar a 100 registros para performance
    const dadosLimitados = dados.slice(0, 100);

    dadosLimitados.forEach(dado => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${dado.tipo_ocorrencia || '-'}</td>
            <td>${dado.municipio || '-'}</td>
            <td>${dado.regiao || '-'}</td>
            <td>${dado.ano || '-'}</td>
            <td>${dado.mes ? obterNomeMes(dado.mes) : '-'}</td>
            <td><strong>${formatarNumero(dado.quantidade)}</strong></td>
        `;
        tbody.appendChild(tr);
    });

    if (dados.length > 100) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td colspan="6" class="text-center text-muted">
                Mostrando 100 de ${formatarNumero(dados.length)} registros
            </td>
        `;
        tbody.appendChild(tr);
    }
}

// Carregar gráficos
async function carregarGraficos() {
    const params = new URLSearchParams(filtrosAtuais);

    try {
        // Gráfico de evolução temporal
        const responseEvolucao = await fetch(`${API_BASE_URL}/api/grafico/evolucao-temporal?${params}`);
        const dataEvolucao = await responseEvolucao.json();
        if (dataEvolucao.success) {
            Plotly.newPlot('graficoEvolucao', JSON.parse(dataEvolucao.grafico).data,
                JSON.parse(dataEvolucao.grafico).layout, {responsive: true});
        }

        // Gráfico de tipos
        const responseTipos = await fetch(`${API_BASE_URL}/api/grafico/ocorrencias-por-tipo?${params}`);
        const dataTipos = await responseTipos.json();
        if (dataTipos.success) {
            Plotly.newPlot('graficoTipos', JSON.parse(dataTipos.grafico).data,
                JSON.parse(dataTipos.grafico).layout, {responsive: true});
        }

        // Gráfico de regiões
        const responseRegioes = await fetch(`${API_BASE_URL}/api/grafico/ocorrencias-por-regiao?${params}`);
        const dataRegioes = await responseRegioes.json();
        if (dataRegioes.success) {
            Plotly.newPlot('graficoRegioes', JSON.parse(dataRegioes.grafico).data,
                JSON.parse(dataRegioes.grafico).layout, {responsive: true});
        }

        // Gráfico de municípios
        const responseMunicipios = await fetch(`${API_BASE_URL}/api/grafico/ocorrencias-por-municipio?${params}`);
        const dataMunicipios = await responseMunicipios.json();
        if (dataMunicipios.success) {
            Plotly.newPlot('graficoMunicipios', JSON.parse(dataMunicipios.grafico).data,
                JSON.parse(dataMunicipios.grafico).layout, {responsive: true});
        }

    } catch (error) {
        console.error('Erro ao carregar gráficos:', error);
    }
}

// Exportar para CSV
function exportarCSV() {
    if (dadosAtuais.length === 0) {
        alert('Nenhum dado para exportar');
        return;
    }

    // Criar CSV
    let csv = 'Tipo de Ocorrência,Município,Região,Ano,Mês,Quantidade\n';

    dadosAtuais.forEach(dado => {
        csv += `"${dado.tipo_ocorrencia || ''}","${dado.municipio || ''}","${dado.regiao || ''}",`;
        csv += `${dado.ano || ''},${dado.mes || ''},${dado.quantidade || 0}\n`;
    });

    // Download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `dados_ssp_sc_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Utilitários
function mostrarLoading(mostrar) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = mostrar ? 'flex' : 'none';
}

function mostrarErro(mensagem) {
    alert(mensagem);
}

function formatarNumero(numero) {
    return new Intl.NumberFormat('pt-BR').format(numero);
}

function obterNomeMes(mes) {
    const meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];
    return meses[mes - 1] || mes;
}
