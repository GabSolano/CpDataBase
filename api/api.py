import os
import oracledb
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder='../')

DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_DSN = os.environ.get("DB_DSN")

def get_connection():
    return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)

@app.route('/')
def index():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_ativo, nome, setor, preco_base, estoque FROM TB_ATIVOS_GALACTICOS ORDER BY id_ativo")
        ativos = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('index.html', ativos=ativos)
    except Exception as e:
        return f"Erro ao conectar no banco de dados ou executar a consulta: {e}"

@app.route('/processar', methods=['POST'])
def processar():
    evento = request.form.get('evento')
    setor = request.form.get('setor')
    valor = request.form.get('valor')
    
    plsql_block = """
    DECLARE
        v_evento       VARCHAR2(50) := :evento;
        v_setor        VARCHAR2(20) := :setor;
        v_fator        NUMBER       := :valor;
        v_novo_preco   NUMBER(10,2);
        
        CURSOR c_ativos IS
            SELECT
                id_ativo,
                preco_base
            FROM
                TB_ATIVOS_GALACTICOS
            WHERE
                setor = v_setor;
    BEGIN
        FOR r_ativo IN c_ativos LOOP
            
            IF v_evento = 'RADIACAO' THEN
                v_novo_preco := r_ativo.preco_base + (r_ativo.preco_base * (v_fator / 100));
            ELSIF v_evento = 'DESCOBERTA_MINA' THEN
                v_novo_preco := r_ativo.preco_base - (r_ativo.preco_base * (v_fator / 100));
            ELSE
                v_novo_preco := r_ativo.preco_base;
            END IF;

            UPDATE
                TB_ATIVOS_GALACTICOS
            SET
                preco_base = v_novo_preco
            WHERE
                id_ativo = r_ativo.id_ativo;
                
        END LOOP;
        
        COMMIT;
    END;
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(plsql_block, evento=evento, setor=setor, valor=float(valor))
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Erro na execução do PL/SQL: {e}")
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)