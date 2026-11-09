# -*- coding: utf-8 -*-
"""Opcjonalne porządki BAT po instalacji Soulbound v108 lub v109.

Domyslnie tylko sprawdza. --wykonaj wymaga recznego potwierdzenia.
Nie dotyka SQLite, plikow graczy ani dzialania serwera. Stare BAT zachowuje
w osobnym archiwum z instalacji, bez nadpisywania istniejacych plikow.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'narzedzia'/'bat_historyczne'/'z_instalacji'
ORIGINAL_SHA256={
    'ARENA_UOSS_REAL_1_DO_1.bat': 'e32d8391cb3095dd117483570fd99f389d99f0ae23d7765414549a5299971829',
    'AUDYT_V107_EQ_NA_KOPII_BAZY.bat': '0272bc226294d7725711e5afe1ae243830b51efee5c9a3aab202bc67999c8276',
    'AUDYT_V107_EQ_TRANSAKCJE_NA_KOPII.bat': 'b693d83543f7b97780c747ee5db71ebca6f65c1616e8702f818f32c7bb1e1401',
    'PROFILUJ_Soulbound.bat': '7c78534d13422fdbea71329bc9eb40afd14aa44450e91b4c3689b9e27c53d0c0',
    'SPRAWDZ_TCP_ERA_V103.bat': '23dd0108cdb910db47100a7b5edcde07879b012e8a5f345e158cb03bf88d1391',
    'SPRAWDZ_V104_ATOMOWE_LUPY_OFFLINE.bat': 'b159c5a237a90b9c26ba740398a1afcd57c4550df164188178ae68730c5e065c',
    'SPRAWDZ_V104_BIGNUMBER_KOPIA_OFFLINE.bat': '56a2ebacc5f5d4bf395226bb058720421aaf3ba84487538d79bed68603492a59',
    'SPRAWDZ_V104_BIG_NUMBER_14_OSI_OFFLINE.bat': '3cbca2af7eb93a90fff11b5fbc12d26df0524b7451b2812df16e01f640ba727a',
    'SPRAWDZ_V104_BIG_NUMBER_AKTYWNY_ZAPIS_NA_KOPII.bat': '4085f12cc2e92ae5195696c475cc40ab0d76a8e7198b6b54416292220f0762d3',
    'SPRAWDZ_V104_BIG_NUMBER_KLASY_OFFLINE.bat': '9de3d62e3c12a8727d7a565d480f91a4dfcc3f5c00f8baddf881b9111210d0ea',
    'SPRAWDZ_V104_CALOSC_OFFLINE.bat': '67bf1a927f2684ecb68195fe965d251e197e11e7533ad409f85768bf9a93543d',
    'SPRAWDZ_V104_DUZA_INTEGRACJA_2_OFFLINE.bat': '8572b416efe69e64d50982de457c061c41505a0b31cb89edf682968e1e4bb767',
    'SPRAWDZ_V104_DUZA_KONTROLA_BEZ_SIECI.bat': '3e443f577d673ef4f46e4d16798483f13c6d7e4eb21ea3aaae55046431e173b6',
    'SPRAWDZ_V104_DWA_KONTA_WALKA_TCP.bat': 'bc8cde90f158f34f4f9d3c635928b582ca6588200de59e0e38c51607f7ea8614',
    'SPRAWDZ_V104_ETAP10_OFFLINE.bat': '14b7822a1f24eb2642ddb267d91a5cb2435bae0563c746ffeab2e9a648d43dbe',
    'SPRAWDZ_V104_ETAP11_OFFLINE.bat': '16ed8959d11d6d7558088c5b26ba74c1f92bbe1e8489f0f1016bf9aa25dba8aa',
    'SPRAWDZ_V104_ETAP12_OFFLINE.bat': '1eabbe485b11efd1c5b314bf3470c097c6d999a211bd89336efc1a406e0f557d',
    'SPRAWDZ_V104_ETAP13_OFFLINE.bat': '80821a0b01579c81a60ea24ad8b21961ca6f00c2e2fa40c2028f8d60c4a069e2',
    'SPRAWDZ_V104_ETAP14_OFFLINE.bat': '6deb8d8eac7a959612af34efbd009e31443eff02ec59d13fd8e59a8d466a1091',
    'SPRAWDZ_V104_ETAP1_BIGNUMBER.bat': '9c38b447c18a36111e5488133d3029f5aa65b5033dd830ebd801b828330bbdf5',
    'SPRAWDZ_V104_ETAP2_KRAINY.bat': '7287fb4be88281bb2a600bcc0cf2bf361b50e04a9b117396420e3e4aa8a2e23e',
    'SPRAWDZ_V104_ETAP3_SOUL_TIER.bat': 'e84fdb56ce849f1f411b4fdb9c56cdc51f7dcbe7e19f0bce491185d0866e4f52',
    'SPRAWDZ_V104_ETAP4_RAJDY.bat': 'ae587a58380d09ce7b28d7086f76b34224bf4780566a3a1b85c899017d14e4a4',
    'SPRAWDZ_V104_ETAP8_OFFLINE.bat': 'ceec156e99c01c0f3c53abe5bee31fa7c3816ab841c174e68cf0fd98fb158009',
    'SPRAWDZ_V104_ETAP9_OFFLINE.bat': 'a4f53cf4af355a91b04a904163bdb5d25827cc60ee4be500bf172add045ac899',
    'SPRAWDZ_V104_JEDNYM_KLIKNIECIEM.bat': '5449f4299a1421dc8942fe26db115b102f2150787ed3748924d9ad8b582ca04c',
    'SPRAWDZ_V104_LUPY_CALEGO_ZABICIA_OFFLINE.bat': '050db669e6135e14bfa652adea05268277ca504a5b16846cd3259f80fda9fb69',
    'SPRAWDZ_V104_NOWA_INTEGRACJA_OFFLINE.bat': '1e922f892e7dd51c0110be93d6d010b7bdc78ddf888093b68fe6e1790c0230e7',
    'SPRAWDZ_V104_OFFLINE.bat': '86b7a22bb41d15c0f34312fc9e80e810cfed902fa0da73daf7454ac9fe9d9b03',
    'SPRAWDZ_V104_PROFILE_PRACA_OFFLINE.bat': '57e5758ca835c809fcc8bf9783a894d250d891fe2066e2e867328f5915962023',
    'SPRAWDZ_V104_QUESTY_OFFLINE.bat': '382d668ddd9cf2bc9dd4e7a43dc4ac5d225138ca16aa72b41d3f6d19b5e328b6',
    'SPRAWDZ_V104_RC_BEZPIECZNIE.bat': '5a60f94dc272ab11adad172438612013cb9aefbc12e4eca27a792339d2acac65',
    'SPRAWDZ_V104_RC_PRECYZJA_OFFLINE.bat': 'ba612369dfd8669ff9f32115b30cf0c9dd5218bbfed1f7b3a4c0550b2e8ce3a2',
    'SPRAWDZ_V104_ROWNOLEGLE_WALKI.bat': '7e7c41f9abd7e8e16afb4ed0bf4d5810867ff0db2a2ab4c7f4651755a7f6ea0b',
    'SPRAWDZ_V104_RZEMIOSLO_BEZ_STRAT.bat': 'a23a2d7782099c9e8247c2afed1394705c0b8d1997091b8c20ba4ab6d18721bb',
    'SPRAWDZ_V104_START_TCP_DIAGNOSTYKA.bat': '387a6692b52c43b5f8734cecc8190d54ea52d8895c184fac8b869323b464d499',
    'SPRAWDZ_V104_WALUTA_STATY_OFFLINE.bat': '4c238d74a779f05eff7849b4e5a9954465ca46a35366a60ba3b138e2d168a36a',
    'SPRAWDZ_V104_WALUTY_BIGNUMBER_KOPIA.bat': '6e8602af9052cd52e7390bdb7a12560d18d4e858bf9d1652cda4802bb0d8a696',
    'SPRAWDZ_V104_WYDANIE_RC_OFFLINE.bat': '6810198ea2925b69ac4cf787d3f3f50811218d8e5e32f7fbea14a6beca06609d',
    'SPRAWDZ_V104_ZGODNOSC_SKILLI_OFFLINE.bat': '0b4330ec26a15818ace13f07c3560924c58da71208f57078679034925b56211d',
    'SPRAWDZ_V105_MIGRACJE_NA_KOPII_BAZY.bat': '033e70169ef0757fd15b5b442b6e8724f41f8e334b7b8bcb4cfbd60783b1cab5',
    'SPRAWDZ_V105_TCP_NOWE_KRAINY.bat': '42078624728327ce0db146066c38cf2a51f40dbd8be172c3ea03639460d2a21c',
    'SPRAWDZ_V106_EQ_NA_KOPII.bat': '4da28bc64f8fdf3d8836d42f07f108491172ba0cfe7dad489e2c152047388501',
    'SPRAWDZ_V107_MAGITEK_KOD_ROBOCZY.bat': '072e1207fbdc073066f94941e948245c9026a85550fb94a1568be8828ab88eb1',
    'STRESS_TCP_Soulbound.bat': '859b69e523705353de14a4f52642c81bbc8622c89f0b68136fd17247c004c05b',
    'TESTUJ_V106_KOD_ROBOCZY_OFFLINE.bat': 'e304c69b9654120c4819ba8db81e152e9551aa1a9115010f65f6ab4dc4daa922',
    'TESTUJ_V106_TCP_5_GRACZY_OFFLINE.bat': '247ad2bc83a6f78eb16bd7f65be7353b0d94a3c3ad46f066b876b26ce668c523',
    'TESTUJ_V106_WSZYSTKO_JEDNYM_KLIKNIECIEM.bat': 'ffb45e7344298b85668a8045bb8f481132d9dd3410abbac603e1b76730e3a7a4',
    'TESTUJ_V106_WSZYSTKO_OFFLINE.bat': '9b31ff236d14dbd15e5358d5afed6cd3d393e258a0e002e8d15419c42f3b8994',
    'TEST_V104_BEZPIECZNY_OFFLINE.bat': '4a399c42448b4c9af0577bc3ec3a81603e98f2a3a81d77c7f669ea288697f1e7',
    'WDROZ_V107_PO_PREDEPLOY_Z_KANDYDATA.bat': '0b0e22aa8ad79a890cf889ad2555c74702dfb29b8f61c55461801e8c676eb7a7',
}


def plan(root=ROOT):
    root=Path(root)
    out=[]
    for name,expected in ORIGINAL_SHA256.items():
        source=root/name
        if not source.is_file() or source.is_symlink():
            continue
        realhash=hashlib.sha256(source.read_bytes()).hexdigest()
        out.append((name, 'PRZENIES' if realhash==expected else 'POMIN_ZMIENIONY'))
    return out


def cleanup(root=ROOT, *, execute=False):
    root=Path(root)
    if execute and (root/'VERSION').read_text(encoding='utf-8-sig').strip() not in ('108.00.0', '109.00.0'):
        raise RuntimeError('Porzadki tylko po instalacji v108/v109, nie na starszej wersji')
    planned=plan(root)
    if execute:
        target=root/'narzedzia'/'bat_historyczne'/'z_instalacji'
        for name,status in planned:
            if status!='PRZENIES':
                continue
            source=root/name
            # Existing archive is never overwritten or replaced.
            dest=target/name
            if dest.exists():
                continue
            target.mkdir(parents=True, exist_ok=True)
            if source.is_symlink() or hashlib.sha256(source.read_bytes()).hexdigest()!=ORIGINAL_SHA256[name]:
                continue
            os.rename(source,dest)
    return planned


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ['--sprawdz'],['--wykonaj']):
        print('Uzycie: PORZADKI_BAT_Soulbound.bat [--sprawdz | --wykonaj]')
        return 2
    execute=args==['--wykonaj']
    if execute:
        answer=input('Wpisz PORZADKUJ BAT aby przeniesc znane historyczne BAT: ').strip()
        if answer!='PORZADKUJ BAT':
            print('Anulowano, nic nie zmieniono.')
            return 2
    try:
        planned=cleanup(execute=execute)
    except (OSError, RuntimeError) as exc:
        print('Nie wykonano porzadkow: '+str(exc)); return 2
    ready=sum(state=='PRZENIES' for _,state in planned)
    changed=sum(state=='POMIN_ZMIENIONY' for _,state in planned)
    print(('PRZENIESIONO' if execute else 'DO PRZENIESIENIA')+': '+str(ready))
    print('POMINIETO, BO ZMIENIONE PRZEZ UZYTKOWNIKA: '+str(changed))
    if not execute: print('Tryb tylko do odczytu. --wykonaj wymaga potwierdzenia i v108/v109.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
