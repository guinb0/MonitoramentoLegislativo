import requests
import json
from datetime import datetime
import re
import glob
import csv
import os
import pandas as pd
from time import perf_counter

def criar_diretorio(nome_diretorio):
    """Cria diretório se não existir"""
    try:
        os.makedirs(nome_diretorio, exist_ok=True)
    except Exception as e:
        print(f"Erro ao criar diretório: {e}")

def primeira_fase_extracao(parametros, tipo_proj):
    """Primeira fase: extrai dados básicos dos projetos"""
    DATAS_FIX_2023 = {'PL-192': '14/04/2023', 'PL-578': '29/09/2023'}
    DATAS_FIX_2022 = {'PL-277': '14/04/2022', 'PL-579': '30/09/2022', 'PL-280': '14/04/2022'}
    
    API_DELIBERACOES = 'https://splegisws.saopaulo.sp.leg.br/ws/ws2.asmx/FasesDeDeliberacaoJSON'
    dados = []
    
    try:
        resposta = requests.get(API_DELIBERACOES, params=parametros, timeout=60)
        if resposta.status_code == 200:
            resposta_obj = json.loads(resposta.content)
            for registro in resposta_obj:
                if registro['tipo'] != tipo_proj:
                    pass
                else:
                    infos_projeto = f"{registro['tipo']} {registro['numero']}/{registro['ano']}"
                    data_apresent_extraida = registro.get('leitura', 'Data não encontrada')
                    
                    try:
                        data_apresent = re.search(r"\d{4}-\d{2}-\d{2}", data_apresent_extraida).group()
                    except:
                        data_apresent = ""
                    
                    data_apresent_final = ""
                    frase_aprovacao = ""
                    formato_data = "%d/%m/%Y"
                    casos_especiais = False
                    
                    if data_apresent == "":
                        if registro['ano'] == 2022:
                            if DATAS_FIX_2022.get(f"{registro['tipo']}-{registro['numero']}") is not None:
                                data_apresent_final = DATAS_FIX_2022.get(f"{registro['tipo']}-{registro['numero']}")
                                casos_especiais = True
                        elif registro['ano'] == 2023:
                            if DATAS_FIX_2023.get(f"{registro['tipo']}-{registro['numero']}") is not None:
                                data_apresent_final = DATAS_FIX_2023.get(f"{registro['tipo']}-{registro['numero']}")
                                casos_especiais = True
                    
                    if not casos_especiais:
                        try:
                            data_temp = data_apresent.split("-")
                            data_apresent_final = f"{data_temp[2]}/{data_temp[1]}/{data_temp[0]}"
                        except:
                            data_apresent_final = data_apresent_extraida
                    
                    for deliberacao in registro['deliberacoes']:
                        frase_aprovacao = deliberacao['resultado']
                    
                    try:
                        data_aprovacao = re.search(r'\b\d{2}/\d{2}/\d{4}\b', frase_aprovacao).group()
                    except:
                        data_aprovacao = "Data não encontrada"
                    
                    try:
                        data_apresent_obj = datetime.strptime(data_apresent_final, formato_data)
                        data_aprovacao_obj = datetime.strptime(data_aprovacao, formato_data)
                        tempo_tramitacao = data_aprovacao_obj - data_apresent_obj
                        tempo_tramitacao_dias = str(tempo_tramitacao.days)
                    except:
                        tempo_tramitacao_dias = "Não foi possível de ser calculado"
                    
                    dados.append({
                        "numero": registro['numero'],
                        "info_projeto": infos_projeto,
                        "data_apresent": data_apresent_final,
                        "data_aprovacao": data_aprovacao,
                        "tempo_tramitacao": tempo_tramitacao_dias
                    })
            
            print("Dados extraídos com sucesso da API FasesDeDeliberação!")
            return dados
        else:
            print(f"Requisição não foi OK. Status code: {resposta.status_code}")
            return None
    except Exception as e:
        print(f"Requisição mal-sucedida ou falha de timeout na API FasesDeDeliberação: {e}")
        return None

def segunda_fase_extracao(parametros, dados, tipo_proj):
    """Segunda fase: adiciona ementas aos projetos"""
    API_PROJETOS_ANO = 'http://splegisws.saopaulo.sp.leg.br/ws/ws2.asmx/ProjetosPorAnoJSON'
    
    try:
        resposta = requests.get(API_PROJETOS_ANO, params=parametros, timeout=60)
        if resposta.status_code == 200:
            resposta_obj = json.loads(resposta.content)
            for dado in dados:
                for registro in resposta_obj:
                    if f"{tipo_proj}-{dado['numero']}" == f"{registro['tipo']}-{registro['numero']}":
                        dado["ementa"] = registro['ementa']
                        break
            print("Dados extraídos com sucesso da API ProjetosAno!")
            return dados
        else:
            print(f"Erro na segunda fase. Status: {resposta.status_code}")
            return dados
    except Exception as e:
        print(f"Requisição mal-sucedida ou falha de timeout na API ProjetosAno: {e}")
        return dados

def escrever_arquivo_csv(caminho_arquivo, info, cabecalho):
    """Escreve dados no arquivo CSV"""
    if len(glob.glob(caminho_arquivo)) > 0:
        try:
            with open(caminho_arquivo, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(info)
        except Exception as e:
            print(f"Erro ao escrever no arquivo existente: {e}")
    else:
        try:
            with open(caminho_arquivo, "w", newline="") as f:
                info.insert(0, cabecalho)
                writer = csv.writer(f)
                writer.writerows(info)
        except Exception as e:
            print(f"Erro ao criar novo arquivo: {e}")

def escrever_planilha(caminho_arquivo_csv, caminho_planilha):
    """Converte CSV para Excel"""
    df_projetos_tramitacao = pd.read_csv(caminho_arquivo_csv)
    with pd.ExcelWriter(caminho_planilha, mode="w", engine="openpyxl") as writer:
        df_projetos_tramitacao.to_excel(writer, sheet_name="Folha1", index=False)
    print("Planilha gerada com sucesso!")

def extrair_projetos_tramitacao(ano, tipo_projeto):
    """
    Extrai informações sobre projetos em tramitação
    
    Args:
        ano (int): Ano para extração
        tipo_projeto (str): Tipo de projeto (PL, PDL, etc)
    
    Returns:
        dict: Dicionário com resultado da extração
    """
    inicio = perf_counter()
    
    try:
        CABECALHO = ["Projeto", "Ementa", "Data_Apresentação", "Data_Aprovação", "Tempo_Tramitação"]
        
        parametros = {'ano': str(ano)}
        
        diretorio_dados = f"resultados/dados-{tipo_projeto}-{ano}"
        criar_diretorio(diretorio_dados)
        
        print(f"Iniciando extração para {tipo_projeto} do ano {ano}...")
        
        # Primeira fase
        dados = primeira_fase_extracao(parametros, tipo_projeto)
        
        if dados is None or len(dados) == 0:
            return {
                'sucesso': False,
                'erro': f'Nenhum dado encontrado para {tipo_projeto} do ano {ano}'
            }
        
        # Segunda fase
        dados = segunda_fase_extracao(parametros, dados, tipo_projeto)
        
        if dados is None:
            return {
                'sucesso': False,
                'erro': 'Erro na segunda fase de extração'
            }
        
        # Escrever dados
        caminho_arquivo_csv = f"{diretorio_dados}/projetos_tramitacao_{tipo_projeto}_{ano}.csv"
        caminho_arquivo_planilha = f"{diretorio_dados}/projetos_tramitacao_{tipo_projeto}_{ano}.xlsx"
        
        for dado in dados:
            lista_insercao = []
            lista_insercao.append([
                dado["info_projeto"],
                dado.get("ementa", "Ementa não disponível"),
                dado["data_apresent"],
                dado["data_aprovacao"],
                dado["tempo_tramitacao"]
            ])
            escrever_arquivo_csv(caminho_arquivo_csv, lista_insercao, CABECALHO)
        
        escrever_planilha(caminho_arquivo_csv, caminho_arquivo_planilha)
        
        fim = perf_counter()
        tempo_execucao = fim - inicio
        
        return {
            'sucesso': True,
            'arquivo_excel': caminho_arquivo_planilha,
            'total_projetos': len(dados),
            'tempo_execucao': tempo_execucao
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e)
        }
