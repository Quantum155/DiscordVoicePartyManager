import datetime


def predict_stats(days_back: int, fkills: int, fdeaths: int, stars: int,
                  current_fkills: int, current_fdeaths: int, current_stars: int,
                  date: datetime.date = datetime.date(2023, 12, 30))\
                  -> tuple[float, float, float, float]:
    today = datetime.date.today()
    future = date
    diff = future - today
    days_left = diff.days

    predicted_stars_gained = stars / days_back * days_left
    predicted_stars = current_stars + predicted_stars_gained

    predicted_finals_gained = fkills / days_back * days_left
    predicted_fdeaths_gained = fdeaths / days_back * days_left
    predicted_finals = predicted_finals_gained + current_fkills
    predicted_fdeaths = predicted_fdeaths_gained + current_fdeaths

    predicted_fkdr = predicted_finals / predicted_fdeaths

    return round(predicted_stars, 2), round(predicted_finals, 2),\
        round(predicted_fdeaths, 2), round(predicted_fkdr, 2)

# Main server: "<:up_emoji:1051970899743608954>"
# Main server: "<:down_arrow:1051970897948442754>"

# Test server: <:up_emoji:1051894293410881547>
# Test server <:down_arrow:1051894291733164113>

def change_character(original=None, after=None, change=None):
    if change is not None:
        if change >= 0:
            return "<:up_emoji:1051970899743608954>"
        else:
            return "<:down_arrow:1051970897948442754>"
    else:
        if after - original >= 0:
            return "<:up_emoji:1051970899743608954>"
        else:
            return "<:down_arrow:1051970897948442754>"
