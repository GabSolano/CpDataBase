import os
import oracledb
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder='../')

DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_DSN = os.environ.get("DB_DSN")

def conectar_banco():
    return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)

@app.route('/')
def index():
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT id_ativo, nome, setor, preco_base, estoque FROM TB_ATIVOS_GALACTICOS ORDER BY id_ativo")
        ativos = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('index.html', ativos=ativos)
    except Exception as e:
        return f"Falha na conexão ou na busca de dados: {e}"

@app.route('/processar', methods=['POST'])
def processar():
    evento = request.form.get('evento')
    setor = request.form.get('setor')
    valor = request.form.get('valor')
    
    plsql_block = """
    DECLARE
        v_tipo_evento  VARCHAR2(50) := :evento;
        v_alvo_setor   VARCHAR2(20) := :setor;
        v_percentual   NUMBER       := :valor;
        v_preco_final  NUMBER(10,2);
        
        CURSOR c_itens_galacticos IS
            SELECT id_ativo, preco_base 
            FROM TB_ATIVOS_GALACTICOS 
            WHERE setor = v_alvo_setor;
    BEGIN
        FOR r_item IN c_itens_galacticos LOOP
            
            IF v_tipo_evento = 'RADIACAO' THEN
                v_preco_final := r_item.preco_base + (r_item.preco_base * (v_percentual / 100));
            ELSIF v_tipo_evento = 'DESCOBERTA_MINA' THEN
                v_preco_final := r_item.preco_base - (r_item.preco_base * (v_percentual / 100));
            ELSE
                v_preco_final := r_item.preco_base;
            END IF;

            UPDATE TB_ATIVOS_GALACTICOS
            SET preco_base = v_preco_final
            WHERE id_ativo = r_item.id_ativo;
            
        END LOOP;
        
        COMMIT;
    END;
    """
    
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute(plsql_block, evento=evento, setor=setor, valor=float(valor))
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Falha ao rodar a procedure PL/SQL: {e}")
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
