from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
from typing import Any, Text, Dict, List
import json
import datetime


def load_opening_hours():
    with open('opening_hours.json') as f:
        return json.load(f)['items']


def load_menu():
    with open('menu.json') as f:
        return json.load(f)['items']


class ActionCheckOpeningHours(Action):
    def name(self) -> Text:
        return "action_check_opening_hours"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> List[Dict[Text, Any]]:

        opening_hours = load_opening_hours()
        entities = tracker.latest_message.get("entities", [])
        datetime_entity = next((e for e in entities if e["entity"] == "datetime"), None)

        if not datetime_entity:
            dispatcher.utter_message("Please specify a date or time.")
            return []

        try:
            parsed_date = datetime_entity["additional_info"]["value"]
            if isinstance(parsed_date, dict):
                parsed_date = parsed_date["from"]

            dt = datetime.datetime.fromisoformat(parsed_date)
            day_name = dt.strftime("%A")
            target_time = dt.hour + dt.minute / 60
        except Exception as e:
            dispatcher.utter_message("Sorry, I didn't understand that time.")
            return []

        hours = opening_hours.get(day_name)
        if not hours or hours["open"] == 0:
            dispatcher.utter_message(f"We're closed on {day_name}.")
            return []

        open_time = hours["open"]
        close_time = hours["close"]

        if "value" in datetime_entity["additional_info"]:
            if open_time <= target_time < close_time:
                response = f"Yes, we're open from {open_time}:00 to {close_time}:00 on {day_name}."
            else:
                response = f"Closed at that time. Our {day_name} hours are {open_time}:00-{close_time}:00."
        else:
            response = f"We're open {open_time}:00-{close_time}:00 on {day_name}."

        dispatcher.utter_message(response)
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
