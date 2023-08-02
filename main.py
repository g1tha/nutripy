from Persons import Person
import csv
import json
import polars as pl
import curses
import re


def main():
    food = curses.wrapper(search_food)
    print(food)
    # with open('dct.json', 'w') as file:
    #   json.dump(dct, file)


def search_food(stdscr):
    # Set colors to match terminal defaults
    curses.use_default_colors()
    # Read parquet food files
    food_list = pl.read_parquet("data/sources/food_list.parquet")
    food_list = food_list.with_columns(
        pl.col("food")
        .str.to_lowercase()
        .str.replace_all(r"[^a-z.]", "")
        .alias("food_strip")
    )
    # Establish filtered_food variable for search results
    filtered_food = food_list
    # Establish scroll_counter variable for scrolling through search results
    scroll_counter = 0
    food_nutrients = pl.read_parquet("data/sources/food_nutrients.parquet")
    # Prompt user for input
    prompt = "Enter food search term (or press the 'esc' key to quit): "
    user_input = ""
    # Start a new screen
    stdscr.clear()
    stdscr.addstr(0, 0, prompt)
    stdscr.refresh()
    # Add a new pad
    height, width = stdscr.getmaxyx()
    height = height - 1
    pad = curses.newpad(height, width)
    pad.refresh(0, 0, 1, 0, height, width)

    # List keys which do not have any input
    # Update screen and pad
    while True:
        key = stdscr.getch()
        # exit if escape key (27) is hit, return nothing
        if key == 27:
            return None
        # If enter key (10) hit, return 1st entry of filtered_food
        elif key == 10:
            if user_input and pl.count(filtered_food["food"]) > 0:
                user_input = filtered_food.item(row=0, column="food")
                return user_input
        # If tab key (9) is hit, autocomplete
        # based on 1st entry of filtered food
        elif key == 9:
            if user_input and pl.count(filtered_food["food"]) > 0:
                user_input = filtered_food.item(row=0, column="food")
        # If backspace is hit, delete
        elif (key == curses.KEY_BACKSPACE or key == curses.KEY_LEFT):
            # clear text based on previous user_input length
            stdscr.addstr(0, (len(prompt)+ len(user_input)), (width - len(prompt) - len(user_input)) * " ")
            user_input = user_input[:-1]
            scroll_counter = 0
        # Otherwise, if key pressed is standard text characters, add to user_input
        elif key > 31 and key < 127:
            # clear text based on previous user_input length
            stdscr.addstr(0, (len(prompt)+ len(user_input)), (width - len(prompt) - len(user_input)) * " ")
            user_input += chr(key)
            scroll_counter = 0
        # update the pad with search results for the user_input
        if user_input:
            # Use stripped (lower_case alphabetic characters only) for search
            user_input_stripped = re.sub(r"[^a-z.]", "", user_input.lower())
            # Find foods that beging with user_input
            food_begins = food_list.filter(
                pl.col("food_strip").str.starts_with(user_input_stripped)
            )
            # From the remaining foods, find those that contain user_input
            food_contains = food_list.filter(
                ~pl.col("food_strip").str.starts_with(user_input_stripped)
            ).filter(pl.col("food_strip").str.contains(user_input_stripped))
            # Combine dataframes, prioritising foods that begin with user_input
            filtered_food_full = pl.concat([food_begins, food_contains])
            # create a windowed filtered_food to allow scrolling through results
            # Allow incremental scrolling
            if key == curses.KEY_DOWN and scroll_counter < (filtered_food_full.height - 1):
                scroll_counter += 1
            if key == curses.KEY_UP and scroll_counter > 0:
                scroll_counter += -1
            # Allow scrolling by page
            if key == curses.KEY_NPAGE and scroll_counter < (filtered_food_full.height - 1 - height):
                scroll_counter += height
            if key == curses.KEY_PPAGE and scroll_counter > 0 + height:
                scroll_counter += -height
            elif key == curses.KEY_PPAGE:
                scroll_counter = 0
            # Go back to start by pressing home
            if key == curses.KEY_HOME:
                scroll_counter = 0
            # Go to last page by pressing end
            if key == curses.KEY_END:
                scroll_counter = max((filtered_food_full.height - height), 0)
            # If scroll counter hasn't been updated by above conditions but the filter has 
            # e.g. pressing key_down after only one filtered result availble, 
            # reset the scroll counter to zero.
            if scroll_counter >= filtered_food_full.height:
                scroll_counter = 0
            filtered_food = filtered_food_full.slice(scroll_counter)
            # Clear existing search results in pad
            pad.erase()
            # Add search results (filtered_food) to pad 
            line = 0
            for count, value in enumerate(filtered_food["food"]):
                if count < height - 1:
                    pad.addstr(line, 0, f"{value}\n")
                    pad.refresh(0, 0, 1, 0, height, width)
                    line = count + 1
        # When there isn't user input, clear the pad
        else:
            pad.erase()
            pad.refresh(0, 0, 1, 0, height, width)
        # Update user_input shown on screen following key-press
        stdscr.addstr(0, len(prompt), user_input)
        stdscr.refresh()


def new_user():
    person = Person.get()

    print(person)
    print(person.uid)
    print(person.bmi)
    print(person.desired_bmi)
    print(person.desired_weight)

    for nutrient in person.diet_rqmts:
        if (
            person.diet_rqmts[nutrient]["amount_lower"]
            and person.diet_rqmts[nutrient]["amount_upper"]
            and person.diet_rqmts[nutrient]["amount_lower"]
            != person.diet_rqmts[nutrient]["amount_upper"]
        ):
            if person.diet_rqmts[nutrient]["amount_tul"]:
                print(
                    f"{nutrient}: {person.diet_rqmts[nutrient]['amount_lower']:.2f}-{person.diet_rqmts[nutrient]['amount_upper']:.2f} ({person.diet_rqmts[nutrient]['amount_tul']:.2f} limit) {person.diet_rqmts[nutrient]['unit']}"
                )
            else:
                print(
                    f"{nutrient}: {person.diet_rqmts[nutrient]['amount_lower']:.2f}-{person.diet_rqmts[nutrient]['amount_upper']:.2f} {person.diet_rqmts[nutrient]['unit']}"
                )
        elif person.diet_rqmts[nutrient]["amount_lower"]:
            if person.diet_rqmts[nutrient]["amount_tul"]:
                print(
                    f"{nutrient}: {person.diet_rqmts[nutrient]['amount_lower']:.2f} ({person.diet_rqmts[nutrient]['amount_tul']:.2f} limit) {person.diet_rqmts[nutrient]['unit']}"
                )
            else:
                print(
                    f"{nutrient}: {person.diet_rqmts[nutrient]['amount_lower']:.2f} {person.diet_rqmts[nutrient]['unit']}"
                )


if __name__ == "__main__":
    main()
