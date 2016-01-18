# -*- coding: utf-8 -*-

import sqlite3


db_path = 'konto_internetowe.db'
conn = sqlite3.connect(db_path)

c = conn.cursor()
#
# Tabele
#

#c.execute('''
#        DROP TABLE if exists Transakcje
#        ''')
#c.execute('''
#        DROP TABLE if exists Rachunek
#        ''')

c.execute('''
        CREATE TABLE Rachunek
        ( id INTEGER PRIMAR KEY,
          imie VARCHAR(100) NOT NULL,
          nazwisko VARCHAR(100) NOT NULL,
          nr_konta VARCHAR(26)
        )
          ''')


c.execute('''
          CREATE TABLE Transakcje (
            id INTEGER NOT NULL,
            id_rachunek INTEGER,
            kontrahent_nr_rachunku VARCHAR(26) NULL,
            data_operacji DATE NULL,
            kwota_transakcji DECIMAL(10,2) NULL,
            FOREIGN KEY(id_rachunek) REFERENCES Rachunek(id),
            PRIMARY KEY(id)
          )
          ''')
