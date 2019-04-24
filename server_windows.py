from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from sys import argv
import json
import logging
import pandas as pd
import psycopg2


class S(BaseHTTPRequestHandler):

    def _set_response(self, num=200):
        self.send_response(num)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        path_splited = self.path[1:].split('/')
        if not path_splited[0] == 'titulo_tesouro':
            self.send_response(400)
            self.wfile.write("Path not valid.".encode('utf-8'))
        else:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data)
            id = int(path_splited[1])
            if id:
                params['id'] = id
                self.get_historic(params)


    def do_POST(self):
        content_length = int(self.headers['Content-Length']) 
        post_data = self.rfile.read(content_length)
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))
        if self.request_is_valid():
            params = json.loads(post_data)
            cur = get_cursor()
            cur.execute(f"SELECT id FROM category WHERE title = '{params['categoria_titulo']}'")
            try:
                category_id = cur.fetchone()[0]
            except TypeError:
                cur.execute(f"INSERT INTO category(title) VALUES ('{params['categoria_titulo']}') RETURNING id")
                category_id = cur.fetchone()[0]
                response = f"Created new category {params['categoria_titulo']}, id = {category_id}. "
            date = datetime.strptime(str(params['mes'])+str(params['ano']), f"%m%Y")
            action = 0 if 'resgate' in params['acao'] else 1
            self._set_response()
            try:
                cur.execute(f"INSERT INTO monetary_value VALUES ({category_id}, '{date}', {action}, {params['valor']}) ")
                commit()
                dict_response = {'success': True, 'message': (response if response else "")+"Data inserted successfully."}
            except psycopg2.errors.UniqueViolation:
                dict_response = {'success': False, 'message': "This monetary value already exists."}
            self.wfile.write(json.dumps(dict_response).encode('utf-8'))

    def do_DELETE(self):
        logging.info("DELETE request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        if self.request_is_valid():
            self.wfile.write(self.path)

    def do_PUT(self):
        logging.info("PUT request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        if self.request_is_valid():
            self.wfile.write(self.path)

    def request_is_valid(self):
        if 'titulo_tesouro' in self.path:
            return True
        self.send_response(400)
        self.wfile.write("Path not valid.".encode('utf-8'))
        return False

    def get_historic(self, params):

        start_date = params.get('data_inicio', None)
        end_date = params.get('data_fim', None)
        group_by = params.get('group_by', None)

        start_date = datetime.strptime(start_date, f"%m/%Y") if start_date else None
        end_date = datetime.strptime(end_date, f"%m/%Y") if end_date else None

        cur = get_cursor()
        cur.execute(f"SELECT title FROM category WHERE id = {params['id']}")
        try:
            title = cur.fetchone()[0]
        except TypeError:
            title = None
            self._set_response(400)
            self.wfile.write("Category not found.".encode('utf-8'))
        
        if title:
            response = {'id': params['id'], 'categoria_titulo': title}

            date_greater_then = f"AND date >= '{start_date}'" if start_date else ""
            date_lower_then = f"AND date <= '{end_date}'" if end_date else ""

            if group_by:
                select = f'''SELECT EXTRACT(YEAR FROM date) as year, action, SUM(value) FROM monetary_value
                        WHERE category = {params['id']} {date_greater_then} {date_lower_then}
                        GROUP BY year, action
                        ORDER BY year'''
                cur.execute(select)
                historico = {}
                for row in cur:
                    year = int(row[0])
                    if historico.get(year, None):
                        if row[1] == 1:
                            historico[year]['valor_venda'] = historico[year].get('valor_venda', 0) + row[2]
                        else:
                            historico[year]['valor_resgate'] = historico[year].get('valor_resgate', 0) + row[2]
                    else:
                        if row[1] == 1:
                            historico[year] = {'valor_venda': row[2]}
                        else:
                            historico[year] = {'valor_resgate': row[2]}
                historico_list = []
                for k, v in historico.items():
                    h = {'ano': k}
                    h.update(v)
                    historico_list.append(h)
            else:
                select = f'''SELECT date, action, value FROM monetary_value
                        WHERE category = {params['id']} {date_greater_then} {date_lower_then}
                        ORDER BY date'''
                cur.execute(select)
                historico_list = []
                for row in cur:
                    year = row[0].year
                    month = row[0].month
                    for h in historico_list:
                        if h.get('ano', None) == year:
                            if h.get('mes', None) == month:
                                if row[1] == 1:
                                    h['valor_venda'] = row[2]
                                else:
                                    h['valor_resgate'] = row[2]
                                break
                    else:
                        h = {'mes': month, 'ano': year}
                        if row[1] == 1:
                            h['valor_venda'] = row[2]
                        else:
                            h['valor_resgate'] = row[2]
                        historico_list.append(h)
            response['historico'] = historico_list
            self._set_response()
            self.wfile.write(json.dumps(response).encode('utf-8'))



def run(server_class=HTTPServer, handler_class=S, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting server at localhost:%s...\n', port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping server...\n')
    conn.close()

def get_cursor():
    return conn.cursor()

def commit():
    conn.commit()

def prepare_database(cur):
    '''
    Verifies if the tables already exist, if not, create and populate them.
    '''

    file = 'series_tesourodireto.xlsx'
    xl = pd.ExcelFile(file)
    df = xl.parse('Planilha1')

    select_table = "SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name=%s)"

    # Category table
    cur.execute(select_table, ('category',))
    if not cur.fetchone()[0]:
        cur.execute("CREATE TABLE category (id serial PRIMARY KEY, title VARCHAR (50) UNIQUE NOT NULL)")
        for data in df.iloc[5, 2:]:
            name = data.split('Tesouro Direto - ')[-1]
            cur.execute('''INSERT INTO category(title) SELECT '%s'
                        WHERE NOT EXISTS (
                            SELECT id FROM category WHERE title = '%s'
                        )''' % (name, name))
            conn.commit()

    # Monetary Value table
    cur.execute(select_table, ('monetary_value',))
    if not cur.fetchone()[0]:
        cur.execute('''CREATE TABLE monetary_value (
                            category INTEGER NOT NULL, 
                            date DATE NOT NULL, action SMALLINT NOT NULL,
                            value float(2) NOT NULL,
                            UNIQUE (category, date, action),
                            CONSTRAINT moneraty_value_category_id_fkey FOREIGN KEY (category)
                                REFERENCES category (id) MATCH SIMPLE
                                ON DELETE CASCADE
                        )''')
        for col in range(2, df.shape[1]):
            category_data = df.iloc[5, col].split('Tesouro Direto - ')
            category_name = category_data[-1]
            cur.execute(f"SELECT id FROM category WHERE title = '{category_name}'")
            action = 0 if 'Resgates' in category_data[0] else 1
            category_id = cur.fetchone()[0]
            for row in range(12, df.shape[0]):
                cur.execute(f"INSERT INTO monetary_value VALUES ({category_id}, '{df.iloc[row, 1]}', {action}, {df.iloc[row, col]})")
                conn.commit()

if __name__ == '__main__':

    if len(argv) == 2:
        logging.basicConfig(level=argv[1])
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        conn = psycopg2.connect(host='localhost', database='historico', user='postgres', password='1928370a')
        logging.info("Connected to database.")
    except Exception as err:
        logging.critical(err)

    prepare_database(conn.cursor())
    run()

    

    
