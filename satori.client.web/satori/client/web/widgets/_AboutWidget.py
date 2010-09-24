from _Widget import Widget

#Temporary - just to show how it can be used
EXAMPLERSTTXT = """
Nazwa problemu
==============

Przy Okraglym Stole zasiada :math:`n` rycerzy, numerowanych od :math:`0` do :math:`n-1`. Kazdy z nich jest charakteryzowany przez swoja **walecznosc**, bedaca liczba calkowita, niekoniecznie dodatnia (niestety...). 
Tradycja nakazuje, aby na trudne i niebezpieczne misje wysylac pewien spojny fragment Okraglego Stolu -- innymi slowy, wybiera sie pewien luk Stolu i wszystkich rycerzy siedzacych na tym luku. 
Krol Artur oczywiscie chcialby wiedziec, jaka jest najwieksza sumaryczna walecznosc druzyny, ktora moze zgromadzic. Czasami druzyna moze skladac sie ze wszystkich rycerzy Okraglego Stolu, moze tak sie tez zdarzyc, ze oplaca sie nie wysylac zupelnie nikogo (jak juz maja cos popsuc, lepiej niech siedza w domu).

Oczywiscie zawod rycerza nie jest latwy, a oczekiwana dlugosc zycia nie bije rekordow. Co jakis czas ktoregos z nich spotyka chwalebny koniec -- jest wtedy zastepowany innym, co moze wplynac na wartosc bojowa calej druzyny.

Rozstrzygnij, jaka jest najlepsza wartosc druzyny na poczatku oraz po kazdej zmianie w skladzie Okraglego Stolu.

.. note::
   Waznym jest zeby cos zauwazyc!

Wejscie
-------
Pierwsza linia zestawu zawiera liczbe naturalna :math:`n` (:math:`1\le n\le 200\,000`) -- liczbe rycerzy Okraglego Stolu. Druga linia to :math:`n` oddzielonych spacjami liczb calkowitych (na modul nie wiekszych niz :math:`10^9`) oznaczajacych walecznosci kolejnych rycerzy. Trzecia linia zawiera liczbe calkowita :math:`m` (:math:`1\le m\le 200\,000`) -- liczbe zmian w skladzie Okraglego Stolu.
W kolejnych :math:`m` liniach znajduja sie pary liczb :math:`k`, :math:`a` -- kazda para oznacza, ze rycerz o numerze :math:`k` polegl i zostal zastapiony innym, o walecznosci :math:`a` (:math:`|a| \leq 10^9`).

::

    3
    7
    2 -6 3 -8 -2 7 4
    5
    5 1
    3 6
    0 7
    3 -3
    2 0
    1
    0
    2
    0 1
    0 -1
    8
    1 1 1 1 1 -1 -1 1
    4
    2 -1
    6 1
    5 1
    1 -1

Wyjscie
-------
Dla kazdego zestawu na wyjscie wypisz :math:`m+1` liczb -- najwieksza wartosc spojnej druzyny na poczatku i po kazdej zmianie rycerza.

::

    13
    7
    14
    19
    12
    12
    0
    1
    0
    6
    4
    5
    7
    6

"""

from satori.client.web.sphinx.translator import rendertask
from satori.client.web.urls import PROJECT_PATH
# about table (to test ajah)
class AboutWidget(Widget):
    pathName = 'about'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/about.html'
        import os
        self.task = rendertask( EXAMPLERSTTXT, os.path.join(PROJECT_PATH, 'files'), 'files')

