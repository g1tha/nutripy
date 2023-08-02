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
    filtered_food = food_list
    food_nutrients = pl.read_parquet("data/sources/food_nutrients.parquet")
    prompt = "Enter food search term (or press the 'esc' key to quit): "
    user_input = ""
    # Start a new screen
    stdscr.clear()
    # curses.curs_set(0)
    stdscr.addstr(0, 0, prompt)
    stdscr.refresh()
    # Add a new pad
    height, width = stdscr.getmaxyx()
    height = height - 1
    pad = curses.newpad(height, width)
    pad.refresh(0, 0, 1, 0, height, width)

    while True:
        key = stdscr.getch()
        # exit if escape key (27) is hit, return nothing
        if key == 27:
            return None
        # If enter key (10) hit, return 1st entry of 
        # filtered food, otherwise return none
        elif key == 10:  # Enter key pressed
            if pl.count(filtered_food["food"]) > 0:
                user_input = filtered_food.item(row=0, column="food")
                return user_input
            else:
                return None
        # If tab key (9) is hit, autocomplete
        # based on 1st entry of filtered food
        elif key == 9: # Tab key pressed
            if pl.count(filtered_food["food"]) > 0:
                user_input = filtered_food.item(row=0, column="food")
        elif key == curses.KEY_BACKSPACE:
            stdscr.addstr(0, (len(prompt)+ len(user_input)), (width - len(prompt) - len(user_input)) * " ")
            user_input = user_input[:-1]  # Remove the last character
        else:
            stdscr.addstr(0, (len(prompt)+ len(user_input)), (width - len(prompt) - len(user_input)) * " ")
            user_input += chr(key)  # Add the pressed character to user input
        if user_input:
            user_input_stripped = re.sub(r"[^a-z.]", "", user_input.lower())
            food_begins = food_list.filter(
                pl.col("food_strip").str.starts_with(user_input_stripped)
            )
            food_contains = food_list.filter(
                ~pl.col("food_strip").str.starts_with(user_input_stripped)
            ).filter(pl.col("food_strip").str.contains(user_input_stripped))
            filtered_food = pl.concat([food_begins, food_contains])
            pad.erase()
            line = 0
            for count, value in enumerate(filtered_food["food"]):
                if count < height - 1:
                    pad.addstr(line, 0, f"{value}\n")  # Display the filtered DataFrame
                    pad.refresh(0, 0, 1, 0, height, width)
                    line = count + 1
        stdscr.addstr(0, len(prompt), user_input)
        stdscr.refresh()


def filter_food(term):
    food_list = pl.read_parquet("data/sources/food_list.parquet")
    food_nutrients = pl.read_parquet("data/sources/food_nutrients.parquet")
    filtered_food = food_list.filter(pl.col("food").str.contains(term))
    for i in filtered_food["food"].head(10):
        print(i)


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
