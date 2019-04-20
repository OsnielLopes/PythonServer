# TesouroAPI

## Instalação do PostgreSQL
    ### Mac
    Para a instalação usamos o HomeBrew.
    No terminal:
    ```
    brew update
    brew install postgres
    postgres -D /usr/local/var/postgres
    createdb 'historico'
    pip3 install psycopg2
    pip3 install pandas
    pip3 install xlrd
    ```
        
![Modelo Entidade Relacionamento usado para criação do banco](https://github.com/OsnielLopes/PythonServer/blob/master/er-diagram.png)

