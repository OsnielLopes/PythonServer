# TesouroAPI

## Instalação do PostgreSQL
### Mac -> Via HomeBrew
   
   No terminal:
    
        virtualenv env (dentro da pasta do projeto)
        source env/bin/activate
        brew update
        brew install postgres
        postgres -D /usr/local/var/postgres
        createdb 'historico'
        pip3 install psycopg2
        ![Modelo Entidade Relacionamento usado para criação do banco](https://github.com/OsnielLopes/PythonServer/blob/master/er-diagram.png)
