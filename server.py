from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from sys import argv
import logging
import pandas as pd
import psycopg2


class S(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("oi amorzinho lindo request for {}".format(self.path).encode('utf-8'))
        self.fun()

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

    def fun(self):
        cur = get_cursor()
        cur.execute('SELECT * FROM monetary_value')
        for row in cur:
            self.wfile.write((str(row)+'<br>').encode('utf-8'))


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
        for data in df.iloc[4, 2:]:
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
            category_data = df.iloc[4, col].split('Tesouro Direto - ')
            category_name = category_data[-1]
            cur.execute(f"SELECT id FROM category WHERE title = '{category_name}'")
            action = 0 if 'Resgates' in category_data[0] else 1
            category_id = cur.fetchone()[0]
            for row in range(9, df.shape[0]):
                cur.execute(f"INSERT INTO monetary_value VALUES ({category_id}, '{df.iloc[row, 1]}', {action}, {df.iloc[row, col]})")
                conn.commit()

if __name__ == '__main__':

    if len(argv) == 2:
        logging.basicConfig(level=argv[1])
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        conn = psycopg2.connect(host='localhost', database='historico', user='osniellopesteixeira', password='1928370a')
        logging.info("Connected to database.")
    except Exception as err:
        logging.critical(err)

    prepare_database(conn.cursor())
    run()

    

    
