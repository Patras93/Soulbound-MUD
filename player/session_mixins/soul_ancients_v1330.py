# -*- coding: utf-8 -*-
"""Accessible progression readout for Soulbound v1.33.0."""
from systems.soul_ancients_v1330 import (
    EVOLUTION_THRESHOLDS, STAGE_NAMES, WEAPON_MILESTONES,
    evolution_stage, weapon_resonance_percent,
)
from core.classes_skills import CLASS_SKILLS
from systems.soul_evolutions_v1332 import evolution_description

class SessionSoulAncientsV1330Mixin:
    async def soul_legacy_v1330(self, args=''):
        if not self.character:
            await self.send('Najpierw zaloguj postać.');return
        ch=self.character
        soul=int(ch.soul_level)
        mastery=int(ch.soul_weapon_mastery_level)
        await self.send(f'DZIEDZICTWO DUSZY v1.33.2. Soul Level {soul}/800. Biegłość Broni Duszy {mastery}/800.')
        await self.send(f'Rezonans Broni Duszy: +{weapon_resonance_percent(mastery):g}% zwykłych trafień. Osobno od dotychczasowego Soul Tier i premii biegłości.')
        upcoming=next((level for level,_ in WEAPON_MILESTONES if mastery<level),None)
        if upcoming:await self.send(f'Następny rezonans Broni Duszy: biegłość {upcoming}.')
        else:await self.send('Osiągnięto najwyższy etap rezonansu Broni Duszy.')
        wanted=str(args or '').strip().casefold()
        if wanted in ('', 'info', 'pomoc'):
            await self.send('Wpisz: dziedzictwo skille — ewolucje poznanych umiejętności; dziedzictwo starozytni — arena Rady i cztery sanktuaria.')
            return
        if wanted in ('starozytni','bossowie'):
            await self.send('RADA STAROŻYTNYCH: wspólna arena. Wejście: Sanktuarium Smoka Korony Burz, kierunek wschód, potem północ.')
            await self.send('STAROŻYTNI: Olbrzym Pierwszych Kuźni, Smok Korony Burz, Tytan Utraconego Czasu, Duch Pradawnego Wodza.')
            await self.send('Dojście: ery starozytni. Bossowie zmieniają żywioły i ataki wraz z fazą, przyzywają strażników bez limitu.')
            return
        if wanted not in ('skille','skills','umiejetnosci'):
            await self.send('Dostępne: dziedzictwo skille; dziedzictwo starozytni.');return
        known=set(self.server.db.learned_skill_ids(self.account_id))
        entries=[];seen=set()
        for class_name in self.active_class_names():
            for skill in CLASS_SKILLS.get(class_name,()):
                sid=str(skill['id'])
                if sid not in known or sid in seen:continue
                seen.add(sid)
                level=int(self.server.db.skill_progress(self.account_id,sid)['level'])
                stage=evolution_stage(level,soul)
                next_gate=next(((s,so) for s,so in EVOLUTION_THRESHOLDS if level<s or soul<so),None)
                progress=f'Następny etap: Skill Level {next_gate[0]}, Soul Level {next_gate[1]}.' if next_gate else 'Ostatnia ewolucja osiągnięta.'
                entries.append(f'{skill["name"]}: poziom {level}/800; {STAGE_NAMES[stage]}; {evolution_description(skill,level,soul)}; {progress}')
        await self.send(f'Poznane skille: {len(entries)}. Ewolucje są zależne od Skill Level i Soul Level; efekt zależy od roli umiejętności.')
        for line in entries:await self.send(line)
