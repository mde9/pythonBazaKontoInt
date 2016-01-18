# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

from scipy import stats
from scipy.stats import norm

import numpy as np
import matplotlib.pyplot as plt
#
# Ścieżka połączenia z bazą danych
#
db_path = 'konto_internetowe.db'

#
# Wyjątek używany w repozytorium
#
class RepositoryException(Exception):
    def __init__(self, message, *errors):
        Exception.__init__(self, message)
        self.errors = errors

#
# Model danych
#
class Rachunek():
    """Model pojedynczej faktury
    """
    def __init__(self, id, imie='', nazwisko='', nr_konta='',trans_items=[]):
        self.id = id
        self.imie  = imie
        self.nazwisko = nazwisko
        self.nr_konta = nr_konta
        self.trans_items = trans_items


    def __repr__(self):
        return "<Rachunek(id='%s', imie='%s', nazwisko='%s', nr_konta='%s',items='%s')>\n" % (
                    self.id, self.imie, self.nazwisko, self.nr_konta, self.trans_items
                )


class Transakcje ():
    """Model pozycji na fakturze. Występuje tylko wewnątrz obiektu Invoice.
    """
    def __init__(self, id, id_rachunek, kontrahent_nr_rachunku, data_operacji, kwota_transakcji):
        self.id = id
        self.id_rachunek= id_rachunek
        self.kontrahent_nr_rachunku = kontrahent_nr_rachunku
        self.data_operacji = data_operacji
        self.kwota_transakcji = kwota_transakcji

    def __repr__(self):
        return "<Transakcje (id='%s', id_rachunek='%s', kontrahent_nr_rachunku='%s', data_operacji='%s', kwota_transakcji='%s')>\n" % (
                    self.id, self.id_rachunek, self.kontrahent_nr_rachunku, str(self.data_operacji), str(self.kwota_transakcji)
                )


#
# Klasa bazowa repozytorium
#
class Repository():
    def __init__(self):
        try:
            self.conn = self.get_connection()
        except Exception as e:
            raise RepositoryException('GET CONNECTION:', *e.args)
        self._complete = False

    # wejście do with ... as ...
    def __enter__(self):
        return self

    # wyjście z with ... as ...
    def __exit__(self, type_, value, traceback):
        self.close()

    def complete(self):
        self._complete = True

    def get_connection(self):
        return sqlite3.connect(db_path)

    def close(self):
        if self.conn:
            try:
                if self._complete:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            except Exception as e:
                raise RepositoryException(*e.args)
            finally:
                try:
                    self.conn.close()
                except Exception as e:
                    raise RepositoryException(*e.args)

#
# repozytorium obiektow typu Rachunek
#
class RachunekRepository(Repository):

    def add(self, rachunek):
        """Metoda dodaje pojedynczą fakturę do bazy danych,
        wraz ze wszystkimi jej pozycjami.
        """
        try:
            c = self.conn.cursor()

            c.execute('INSERT INTO Rachunek (id, imie, nazwisko, nr_konta) VALUES(?, ?, ?, ?)',
                        (rachunek.id, rachunek.imie, rachunek.nazwisko, rachunek.nr_konta)
                    )
            if rachunek.trans_items:
                for trans_item in rachunek.trans_items:
                    try:
                        c.execute('INSERT INTO Transakcje (id, id_rachunek, kontrahent_nr_rachunku, data_operacji, kwota_transakcji) VALUES(?,?,?,?,?)',
                                        (trans_item.id, rachunek.id, trans_item.kontrahent_nr_rachunku, trans_item.data_operacji, trans_item.kwota_transakcji)
                                )
                    except Exception as e:
                        #print "item add error:", e
                        raise RepositoryException('error adding rachunek item: %s, to rachunek: %s' %
                                                    (str(trans_item), str(rachunek.id))
                                                )


        except Exception as e:
            #print "invoice add error:", e
            raise RepositoryException('error adding rachunek %s' % str(rachunek))

    def delete(self, rachunek):
        """Metoda usuwa pojedynczą fakturę z bazy danych,
        wraz ze wszystkimi jej pozycjami.
        """
        try:
            c = self.conn.cursor()

            c.execute('DELETE FROM Transakcje WHERE id_rachunek=?', (rachunek.id,))

            # usuń nagłowek
            c.execute('DELETE FROM Rachunek WHERE id=?', (rachunek.id,))

        except Exception as e:
            #print "invoice delete error:", e
            raise RepositoryException('error deleting rachunek %s' % str(rachunek))

    def getById(self, id):
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM Rachunek WHERE id=?", (id,))
            inv_row = c.fetchone()
            rachunek = Rachunek(id=id)
            if inv_row == None:
                rachunek=None
            else:
                rachunek.imie = inv_row[1]
                rachunek.nazwisko = inv_row[2]
                rachunek.nr_konta = inv_row[3]
                c.execute("SELECT * FROM Transakcje WHERE id_rachunek=? order by data_operacji", (id,))
                trans_item_rows = c.fetchall()
                items_list = []
                for item_row in trans_item_rows:
                     item = Transakcje(id=item_row[0], id_rachunek=item_row[1], kontrahent_nr_rachunku=item_row[2], data_operacji=item_row[3], kwota_transakcji=item_row[4])
                     items_list.append(item)
                rachunek.trans_items=items_list
        except Exception as e:
            print "rachunek getById error:", e
            raise RepositoryException('error getting by id id_rachunek: %s' % str(id))
        return rachunek
    def getAllTransactions(self):
        try:
            c=self.conn.cursor()
            c.execute("SELECT kwota_transakcji FROM Transakcje order by data_operacji")
            trans_item_rows = c.fetchall()
            items_list = []
            for item_row in trans_item_rows:
                 items_list.append(item_row[0])
        except Exception as e:
             print "getAllTransactions error:", e

        return items_list

    def update(self, rachunek):
        """Metoda uaktualnia pojedynczą fakturę w bazie danych,
        wraz ze wszystkimi jej pozycjami.
        """
        try:

            rach_oryg = self.getById(rachunek.id)
            if rach_oryg != None:

                self.delete(rachunek)
            self.add(rachunek)

        except Exception as e:
            #print "invoice update error:", e
            raise RepositoryException('error updating rachunek %s' % str(rachunek))





if __name__ == '__main__':
    try:
        with RachunekRepository() as rachunek_repository:
            rachunek_repository.add(
                Rachunek(id=1, imie = 'Jan', nazwisko = 'Kowalski', nr_konta = '11111111111111111111111111',
                    trans_items = [
                        Transakcje(id=1, id_rachunek=1, kontrahent_nr_rachunku='1111111111111111111111114', data_operacji='2015-08-11', kwota_transakcji= 45.80),
                        Transakcje(id=2, id_rachunek=1, kontrahent_nr_rachunku='1111111111111111111111111', data_operacji='2015-09-17', kwota_transakcji= 500.70),
                        Transakcje(id=3, id_rachunek=1, kontrahent_nr_rachunku='1111111111111111111113456', data_operacji='2015-12-07', kwota_transakcji= 78.80),
                        ]
                )
            )
            rachunek_repository.complete()
    except RepositoryException as e:
        print(e)

    print RachunekRepository().getById(1)


    try:
        with RachunekRepository() as rachunek_repository:
            rachunek_repository.add(
                Rachunek(id=2, imie = 'Karolina', nazwisko = 'Nowak', nr_konta = '11111111111111111111111112',
                    trans_items = [
                        Transakcje(id=4, id_rachunek=2, kontrahent_nr_rachunku='1111111111111111111111114', data_operacji='2015-06-07', kwota_transakcji= 49.90),
                        Transakcje(id=5, id_rachunek=2, kontrahent_nr_rachunku='1111111111111111111111112', data_operacji='2015-09-02', kwota_transakcji= 100.80),
                        Transakcje(id=6, id_rachunek=2, kontrahent_nr_rachunku='1111111111111111111113456', data_operacji='2015-11-07', kwota_transakcji= 400.50),
                    ]
                )
            )
            rachunek_repository.complete()
    except RepositoryException as e:
        print(e)
    print RachunekRepository().getById(2)

    try:
        with RachunekRepository() as rachunek_repository:
            rachunek_repository.add(
                Rachunek(id=3, imie = 'Dorota', nazwisko = 'Dymek', nr_konta = '11111111111111111111111134',
                    trans_items = [
                        Transakcje(id=7, id_rachunek=3, kontrahent_nr_rachunku='1111111111111111111111117', data_operacji='2015-10-27', kwota_transakcji= 454.80),
                        Transakcje(id=8, id_rachunek=3, kontrahent_nr_rachunku='1111111111111111111111113', data_operacji='2015-11-07', kwota_transakcji= 200.70),
                        Transakcje(id=9, id_rachunek=3, kontrahent_nr_rachunku='1111111111111111111123456', data_operacji='2015-12-12', kwota_transakcji= 400.80),
                    ]
                )
            )
            rachunek_repository.complete()
    except RepositoryException as e:
        print(e)

    print RachunekRepository().getById(3)
    items = RachunekRepository().getAllTransactions()
    #kwoty wszystkich transakcji
    for item in items:
        print item

    mu=np.mean (items)
    sigma=np.std(items, ddof=1)
    print 'srednia:', mu
    print 'odch.standardowe:',sigma

    n, (smin, smax), sm, sv, ss, sk = stats.describe(items)
    #n, (smin, smax), sm, sv, ss, sk = stats.describe([1,2,3])

    sstr = 'mean = %6.4f, variance = %6.4f, skew = %6.4f, kurtosis = %6.4f'

    print 'sample params:'
    print sstr %(sm, sv, ss, sk)

    count, bins, ignored = plt.hist(items)
    plt.plot(bins, 1/(sigma * np.sqrt(2 * np.pi)) *
                    np.exp( - (bins - mu)**2 / (2 * sigma**2) ),
              linewidth=2, color='r')
    plt.grid(True)
    plt.show()



    ######################################
    # try:
    #     with RachunekRepository() as rachunek_repository:
    #         rachunek_repository.delete( Rachunek(id = 1) )
    #         rachunek_repository.complete()
    # except RepositoryException as e:
    #     print(e)
