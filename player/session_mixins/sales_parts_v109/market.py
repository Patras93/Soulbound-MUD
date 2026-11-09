# -*- coding: utf-8 -*-
"""v109: sprzedaż — market; identyczne metody względem v108."""
from .dependencies import *

class SalesMarketV109Mixin:

    def generic_item_sale_allowed_here(self):
            # Zwykłe przedmioty można odsprzedawać w każdej lokacji z normalnym sklepem.
            return self.character.room_id in SHOPS
    def generic_item_sale_buyer_name(self):
            seller_id = SHOP_SELLERS.get(self.character.room_id)
            seller = NPCS.get(seller_id) if seller_id else None
            return seller.get("name") if seller else "lokalny handlarz"
    def market_buyer_rejects_item(self, item_id, item):
            # v0.9.15: Rynek ma osobny skup łupów/EQ, ale nigdy nie przejmuje
            # sprzedaży profesji. Każdy surowiec typu resource zostaje dla
            # właściwego fachowca albo systemu craftingu.
            if self.character.room_id != "market":
                return False
            if not item:
                return True
            if item.get("type") in {"resource", "craft_material"}:
                return True
            if item_id in CRAFT_MATERIAL_STORAGE_IDS:
                return True
            if item_id in (
                FISH_STORAGE_IDS | MINING_STORAGE_IDS | WOOD_STORAGE_IDS | HERB_STORAGE_IDS
            ):
                return True
            return False
    def resource_sale_allowed_here(self, item_id):
            # v0.8.67: surowce profesji skupują tylko właściwi fachowcy.
            room_id = self.character.room_id
            if item_id in FISH_STORAGE_IDS:
                return room_id == "fish_market"
            if item_id in MINING_STORAGE_IDS:
                return room_id == "mountain_market"
            if item_id in WOOD_STORAGE_IDS:
                return room_id == "lumberjack_camp"
            if item_id in HERB_STORAGE_IDS:
                return room_id == "herbalist_hut"
            return False
    def resource_sale_location_text(self, container):
            return {
                "net": "Targ Rybny — Rybak Borys i rybacy",
                "bag": "Górski Targ Minerałów — Handlarka Minerałów Dagna",
                "woodpile": "Obóz Drwala — Drwal Bran",
                "herbbag": "Chata Zielarki — Zielarka Liora",
            }.get(container, "właściwy punkt skupu profesji")
    def resource_sale_buyer_text(self, container):
            return {
                "net": "Rybakom na Targu Rybnym",
                "bag": "Handlarce Minerałów Dagnie",
                "woodpile": "Drwalowi Branowi",
                "herbbag": "Zielarce Liorze",
            }.get(container, "właściwemu skupującemu")
    def profession_sale_definition(self, container):
            # v0.8.68: sprzedaż u właściwego fachowca rozwija specjalizację/profesję,
            # ale nie narzędzie. EXP jest liczony za faktycznie sprzedane sztuki.
            return {
                "net": ("Wędkarstwo", "fishing"),
                "bag": ("Górnictwo", "mining"),
                "woodpile": ("Drwalstwo", "woodcutting"),
                "herbbag": ("Zielarstwo", "herbalism"),
            }.get(container)
