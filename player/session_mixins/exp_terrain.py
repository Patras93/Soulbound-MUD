# -*- coding: utf-8 -*-
"""Zgodna fasada v109; oryginalne nazwy metod i API zachowane."""
from __future__ import annotations
# Stałe używane przez metody zachowane w tej fasadzie są importowane jawnie.
from core.progression_600 import CHARACTER_MAX_LEVEL
from core.mines_threat import EXP_AREA_BASE_CATEGORY, EXP_AREA_TARGET_POWER
from world.dynamic_content import EXP_AREAS
from .exp_terrain_parts_v109.dependencies import *
from .exp_terrain_parts_v109 import (
    ExpSafetyV109Mixin,
    ExpRecommendationsV109Mixin,
    ExpCalculationV109Mixin,
    ExpTerrainUIV109Mixin,
)

class SessionExpTerrainMixin(
    ExpSafetyV109Mixin,
    ExpRecommendationsV109Mixin,
    ExpCalculationV109Mixin,
    ExpTerrainUIV109Mixin,
):

    def combat_power_explanation_v110016(self):
            """Separate actual level from the estimate; never present it as a level."""
            level = max(1, int(getattr(self.character, "character_level", 1) or 1))
            power = self.character_progression_power()
            return (
                f"Poziom postaci: {level}. "
                f"Orientacyjna siła bojowa: {power}/{CHARACTER_MAX_LEVEL}. "
                "Siła bojowa uwzględnia biegłości, Duszę, statystyki i wyposażenie; "
                "nie zastępuje poziomu postaci ani nie gwarantuje wygranej."
            )

    def exp_area_safety_summary_v110016(self, area, room_id=None):
            """Show entry danger against real character level, not just combat score."""
            level = max(1, int(getattr(self.character, "character_level", 1) or 1))
            target = max(1, int(self.exp_area_target_power(area, room_id=room_id)))
            area_id = str(area.get("id", ""))
            target = max(target, int(EXP_AREA_TARGET_POWER.get(area_id, 1)))
            if area_id == "trening":
                return "Zagrożenie: bezpieczny plac treningowy."
            if area_id == "mythic_crypt":
                target = max(target, 130)
            elif area_id == "mythic_astral":
                target = max(target, 150)
            elif area_id == "astral":
                target = max(target, 110)
            elif area_id == "krypta":
                target = max(target, 30)
            gap = target - level
            if gap >= 20:
                label = "ekstremalnie niebezpieczny — NIEPOLECANY"
            elif gap > 8:
                label = "zbyt trudny — niepolecany"
            elif gap > 0:
                label = "trudny — zachowaj ostrożność"
            elif gap >= -15:
                label = "odpowiedni do rozważenia"
            else:
                label = "raczej łatwy na wejściu"
            return (
                f"Zagrożenie wejścia: {label}. "
                f"Orientacyjny próg przeciwników: {target}, "
                f"poziom postaci: {level}. "
                "Bossowie i głębsze piętra mogą być trudniejsze."
            )

    async def show_exp_areas(self, query=""):
            query = str(query or "").strip()
            normalized = (
                self.normalize_description_query(query)
                if query
                else ""
            )

            # v31: krotki podglad wielkich szescioczesciowych kronik 401-800.
            if normalized in {"kroniki", "kronika", "fabula 401-800", "saga"}:
                from world.v3100_endgame_chronicles import CHAPTERS
                await self.send('KRONIKI KRAIN 401-800. Po jednym NPC na krainę; przyjmij 1.')
                for slug, zone, low, high, mentor, camp, *_rest in CHAPTERS:
                    ids=[f'v3100_{slug}_quest_{i}' for i in range(1,7)]
                    completed=0
                    active=0
                    try:
                        for qid in ids:
                            state=self.server.db.quest(self.account_id,qid)
                            if state and state['status']=='completed':
                                completed+=1
                            elif state and state['status']=='active':
                                active+=1
                    except (AttributeError, TypeError, KeyError):  # AUDIT_INTENTIONAL_PASS: optional quest status overlay
                        # Katalog nadal dziala w sesji bez odczytu postepow.
                        pass
                    suffix=('ukończona' if completed==6 else
                            f'{completed}/6 ukończonych'+(', 1 aktywne' if active else ''))
                    await self.send(f'{zone}, Level {low}-{high}: {suffix}. '
                                    f'NPC: {mentor}, {camp}. Wejście: prowadz {zone.lower()}, '
                                    'potem trzeci pokój i wschód.')
                return

            recommendation_query = (
                normalized in {"polecane", "recommended", "dla mnie"}
                or normalized.startswith("polecane ")
                or normalized.startswith("recommended ")
                or normalized.startswith("dla mnie ")
            )
            if recommendation_query:
                parts = normalized.split()
                final = parts[-1] if parts else ""
                if final in {"wszystkie", "all", "wszystko"}:
                    limit = len(EXP_AREAS)
                elif final.isdigit():
                    limit = max(1, min(len(EXP_AREAS), int(final)))
                elif normalized in {"polecane", "recommended", "dla mnie"}:
                    limit = 5
                else:
                    await self.send("Użycie: expowiska polecane; expowiska polecane 10; expowiska polecane wszystkie.")
                    return
                areas = self.recommended_exp_areas_v2910()
                await self.send(
                    f"POLECANE EXPOWISKA. "
                    f"Level postaci: {self.character.character_level}. "
                    f"Orientacyjna siła bojowa: {self.character_progression_power()}/{CHARACTER_MAX_LEVEL}. "
                    "Lista jest liczona od nowa przy każdym wywołaniu, także po awansie. "
                    "Bossowie i głębsze piętra mogą być dużo trudniejsze."
                )
                if not areas:
                    await self.send(
                        "Brak terenu dokładnie w twoim "
                        "orientacyjnym zakresie. "
                        "Wpisz expowiska, aby zobaczyć wszystko."
                    )
                    return
                for index, area in enumerate(areas[:limit], 1):
                    level = int(self.character.character_level)
                    _, maximum = self.exp_area_character_level_band_v03012(area)
                    deep = str(area.get('id')) in {'krypta', 'astral', 'mythic_crypt', 'mythic_astral'} and level > maximum
                    warning = (' Skalowany loch: dobierz odblokowane piętro do swojej siły.' if deep else '')
                    await self.send(
                        f"{index}. {area['name']}. "
                        f"{self.exp_area_category_text(area)}. "
                        f"Prowadzenie: prowadz {area['guide']}.{warning}"
                    )
                if len(areas) > limit:
                    await self.send(
                        f"Pokazano {limit} z {len(areas)}. "
                        "Więcej: expowiska polecane 10 albo expowiska polecane wszystkie."
                    )
                return

            if query:
                area = self.find_exp_area(query)
                if not area:
                    await self.send(
                        "Nie rozpoznaję expowiska. "
                        "Wpisz expowiska, aby usłyszeć pełną listę."
                    )
                    return
                await self.show_exp_area_details(area)
                return

            await self.send(
                f"EXPOWISKA. Soul Level: {self.character.soul_level}. "
                f"Poziom postaci: {self.character.character_level}. Orientacyjna siła bojowa: {self.character_progression_power()}/{CHARACTER_MAX_LEVEL}."
            )
            await self.send(
                "Tereny mają kategorię bazową: Początkujący, Umiarkowany, Trudny, "
                "Śmiertelny lub Endgame. Ocena 'dla ciebie' zmienia się automatycznie "
                "wraz z Biegłością klas, Soul Levelem, statystykami i wyposażeniem."
            )

            for number, area in enumerate(
                EXP_AREAS,
                1,
            ):
                marker = (
                    " Polecane dla ciebie."
                    if self.exp_area_recommended(area)
                    else ""
                )
                await self.send(
                    f"{number}. {area['name']}. "
                    f"{self.exp_area_category_text(area)}. "
                    f"{area['description']}"
                    f"{marker}"
                )

            await self.send(
                "Szczegóły: expowiska nazwa. "
                "Tylko polecane: expowiska polecane. Więcej: expowiska polecane 10."
            )

    def exp_area_category_text(self, area, room_id=None):
            base = EXP_AREA_BASE_CATEGORY.get(area.get("id"), "Umiarkowany")
            dynamic, target, power = self.exp_area_dynamic_threat(area, room_id=room_id)
            if area.get("id") == "trening":
                dynamic, target = "Treningowy (bezpieczny)", 1
            return (
                f"Kategoria bazowa: {base}. "
                f"Dla twojej obecnej postaci: {dynamic}. "
                f"Poziom postaci {self.character.character_level}, orientacyjna siła bojowa {power}/{CHARACTER_MAX_LEVEL}, "
                f"próg terenu około {target}/{CHARACTER_MAX_LEVEL}. "
                f"{self.exp_area_safety_summary_v110016(area, room_id=room_id)}"
            )
