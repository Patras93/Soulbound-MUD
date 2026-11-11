"""NPCS: historyczna czesc 1, wpisy 1-23.
Bez zmiany ID, wartosci i kolejnosci wpisow.
"""

def build_catalog():
    return {'soul_hunter_master_v1225': {'name': 'Mistrzyni Łowców Aria',
                              'room': 'soul_hunter_board_v1225',
                              'dialogue': 'Zwykłe potwory, elity i bossowie. Każdy kontrakt odnawia się po '
                                          'określonym czasie. Wpisz lowcy.',
                              'v1225_city_service': True},
 'fisher_tomas': {'name': 'Rybak Borys',
                  'room': 'fish_market',
                  'rank_profession': 'Wędkarstwo',
                  'dialogue': 'Jeśli naprawdę chcesz zostać wędkarzem, przynieś mi trzydzieści ryb.',
                  'quest': 'fisher_30_fish'},
 'lumberjack_bran': {'name': 'Drwal Bran',
                     'room': 'lumberjack_camp',
                     'rank_profession': 'Drwalstwo',
                     'dialogue': 'Piłę kupisz tylko tutaj. Jeśli chcesz sprawdzić się jako drwal, przynieś '
                                 'mi trzydzieści sztuk dowolnego drewna.',
                     'quest': 'lumberjack_30_wood'},
 'herbalist_liora': {'name': 'Zielarka Liora',
                     'room': 'herbalist_hut',
                     'rank_profession': 'Zielarstwo',
                     'dialogue': 'Kupisz u mnie Sierp Zielarski i Moździerz Alchemiczny. Przynieś mi '
                                 'trzydzieści dowolnych ziół, a wynagrodzę twoją pracę.',
                     'quest': 'herbalist_30_herbs'},
 'miner_toren': {'name': 'Górnik Toren',
                 'room': 'cave_entrance',
                 'rank_profession': 'Górnictwo',
                 'dialogue': 'Dobra ruda nie wydobędzie się sama. Tylko u mnie kupisz podstawowy Kilof. '
                             'Wpisz list albo shop, aby zobaczyć ofertę. Przynieś mi trzydzieści sztuk '
                             'dowolnej rudy z kopalni.',
                 'quest': 'miner_30_ore',
                 'shopkeeper': True},
 'specialist_fishing': {'name': 'Mistrz Wędkarstwa Neris',
                        'room': 'fish_market',
                        'rank_profession': 'Wędkarstwo',
                        'dialogue': 'Specjalizuję się w Wędkarstwie i rozwoju Wędki. Pokażę ci aktualny '
                                    'level narzędzia, Tier i drogę do następnego progu.',
                        'specialist_tool_type': 'fishing',
                        'specialist_topic': 'wedkarstwo'},
 'specialist_mining': {'name': 'Mistrz Górnictwa Kordan',
                       'room': 'cave_entrance',
                       'rank_profession': 'Górnictwo',
                       'dialogue': 'Specjalizuję się w Górnictwie i rozwoju Kilofa. Im wyższy level Kilofa, '
                                   'tym lepsze rudy możesz wydobywać.',
                       'specialist_tool_type': 'mining',
                       'specialist_topic': 'gornictwo'},
 'specialist_woodcutting': {'name': 'Mistrz Drwalstwa Oren',
                            'room': 'lumberjack_camp',
                            'rank_profession': 'Drwalstwo',
                            'dialogue': 'Specjalizuję się w Drwalstwie i rozwoju Piły. Wyższe levele '
                                        'otwierają dostęp do coraz rzadszych gatunków drewna.',
                            'specialist_tool_type': 'woodcutting',
                            'specialist_topic': 'drwalstwo'},
 'specialist_crafting': {'name': 'Mistrz Rzemiosła Haldor',
                         'room': 'forge',
                         'rank_profession': 'Kowalstwo',
                         'dialogue': 'Specjalizuję się w Kowalstwie, Rzemiośle i Młocie Rzemieślniczym. W '
                                     'Kuźni możesz przetapiać rudy, kuć pancerze i wykonywać powtarzalne '
                                     'zlecenia odnawiane co godzinę.',
                         'specialist_tool_type': 'crafting',
                         'specialist_topic': 'kowalstwo',
                         'specialist_recipes': 'receptury kowalstwo',
                         'quest': 'haldor_crafting_order',
                         'specialist_quests': ('haldor_crafting_order',
                                               'haldor_crafting_order_advanced',
                                               'haldor_crafting_order_master')},
 'specialist_cooking': {'name': 'Kucharz Marcel',
                        'room': 'inn',
                        'rank_profession': 'Gotowanie',
                        'dialogue': 'Jestem Kucharzem Błękitnego Płomienia. Pomogę ci rozwijać Nóż Kucharski '
                                    'i korzystać z receptur Gotowania.',
                        'specialist_tool_type': 'cooking',
                        'specialist_topic': 'gotowanie',
                        'specialist_recipes': 'receptury cook',
                        'quest': 'marcel_cooking_order',
                        'specialist_quests': ('marcel_cooking_order',
                                              'marcel_cooking_order_advanced',
                                              'marcel_cooking_order_master')},
 'specialist_herbalism': {'name': 'Mistrzyni Zielarstwa Sena',
                          'room': 'herbalist_hut',
                          'rank_profession': 'Zielarstwo',
                          'dialogue': 'Specjalizuję się w Zielarstwie i rozwoju Sierpa Zielarskiego. Wysoki '
                                      'level Sierpa pozwala zbierać najrzadsze zioła.',
                          'specialist_tool_type': 'herbalism',
                          'specialist_topic': 'zielarstwo'},
 'specialist_alchemy': {'name': 'Mistrz Alchemii Orin',
                        'room': 'herbalist_hut',
                        'rank_profession': 'Alchemia',
                        'dialogue': 'Specjalizuję się w Alchemii i Moździerzu Alchemicznym. Mam jedenaście '
                                    'poziomów zleceń na mikstury i eliksiry, od podstawowej Many aż do '
                                    'Eliksiru Wiecznej Duszy.',
                        'specialist_tool_type': 'alchemy',
                        'specialist_topic': 'alchemia',
                        'specialist_recipes': 'receptury alchemia',
                        'quest': 'orin_alchemy_order',
                        'specialist_quests': ('orin_alchemy_order',
                                              'orin_alchemy_order_healing',
                                              'orin_alchemy_order_greater_healing',
                                              'orin_alchemy_order_greater_mana',
                                              'orin_alchemy_order_vitality',
                                              'orin_alchemy_order_advanced',
                                              'orin_alchemy_order_supreme_mana',
                                              'orin_alchemy_order_grand_vitality',
                                              'orin_alchemy_order_soul_tonic',
                                              'orin_alchemy_order_astral_restoration',
                                              'orin_alchemy_order_master')},
 'specialist_archaeology': {'name': 'Archeolożka Elara',
                            'room': 'library',
                            'rank_profession': 'Archeologia',
                            'dialogue': 'Prowadzę badania ruin, krypt, cmentarzy, świątyń i dawnych '
                                        'archiwów. Pędzel Archeologa kupujesz u mnie tylko raz na postać. W '
                                        'terenie używaj wykop, a archeologia pokazuje postęp i kolekcję '
                                        'znalezisk.',
                            'specialist_tool_type': 'archaeology',
                            'specialist_topic': 'archeologia',
                            'strict_profession_quests': 'Archeologia',
                            'shopkeeper': True},
 'specialist_cartography': {'name': 'Mistrzyni Kartografii Alena',
                            'room': 'v016_cartographers_archive',
                            'rank_profession': 'Kartografia',
                            'dialogue': 'Dokumentujemy cały świat: miasta, rubieże, lochy, wyspy i sektory '
                                        'proceduralne. Kompas Mierniczy kupujesz tylko raz na postać. Używaj '
                                        'mapuj w odwiedzanych lokacjach, aby rozwijać Kartografię 1-600.',
                            'specialist_tool_type': 'cartography_profession',
                            'specialist_topic': 'kartografia',
                            'strict_profession_quests': 'Kartografia',
                            'shopkeeper': True},
 'banker_aldren': {'name': 'Bankier Aldren',
                   'room': 'market',
                   'dialogue': 'Prowadzę Bank Dusz. Możesz zdeponować walutę i przedmioty, a wszystko '
                               'pozostanie bezpieczne po wylogowaniu.',
                   'quest': None,
                   'banker': True},
 'market_trader_radan': {'name': 'Handlarz Skupu Radan',
                         'room': 'market',
                         'dialogue': 'Skupuję zwykłe łupy z potworów, trofea oraz niezałożone wyposażenie. '
                                     'Sell nazwa sprzedaje wskazany przedmiot, ale sell all sprzedaje '
                                     'wyłącznie niezałożone EQ. Nie kupuję ryb, rud, minerałów, drewna, ziół '
                                     'ani innych materiałów rzemieślniczych. Nie kupuję też narzędzi, '
                                     'przedmiotów questowych ani EQ, które masz aktualnie założone.',
                         'quest': None,
                         'shopkeeper': True,
                         'buyback_trader': True},
 'priest_elor': {'name': 'Kapłan Elor',
                 'room': 'temple',
                 'dialogue': 'Próby Broni Duszy są od T10 do T3000, zawsze co 10 Tierów. Pokazuję najwyżej '
                             'dziesięć kolejnych Prób, aby NVDA czytał krótką listę. Wpisz quest list Kapłan '
                             'Elor. Aby przejrzeć dalsze progi, wpisz quest list Elor 81, quest list Elor '
                             '1001 lub quest list Elor 2001. Przyjmij próbę, wykonaj cel w Krypcie i oddaj '
                             'ją u mnie; potem wpisz unlock.',
                 'quest': 'temple_rats'},
 'captain_arven': {'name': 'Kapitan Arven',
                   'room': 'guard_hall',
                   'dialogue': 'Gobliny zajęły starą strażnicę. Potrzebujemy kogoś, kto oczyści szlak.',
                   'quest': 'goblin_problem'},
 'north_gate_guard_oskar': {'name': 'Strażnik Oskar',
                            'room': 'north_gate',
                            'dialogue': 'Północna brama jest pod stałą ochroną. Za murami zaczyna się Stary '
                                        'Trakt, więc przed wyjściem sprawdź ekwipunek i aktywne questy.',
                            'quest': None},
 'north_gate_guard_marta': {'name': 'Strażniczka Marta',
                            'room': 'north_gate',
                            'dialogue': 'Wracających ze Starego Traktu sprawdzamy po każdym alarmie. Jeżeli '
                                        'szukasz zleceń straży, Kapitan Arven czeka w Strażnicy Głównej.',
                            'quest': None},
 'south_gate_guard_lena': {'name': 'Strażniczka Lena',
                           'room': 'south_gate',
                           'dialogue': 'Na południu zaczynają się łąki i Gaj Szeptów. Wilki potrafią podejść '
                                       'blisko traktu, więc nie ignoruj ostrzeżeń z dziczy.',
                           'quest': None},
 'south_gate_guard_branek': {'name': 'Strażnik Branek',
                             'room': 'south_gate',
                             'dialogue': 'Pilnujemy tej bramy całą dobę. Jeśli wracasz ranny, Świątynia '
                                         'Odrodzenia jest w centrum miasta.',
                             'quest': None},
 'guard_quartermaster_harek': {'name': 'Kwatermistrz Harek',
                               'room': 'guard_armory',
                               'dialogue': 'Każda tarcza i włócznia ma swój numer. Zbrojownia zaopatruje '
                                           'obie bramy i patrole miejskie.',
                               'quest': None}}
