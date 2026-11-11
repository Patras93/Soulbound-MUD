# -*- coding: utf-8 -*-
"""v110: retire only certified obsolete v109 files after full code backup.

Hashes are derived from the previously Windows-certified v109 ZIP. A modified
file is NEVER removed. No game data, logs or player assets are affected.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

# Do not require these old files to exist; list is cleanup-only provenance.
RETIRED_V109_SHA256 = {
    'narzedzia/bat_historyczne/ARENA_UOSS_REAL_1_DO_1.bat': '8ffd1e01103545877f218b43c4dcae47d21c2743098465886ab0bed0b7b2a159',
    'narzedzia/bat_historyczne/AUDYT_V107_EQ_NA_KOPII_BAZY.bat': 'fc902758c1fbf0a4855b174664d29eeeb9d193971e6dc3e5d356181d613c531d',
    'narzedzia/bat_historyczne/AUDYT_V107_EQ_TRANSAKCJE_NA_KOPII.bat': 'd5a2429452aba620855f3858e46d952ca6643a584fd90541c05467316a536b07',
    'narzedzia/bat_historyczne/PROFILUJ_Soulbound.bat': '49a00c1e6eb519a51ed0974722345562ded8c9caa015b12b1980ebd3429e9a26',
    'narzedzia/bat_historyczne/SPRAWDZ_TCP_ERA_V103.bat': '4d6ab7a691a5aad25ed4f463e6f351f12709463b92f217690577f61e34877586',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ATOMOWE_LUPY_OFFLINE.bat': 'e33325cb65b417fff36305e366627faf5ba228a35b07f2dd5030c14948a388b2',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_BIGNUMBER_KOPIA_OFFLINE.bat': '21c7365bd857a1229f8fb4a904d90332530b003eb0c4903981cc4133720daca0',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_BIG_NUMBER_14_OSI_OFFLINE.bat': '7f434f885eb372d54b69a31f13dbafd183786a3b837be8a1b937e06386c98026',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_BIG_NUMBER_AKTYWNY_ZAPIS_NA_KOPII.bat': '3d5dd8c678da903c2dd7ff8a1d455a13c83ed243d99cc0385862bb64c233a700',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_BIG_NUMBER_KLASY_OFFLINE.bat': 'c74189f969c18833de99ddc7c1593d933f8fa57ef22cc0ace0cfd8b3b713c831',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_CALOSC_OFFLINE.bat': 'b99976c27af890ab1a05cfe8575ab65577c270e5733d929db25296dc260d080c',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_DUZA_INTEGRACJA_2_OFFLINE.bat': '6cef8eb22cb4589e8f157cf577a951a17643de948d892e80203589f4b8bd66c5',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_DUZA_KONTROLA_BEZ_SIECI.bat': '1f1915d4e69e5c852502dbd5717514f5692959cc62568ce31d08b782076fc58b',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_DWA_KONTA_WALKA_TCP.bat': '3119e35bf0e5553bb84adef59c22f801a67f4ee06dd3de533d5fe15f2e1768a4',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP10_OFFLINE.bat': 'c64f6e41c318c7f24cd74d758f9647e56e11019bb8c546c5f1bd2072d45f2166',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP11_OFFLINE.bat': 'eeabb1ac354ce58c3bf35320c64a52997cc85ee704626d59ecb834f828941e3a',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP12_OFFLINE.bat': '5dc36e954f01f7d03cc56cf7436ebae35a3a2a4aa51b9ddb478eccc37b13285e',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP13_OFFLINE.bat': 'bb2fc08f5a26f8d2f50a362d8e77ae5b5d861e9f89150670b0f3f156645d5508',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP14_OFFLINE.bat': '9eb7bc751a8d405316a1e0357e228ce9aa2117128b4f596eb4a56e215b04ce0b',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP1_BIGNUMBER.bat': 'cb2ae877c2c55fa05ae4008fe4a645d3faf8870a75055dc892141ef24d1473bd',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP2_KRAINY.bat': 'dc0db72503426051b7eba503f86ca6d96de79fe50cf225959dd3950557dd98f7',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP3_SOUL_TIER.bat': '1cf8a07033240799650dbad0e157af8950cdcefdef69d48d686203c4b05133b1',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP4_RAJDY.bat': '4b382443ad2de7e9ff7075998c822cd4bdb7c77e2772fcd16264dcbeb8be1ef5',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP8_OFFLINE.bat': '230ee9f18f4a9b95e2813fb6fabe7bf4f23390f467938cc8b58a59887055a1ca',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ETAP9_OFFLINE.bat': '0dbcdd86dd6c6aaad23a2aa3bdfe7c213288abb226ad1bf63d93d43fad3f9f2c',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_JEDNYM_KLIKNIECIEM.bat': '96b99dae6584392ea19aa787a5f7cbdb6f4fd88760cf6a53343b27bdc0eaa725',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_LUPY_CALEGO_ZABICIA_OFFLINE.bat': '3dc221e9eb9c9c9655c6514689046c9ae7c550fafe3a066e4d450f77ad9b9da9',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_NOWA_INTEGRACJA_OFFLINE.bat': '9aa7efdf38b9779574788ddf8dce049e7da0a5128bb847bf67fceb49982b7b24',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_OFFLINE.bat': '5f46c7d344c62db6d6f4e10db12fa95ee61b339f61826ae64f33385886bc490b',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_PROFILE_PRACA_OFFLINE.bat': 'db90c8739e26e8997d6603fef1e0e94be786b2486afdf3a3b792424f331f9c66',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_QUESTY_OFFLINE.bat': 'c0c5d6dd48e8f9fc0bfb6b44f42b283a42207a49a67bdf2b410dc8a273afc307',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_RC_BEZPIECZNIE.bat': '3ff69b1a2edf4cdd97062bd252874029e28556a41c45d37cc921364b4acfd0ec',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_RC_PRECYZJA_OFFLINE.bat': '8088d6ba34a3ea10f657345d56ffc16bb2ea45e79d4431aba91faf6589803b08',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ROWNOLEGLE_WALKI.bat': '22e1ecf6378ac5e7e750117cdb4cf8011d472f980349fe89a7c2496dd6e23514',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_RZEMIOSLO_BEZ_STRAT.bat': '987b3dbb882ceadbb6ff97c1d7fcb4455b461729540f25526e3bc92fe23e1943',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_START_TCP_DIAGNOSTYKA.bat': 'd367108710092a333509ff02239120752dd11bc4290539d801980a7b6ea2760a',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_WALUTA_STATY_OFFLINE.bat': '947020e4f2508a017b2d6657ac1a8d27c815b4d209ac917cfb10e8c17fd5df38',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_WALUTY_BIGNUMBER_KOPIA.bat': '34d3ec396fc661e7872032b3f52c082437652becdf7e839546d6199654f098a1',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_WYDANIE_RC_OFFLINE.bat': 'eaf8aaf1fda58d05a0f847fcdb69ca125be1ff87525f83ce46a00b63e69c9231',
    'narzedzia/bat_historyczne/SPRAWDZ_V104_ZGODNOSC_SKILLI_OFFLINE.bat': 'b669068670b3b8670cb261fd32b8527c5ac4733963c2f34bbd0ff308a0266e88',
    'narzedzia/bat_historyczne/SPRAWDZ_V105_MIGRACJE_NA_KOPII_BAZY.bat': 'f8ff297c7b05abb07b43b52164b56c46aa91cf340c86eadc79c0e4fe6e45c3eb',
    'narzedzia/bat_historyczne/SPRAWDZ_V105_TCP_NOWE_KRAINY.bat': '530687cc521824ab3a01d1f984a7a9d2a630cad63a1a78f02da68a3b70f19f34',
    'narzedzia/bat_historyczne/SPRAWDZ_V106_EQ_NA_KOPII.bat': 'b69b9782d82efb9bea7bcfc2430bb1efe169713c882b8eda2b1c9fc3107c09f9',
    'narzedzia/bat_historyczne/SPRAWDZ_V107_MAGITEK_KOD_ROBOCZY.bat': '442e0bb3502f0a83a5aae92bdc62a36878a5e87f02d8344ac5ed89175e0652ba',
    'narzedzia/bat_historyczne/STRESS_TCP_Soulbound.bat': '4664925fec8ceac371bb0712095dc7c55199afc2c516371bbf014b5a3aca7f79',
    'narzedzia/bat_historyczne/TESTUJ_V106_KOD_ROBOCZY_OFFLINE.bat': '54430b51c91bc12f07f0a7159e7aac4e2f991a9c85be734ca062f69348292762',
    'narzedzia/bat_historyczne/TESTUJ_V106_TCP_5_GRACZY_OFFLINE.bat': 'ec6881ab6b0aa4bf560a1aca79b992a1dfa4ce0aa0f6df9283316c7ef28831da',
    'narzedzia/bat_historyczne/TESTUJ_V106_WSZYSTKO_JEDNYM_KLIKNIECIEM.bat': '325d88fe4dbdebab484c044aaaf71dcc7247a65f1c35d07da31d58c73deba6d5',
    'narzedzia/bat_historyczne/TESTUJ_V106_WSZYSTKO_OFFLINE.bat': 'cc8b67f4b459d9c0d1fcc7495a8ebced9ac79afb1d0deb6c086c05ea7c526a4c',
    'narzedzia/bat_historyczne/TEST_V104_BEZPIECZNY_OFFLINE.bat': 'e1c7585f222376f6905399464418b7d1fc7a32e1f60a70e4fc712912384e74c1',
    'narzedzia/bat_historyczne/WDROZ_V107_PO_PREDEPLOY_Z_KANDYDATA.bat': '69125e5aaf6264d1e6dff9236222a2adbb7ba759dc1549a84acf0f6632b84a75',
    'predeploy_v108_z_zewnatrz.py': 'ea596462cef3d2ab81e7b3a367dcadbbfd7f4677a718e51447b076b52685c4b0',
    'predeploy_v109_standard_router.py': 'da2f25031bcf363e11f35f0509a7cf814a279813bcecbfef3cd3d3a4473478e4',
    'predeploy_v109_z_zewnatrz.py': 'bfac0a8c0fb1a4bc40f92e4b01dca191253efdeb1f00dcc4bf34ad96c7ade554',
    'wdroz_v107_z_zewnatrz.py': '0fbf2d8931978e65cb287c354c4ece7e61d1b7025443215b7bda84b95d805c16',
    'wdroz_v108_z_zewnatrz.py': 'dc36c3391594f22480a8e23ea5258e06228e7849fb9dedff9a0e39d991fc62a3',
    'wdroz_v109_z_zewnatrz.py': '71895b024922f8018a2806d0515bdad802cfc39ff0d6e8c991056d8189d42c3a',
}


# Exact root BATs present in the independently certified v109 ZIP. Old diagnostic
# entrypoints are not shipped in v110, but an in-place upgrade must also clean
# prior installed copies. A customized file must NEVER be deleted.
RETIRED_ROOT_BATS_V110 = {
    'AUDYT_V107_WINDOWS_PRZED_PREDEPLOY.bat': '96ba1ed9f0b73f3da52c5e4a2482b61aadf6f06ce126822285f69f4979f41c8d',
    'PORZADKI_BAT_Soulbound.bat': '80ae637e7602586a178c8e257d09d9d979e8742dc2ee594ee579e3fa033aa3f6',
    'REBUILD_EQ_V107_TYLKO_KOPIA.bat': '25ce693341f1aea35c36803d05f8b4553d488eef6d9028f49a53d8e7adb076a7',
    'SPRAWDZ_11_EQ_V107_BEZ_ZMIAN.bat': '1de0ad331e1a64ebc1c7d4e1a2bf8361a3e7064dd313648f28f3a49549104831',
    'SPRAWDZ_INNE_RAJDY_ERA_V103_TCP.bat': 'e6d91fe474e3b06bc68103686a1fb0d74fa43ac3d7c72a9c694139c4421e50f0',
    'SPRAWDZ_RAJD_ERA_V103_TCP.bat': '517d936a0079f0a872ec3770763e7fe993ee0cd6f5ca71327cc9402f15d4c680',
    'SPRAWDZ_V104_KONCOWO_WINDOWS_BEZ_WDROZENIA.bat': 'ac8a9e88d8edb8a83850305b530336553d1331c55ac2646b4f611f26aab2b580',
    'SPRAWDZ_V104_MIGRACJE_NA_KOPII_BAZY.bat': '796b7a5789f7081cef11d165fe1690f280c8206044839b931698bb0356d998d2',
    'SPRAWDZ_V108_GOTOWOSC_WYDANIA.bat': '2b682fca559444c468eaa9cb85b211dbc2c53ff53d3963122044263c27b53a41',
    'SPRAWDZ_V108_OFFLINE.bat': '284f97fe07188443b3de9a40d4fe2bb3861179136845c616885cf889b603ab76',
}
RETIRED_V109_SHA256.update(RETIRED_ROOT_BATS_V110)
# Eight historical diagnostics excluded from v110 after dependency/regression
# audits. SHA256 copied from the same certified v109 ZIP as the BAT entries.
# A customized or unknown file is preserved, even under these exact names.
RETIRED_VALIDATION_PY_V110 = {
    'validation/v10400_numeric_route_audit.py': '092c71687a01b35534c096f0d0dc97e29f516a677f87a75600ba68bebded77ec',
    'validation/v10500_tcp_endgame_regions.py': 'e087c11d098af2a88ed98bcac9a68205b84b5f4948359228519cef854c997cae',
    'validation/v10600_admin_live3_bootstrap_dispatch.py': '89bb3bd217d8610227ad3b4bfe9ad22e5e770dd4cb3fc95190ca5404bb4ef518',
    'validation/v10600_bank_preflight.py': 'f7c0bc1c152d79477aa248d34d83597b8875821d0c23b3fcdbfaef35b7c2904f',
    'validation/v10600_predeploy_parallel_regression.py': 'f90c37a8a875314e1ab84dca94121675fe1d275cb313ab3f85386d41bbbb66e1',
    'validation/v10600_stage_v105_compatibility.py': 'a533b07d5c483ebb27e9fbd34b06475a7ab730fc26fe9e296e11d4535d4a325c',
    'validation/v10800_eq107_source_diagnostic_regression.py': 'eef066300f5ca5db67f0eb0e8d806666cded69a20e1814387915d52bf77ef2da',
    'validation/v10900_standard_upgrade_audit_test.py': '347e00b5a8bc721ddb71aca4420f3b8cc2477ba691bf6c28d838f164881a154e',
}
RETIRED_V109_SHA256.update(RETIRED_VALIDATION_PY_V110)



def retire(root, backup):
    """Remove certified obsolete BAT/PY only if identical bytes exist in backup.

    The caller must first stop the service AND make a complete persistent code
    backup. The update's outer rollback restores all backed-up code on failure.
    """
    root,backup=Path(root),Path(backup)
    if not backup.is_dir():
        raise RuntimeError('V110: brak kopii kodu przed porzadkowaniem instalatorow')
    root_real=root.resolve(strict=True)
    removed, preserved=[],[]
    for relative, expected in RETIRED_V109_SHA256.items():
        path=root/relative
        if not path.exists() and not path.is_symlink():
            continue
        # Never traverse linked folders or operate outside the live root.
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root_real):
            preserved.append(relative)
            continue
        copy=backup/relative
        if not copy.is_file() or copy.is_symlink():
            preserved.append(relative)
            continue
        if (any((root/Path(*Path(relative).parts[:i])).is_symlink()
                for i in range(1,len(Path(relative).parts)))
            or any((backup/Path(*Path(relative).parts[:i])).is_symlink()
                for i in range(1,len(Path(relative).parts)))):
            preserved.append(relative)
            continue
        real_sha=hashlib.sha256(path.read_bytes()).hexdigest()
        saved_sha=hashlib.sha256(copy.read_bytes()).hexdigest()
        if real_sha!=expected or saved_sha!=expected:
            preserved.append(relative)
            continue
        path.unlink()
        removed.append(relative)
    return tuple(removed),tuple(preserved)
