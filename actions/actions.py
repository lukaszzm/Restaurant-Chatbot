from __future__ import annotations

import re

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from typing import Any, Text, Dict, List
import json
from difflib import get_close_matches
from word2number import w2n

NO_MODIFIER_VALUE = "NO_MODIFIER"


def load_opening_hours():
    with open('config/opening_hours.json') as f:
        return json.load(f)['items']


def load_menu():
    with open('config/menu.json') as f:
        return json.load(f)['items']


class ActionCheckOpeningHours(Action):
    def name(self) -> Text:
        return "action_check_opening_hours"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> List[Dict[Text, Any]]:
        opening_hours = load_opening_hours()
        datetime_entity = next(tracker.get_latest_entity_values("datetime"), None)

        if not datetime_entity:
            dispatcher.utter_message("Sorry, I didn't understand the day you provided, please try again...")
            return []

        fixed_datetime = datetime_entity.strip().lower()
        valid_days = [d.lower() for d in opening_hours.keys()]

        matches = get_close_matches(fixed_datetime, valid_days, n=1, cutoff=0.6)

        if not matches:
            dispatcher.utter_message("Sorry, I didn't understand the day you provided, please try again...")

        matched_day = matches[0].capitalize()
        opening_hours_day = opening_hours[matched_day]

        if not opening_hours_day:
            dispatcher.utter_message(f"I couldn't find opening hours for {matched_day}, please try again with "
                                     f"different day...")

        from_hours = opening_hours_day['open']
        to_hours = opening_hours_day['close']

        if from_hours == 0 and to_hours == 0:
            dispatcher.utter_message(f"Sorry, we're closed on {matched_day}")

        dispatcher.utter_message(f"We're open from {from_hours} to {to_hours} on {matched_day}")
        return []


class ActionShowMenu(Action):
    def name(self) -> Text:
        return "action_show_menu"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> List[Dict[Text, Any]]:
        menu = load_menu()
        menu_list = [
            f"- {item['name']} (${item['price']}, {item['preparation_time']}h prep)"
            for item in menu
        ]
        dispatcher.utter_message("Today's menu:\n" + "\n".join(menu_list))
        return []


class ActionHandleOrder(Action):
    def name(self):
        return "action_handle_order"

    def get_quantity(self, quantity: str):
        fixed_quantity = quantity.strip().lower()

        if re.fullmatch(r'^\d+$', fixed_quantity):
            return int(fixed_quantity)

        try:
            return w2n.word_to_num(fixed_quantity)
        except ValueError:
            return None

    def get_item(self, item: str, menu: Any):
        fixed_item = item.strip().lower()
        valid_menu_items = [d['name'].lower() for d in menu]

        matches = get_close_matches(fixed_item, valid_menu_items, n=1, cutoff=0.6)

        if not matches:
            return None

        return matches[0].capitalize()

    def get_order_summary(self, item: str, quantity: int, modifier: str, menu: Any):
        price = 0
        prep_time = 0

        for menu_item in menu:
            if menu_item['name'] == item:
                price += menu_item["price"]
                prep_time += menu_item['preparation_time']

        subtotal = price * quantity
        total_prep = prep_time * quantity

        if modifier:
            return (
                f"Order Summary:\n"
                f"────────────────────────────\n"
                f"Item: {item} with {modifier}\n"
                f"Quantity: {quantity}\n"
                f"Price per unit: ${price:.2f}\n"
                f"Subtotal: ${subtotal:.2f}\n"
                f"Preparation Time: {total_prep:.2f} hours\n"
                f"────────────────────────────"
            )
        else:
            return (
                f"Order Summary:\n"
                f"────────────────────────────\n"
                f"Item: {item}\n"
                f"Quantity: {quantity}\n"
                f"Price per unit: ${price:.2f}\n"
                f"Subtotal: ${subtotal:.2f}\n"
                f"Preparation Time: {total_prep:.2f} hours\n"
                f"────────────────────────────"
            )

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> List[Dict[Text, Any]]:
        menu_items = load_menu()
        item_entry = next(tracker.get_latest_entity_values("menu_item"), "")
        item = self.get_item(item_entry, menu_items)

        if not item:
            dispatcher.utter_message("Sorry, I couldn't find the item in our menu, please try again...")
            return []

        quantity_entry = next(tracker.get_latest_entity_values("quantity"), "1")
        quantity = self.get_quantity(quantity_entry)

        if not quantity:
            dispatcher.utter_message("Sorry, your provided quantity is incorrect, please try again...")
            return []

        modifier_entry = next(tracker.get_latest_entity_values("modifier"), None)

        order_summary = self.get_order_summary(item, quantity, modifier_entry, menu_items)

        dispatcher.utter_message(order_summary + "\n" + "Is everything correct?")
        return []
