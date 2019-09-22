def get_default_options():
    options = (
        'Main',
        'End turn',
        'Quit game',
    )
    return options


def get_city_options(game, city, civ, units=[]):
    prod_current = "Production - {} ({:.1f}/{})".format(
        city.prod,
        city.prod_progress,
        city.get_item_cost(city.prod, 'production')
    ) if city.prod else "Production"
    prod_options = city.prod_options() if city.prod_options() else ["No production options"]
    buildings = [b.name for b in city.buildings]
    civ_options = get_civ_options(civ)
    options = (
        "{} ({})".format(city.name, city.civ),
        (
            prod_current,
            (
                "Choose production",
                *prod_options
            ),
            (
                "Buildings",
                *buildings
            )
        ),
        civ_options,
    )
    for unit in units:
        options += ((get_unit_options(game, unit, civ),) if unit else ("No unit stationed",))
    options += (
        "End turn",
    )
    return options


def get_unit_options(game, unit, civ=None):
    options = (
        "Unit actions: {} ({})".format(unit.name, unit._class),
    )
    if unit._class == 'worker':
        options += (
            "{} moves, {} builds remaining".format(unit.moves, unit.builds),
        )
    else:
        options += (
            "{} moves remaining".format(unit.moves),
        )
    for action in unit.actions(game):
        options += (action,)
    if civ:
        options += (get_civ_options(civ),)
    return options


def get_multi_unit_options(game, units, civ):
    options = ("Multiple units",)
    for unit in units:
        options += (get_unit_options(game, unit),)
    options += (get_civ_options(civ),)
    return options


def get_civ_options(civ):
    yields = ("Yields",)
    totals = ("Totals",)
    for k, v in civ.yields.items():
        yields += ("{}: {:.1f}".format(k, v),)
    for k, v in civ.totals.items():
        totals += ("{}: {:.1f}".format(k, v),)
    options = (
        "Civilization menu",
        yields,
        totals
    )
    return options