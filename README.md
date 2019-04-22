# TesouroAPI

## Instalação, configuração e execução do projeto

Após clonar este repositório:

### Mac
    Para a instalação usamos o HomeBrew.
    No terminal:
    brew update
    brew install postgres
    postgres -D /usr/local/var/postgres
    createdb 'historico'
    pip3 install psycopg2
    pip3 install pandas
    pip3 install xlrd
    
### Windows
    Instalar o PostgreSQL: https://www.postgresql.org/download/windows/
    Abrir o PSQL (um terminal deve aparecer) e usar o seguinte comando:
    CREATE DATABASE historico;
    Abrir o prompt de comando e executar:
    pip3 install psycopg2
    pip3 install pandas
    pip3 install xlrd
    
### Configurar conexão com o banco e executar
    Abrir o arquivo server.py e alterar na linha 227 os dados de conexão com o banco, conforme tenha sido configurado.
    Rodar o arquivo server.py.



## Modelo Entidade-Relacionamento do banco de dados
![Modelo Entidade Relacionamento usado para criação do banco](https://github.com/OsnielLopes/PythonServer/blob/master/er-diagram.png)

