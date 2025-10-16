import requests
import csv
import re
import json
from bs4 import BeautifulSoup
import os
import glob
import pandas as pd
from time import perf_counter

def criar_diretorio(nome_diretorio):
    """Cria diretório se não existir"""
    try:
        os.makedirs(nome_diretorio, exist_ok=True)
    except Exception as e:
        print(f"Erro ao criar diretório: {e}")

def extrair_gastos_vereadores(ano, mes_inicio, mes_fim):
    """
    Extrai gastos de vereadores da Câmara Municipal de São Paulo
    
    Args:
        ano (int): Ano para extração
        mes_inicio (int): Mês inicial (1-12)
        mes_fim (int): Mês final (1-12)
    
    Returns:
        dict: Dicionário com resultado da extração
    """
    inicio = perf_counter()
    
    try:
        dados_csv = []
        dados_json = []
        mes_dir = f"resultados/mes_{ano}"
        ind_dir = f"resultados/ind_{ano}"
        
        criar_diretorio(mes_dir)
        criar_diretorio(ind_dir)
        
        # Regex para remover tags HTML
        TAG_RE = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        
        def remove_tags(text):
            return TAG_RE.sub('', text)
        
        # Loop pelos meses selecionados
        for vmes in range(mes_inicio, mes_fim + 1):
            mes = f"{vmes:02d}"
            mesano = mes + str(ano)
            anomes = str(ano) + mes
            
            url = f"https://sisgvarmazenamento.blob.core.windows.net/prd/PublicacaoPortal/Arquivos/{anomes}.htm"
            
            print(f"Processando {mes}/{ano}...")
            
            try:
                # Consultar o site
                page = requests.get(url, timeout=30)
                
                if page.status_code != 200:
                    print(f"Aviso: Mês {mes}/{ano} não disponível (Status: {page.status_code})")
                    continue
                
                soup = BeautifulSoup(page.content, 'html5lib')
                
                # Criar arquivo CSV para o mês
                csv_filename = f"{mes_dir}/Dados{mesano}.csv"
                f = csv.writer(open(csv_filename, 'w'))
                f.writerow(['Vereador', 'Tipo_de_Gasto', 'Nome_Da_Empresa', 'CNPJ', 'Valor', 'Mes/Ano'])
                
                # Inicialização de variáveis
                index = 0
                start = 0
                nomeVereador = ""
                categoriaDespesa = ""
                cnpj = ""
                LugarDespesa = ""
                skip = 0
                ignore = 0
                bugduplo = 1
                
                # Percorrer as tabelas HTML
                name_list = soup.find('body')
                
                if name_list is None:
                    print(f"Erro: Não foi possível processar o HTML do mês {mes}/{ano}")
                    continue
                
                for tr in name_list.find_all('tr'):
                    if bugduplo == 0:
                        bugduplo = -1
                        continue
                    
                    # Extração do nome do vereador
                    if tr.find(text=re.compile(r"[\s\S]+(Vereador)\((a)\)[:\s]", re.I)):
                        start = 1
                        name_list_itemsp = tr.find_all('td')
                        for name in name_list_itemsp:
                            if name.find(text=re.compile(r"[\s\S]+(Vereador)\((a)\)", re.I)):
                                names = str(name.contents[1])
                                names = re.sub(r"[\s\S]+(Vereador)\((a)\)[:\s]", "", names)
                                names = remove_tags(names)
                                nomeVereador = names
                                ignore = 0
                                if bugduplo == 1:
                                    bugduplo = 0
                    
                    if start != 0:
                        name_list_itemsv = tr.find_all('td')
                        for name in name_list_itemsv:
                            names = str(name.contents[0])
                            
                            if skip == 1:
                                skip = 0
                                continue
                            if ignore == 1:
                                continue
                            
                            names = remove_tags(names)
                            names = re.sub("(Natureza da despesa)", "", names)
                            names = re.sub("(Valor utilizado)", "", names)
                            names = re.sub("(VALORES GASTOS)", "", names)
                            names = re.sub("(VALORES DISPONIBILIZADOS)", "", names)
                            names = re.sub("(TOTAL DO ITEM)", "VXASkip", names)
                            names = re.sub("(TOTAL DO MÊS)", "VXBSkip", names)
                            names = re.sub("(VEREADOR AFASTADO)", "VXBSkip", names)
                            
                            if re.match(r"\d{2}.?\d{3}.?\d{3}/?\\d{4}-?\\d{2}", names) is not None:
                                start = 2
                            
                            if re.match(r"[\s\S]*(VXASkip)", names) is not None:
                                start = 1
                                skip = 1
                                continue
                            
                            if re.match(r"[\s\S]*(VXBSkip)", names) is not None:
                                start = 0
                                ignore = 1
                                break
                            
                            if re.match(r'^\s*$', names):
                                continue
                            
                            if start == 1:
                                categoriaDespesa = names
                                start = 2
                                continue
                            
                            if start == 2:
                                cnpj = names
                                start = 3
                                continue
                            
                            if start == 3:
                                LugarDespesa = names
                                start = 4
                                continue
                            
                            if start >= 4:
                                info_vereador_csv = [[nomeVereador, categoriaDespesa, LugarDespesa, cnpj, names, (mes + "/" + str(ano))]]
                                info_vereador_json = {
                                    'Vereador': nomeVereador,
                                    'Tipo_de_Gasto': categoriaDespesa,
                                    'Nome_Da_Empresa': LugarDespesa,
                                    'CNPJ': cnpj,
                                    'Valor': names,
                                    'Mes/Ano': (mes + "/" + str(ano))
                                }
                                dados_csv.append(info_vereador_csv)
                                dados_json.append(info_vereador_json)
                                f.writerows(info_vereador_csv)
                                start = 2
                            
                            start += 1
                
            except Exception as e:
                print(f"Erro ao processar mês {mes}/{ano}: {str(e)}")
                continue
        
        # Criar arquivos individuais por vereador
        for dado in dados_csv:
            arquivo_vereador = f"{ind_dir}/Dados_{dado[0][0]}.csv"
            if len(glob.glob(arquivo_vereador)) > 0:
                with open(arquivo_vereador, "a") as f:
                    writer = csv.writer(f)
                    writer.writerows(dado)
            else:
                with open(arquivo_vereador, "w") as f:
                    writer = csv.writer(f)
                    writer.writerow(['Vereador', 'Tipo_de_Gasto', 'Nome_Da_Empresa', 'CNPJ', 'Valor', 'Mes/Ano'])
                    writer.writerows(dado)
        
        # Consolidar todos os CSVs
        tipo_arquivo = 'csv'
        todos_csv = [i for i in glob.glob(f'{mes_dir}/*.{tipo_arquivo}')]
        
        if len(todos_csv) == 0:
            return {
                'sucesso': False,
                'erro': 'Nenhum dado foi extraído. Verifique se os meses selecionados têm dados disponíveis.'
            }
        
        # Combinar todos os arquivos
        combinado_csv = pd.concat([pd.read_csv(f) for f in todos_csv])
        
        # Exportar CSV consolidado
        arquivo_csv_final = f"resultados/gastos_vereadores_{ano}_{mes_inicio:02d}_{mes_fim:02d}.csv"
        combinado_csv.to_csv(arquivo_csv_final, index=False, encoding='utf-8-sig')
        
        # Ler e limpar dados
        df_vereadores = pd.read_csv(arquivo_csv_final)
        df_vereadores = df_vereadores.sort_values(by='Vereador')
        
        # Exportar para Excel
        arquivo_excel = f"resultados/Gastos_Vereadores_{ano}_{mes_inicio:02d}_{mes_fim:02d}.xlsx"
        df_vereadores.to_excel(arquivo_excel, index=False, engine='openpyxl')
        
        fim = perf_counter()
        tempo_execucao = fim - inicio
        
        # Estatísticas
        total_registros = len(df_vereadores)
        total_vereadores = df_vereadores['Vereador'].nunique()
        
        return {
            'sucesso': True,
            'arquivo_excel': arquivo_excel,
            'arquivo_csv': arquivo_csv_final,
            'total_registros': total_registros,
            'total_vereadores': total_vereadores,
            'tempo_execucao': tempo_execucao
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e)
        }
