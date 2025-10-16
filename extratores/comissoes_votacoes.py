import requests
import json
import csv
import glob
import os
import pandas as pd
from time import perf_counter

def criar_diretorio(nome_diretorio):
    """Cria diretório se não existir"""
    try:
        os.makedirs(nome_diretorio, exist_ok=True)
    except Exception as e:
        print(f"Erro ao criar diretório: {e}")

def escrever_info_vereador(caminho_arquivo, dados, cabecalho):
    """Escreve informações do vereador no arquivo CSV"""
    if len(glob.glob(caminho_arquivo)) > 0:
        try:
            with open(caminho_arquivo, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(dados)
        except Exception as e:
            print(f"Erro ao escrever no arquivo existente: {e}")
    else:
        try:
            with open(caminho_arquivo, "w", newline="") as f:
                dados.insert(0, cabecalho)
                writer = csv.writer(f)
                writer.writerows(dados)
        except Exception as e:
            print(f"Erro ao criar novo arquivo: {e}")

def coleta_info_vereador(info_vereador_encaminhamentos, cabecalho, infos_projeto, nome_diretorio):
    """Coleta informações de votação dos vereadores"""
    for encaminhamento in info_vereador_encaminhamentos:
        if encaminhamento.get("comissoes") is not None:
            for comissao in encaminhamento["comissoes"]:
                dados = []
                dados.append([
                    comissao["nome"],
                    comissao["nomePolitico"],
                    infos_projeto,
                    comissao.get("conclusao", "Aguarda votação pela comissão")
                ])
                caminho_arquivo = f"{nome_diretorio}/{comissao['nomePolitico']}.csv"
                escrever_info_vereador(caminho_arquivo, dados, cabecalho)

def gerar_planilha_agregada(diretorio_dados, tipo, ano, diretorio_planilhas):
    """Gera planilha agregada com todos os dados"""
    arquivos_csv = [i for i in glob.glob(f"{diretorio_dados}/*.csv")]
    
    if len(arquivos_csv) == 0:
        return None
    
    combinado_csv = pd.concat([pd.read_csv(f) for f in arquivos_csv])
    nome_base = "comissoes_votacoes_agregada"
    caminho_csv_combinado = f"{diretorio_planilhas}/{nome_base}_{tipo}_{ano}.csv"
    caminho_excel_agregado = f"{diretorio_planilhas}/{nome_base}_{tipo}_{ano}.xlsx"
    
    combinado_csv.to_csv(caminho_csv_combinado, index=False)
    df_comissoes_votacoes = pd.read_csv(caminho_csv_combinado)
    df_comissoes_votacoes = df_comissoes_votacoes.sort_values(by='Parlamentar')
    
    with pd.ExcelWriter(caminho_excel_agregado, mode="w", engine="openpyxl") as writer:
        df_comissoes_votacoes.to_excel(writer, sheet_name="Folha1", index=False)
    
    print("Planilha agregada gerada com sucesso!")
    return caminho_excel_agregado

def extrair_comissoes_votacoes(ano, tipo_projeto):
    """
    Extrai informações sobre comissões e votações
    
    Args:
        ano (int): Ano para extração
        tipo_projeto (str): Tipo de projeto (PL, PDL, etc)
    
    Returns:
        dict: Dicionário com resultado da extração
    """
    inicio = perf_counter()
    
    try:
        CABECALHO = ["Comissão", "Parlamentar", "Projeto/Requerimento", "Voto"]
        URL = 'https://splegisws.saopaulo.sp.leg.br/ws/ws2.asmx/ProjetosReunioesDeComissaoJSON'
        
        parametros = {
            'ano': str(ano),
            'tipo': str(tipo_projeto)
        }
        
        diretorio_dados = f"resultados/dados-{tipo_projeto}-{ano}"
        diretorio_planilhas = f"resultados/planilhas-{tipo_projeto}-{ano}"
        
        criar_diretorio(diretorio_dados)
        criar_diretorio(diretorio_planilhas)
        
        dados_ok = False
        
        print(f"Consultando API para {tipo_projeto} do ano {ano}...")
        
        resposta = requests.get(URL, params=parametros, timeout=60)
        
        if resposta.status_code == 200:
            resposta_obj = json.loads(resposta.content)
            
            if len(resposta_obj) == 0:
                return {
                    'sucesso': False,
                    'erro': f'Nenhum dado encontrado para {tipo_projeto} do ano {ano}'
                }
            
            for registro in resposta_obj:
                infos_projeto = f"{registro['tipo']} {registro['numero']}/{registro['ano']}"
                if registro.get("encaminhamentos") is not None:
                    coleta_info_vereador(
                        info_vereador_encaminhamentos=registro["encaminhamentos"],
                        cabecalho=CABECALHO,
                        infos_projeto=infos_projeto,
                        nome_diretorio=diretorio_dados
                    )
                    dados_ok = True
        else:
            return {
                'sucesso': False,
                'erro': f'Requisição não foi OK. Status code: {resposta.status_code}'
            }
        
        if dados_ok:
            arquivo_excel = gerar_planilha_agregada(diretorio_dados, tipo_projeto, ano, diretorio_planilhas)
            
            if arquivo_excel is None:
                return {
                    'sucesso': False,
                    'erro': 'Não foi possível gerar a planilha agregada'
                }
            
            # Estatísticas
            df = pd.read_excel(arquivo_excel)
            total_registros = len(df)
            
            fim = perf_counter()
            tempo_execucao = fim - inicio
            
            return {
                'sucesso': True,
                'arquivo_excel': arquivo_excel,
                'total_registros': total_registros,
                'tempo_execucao': tempo_execucao
            }
        else:
            return {
                'sucesso': False,
                'erro': 'Nenhum dado foi extraído'
            }
            
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e)
        }
