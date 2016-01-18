# -*- coding: utf-8 -*-

import repository
import sqlite3
import unittest

db_path = 'konto_internetowe.db'

class RepositoryTest(unittest.TestCase):

    def setUp(self):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('DELETE FROM Transakcje')
        c.execute('DELETE FROM Rachunek')
        c.execute('''INSERT INTO Rachunek (id, imie, nazwisko, nr_konta) VALUES(1, 'Jan','Kowalski','1111111111111111711111114')''')
        c.execute('''INSERT INTO Transakcje (id, id_rachunek, kontrahent_nr_rachunku, data_operacji, kwota_transakcji) VALUES(1, 1,'111111111111111141111111', '2015-09-17', 500.70)''')
        c.execute('''INSERT INTO Transakcje (id, id_rachunek, kontrahent_nr_rachunku, data_operacji, kwota_transakcji) VALUES(2,1,'1111111111111111111111112', '2015-09-02',100.80)''')
        conn.commit()
        conn.close()

    def tearDown(self):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('DELETE FROM Transakcje')
        c.execute('DELETE FROM Rachunek')
        conn.commit()
        conn.close()

    def testGetByIdInstance(self):
        rachunek = repository.RachunekRepository().getById(1)
        self.assertIsInstance(rachunek, repository.Rachunek, "Objekt nie jest klasy Rachunek")

    def testGetByIdNotFound(self):
        self.assertEqual(repository.RachunekRepository().getById(22),
                None, "Powinno wyjść None")

    def testGetByIdInvitemsLen(self):
        self.assertEqual(len(repository.RachunekRepository().getById(1).trans_items),
                2, "Powinno wyjść 2")

    def testDeleteNotFound(self):
        self.assertRaises(repository.RepositoryException,
                repository.RachunekRepository().delete, 22)



if __name__ == "__main__":
    unittest.main()
