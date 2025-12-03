from fastapi import HTTPException, status

#importing data layers
from storage import get_recipes_data, set_recipes_data, get_pantry_data, set_pantry_data
from model import Recipe, PantryItem

# defining our helper functions

def get_recipes() -> list[Recipe]:
    """Fetches all recipes from storage and converts them to Pydantic models.

    Returns:
        list[Recipe]: a list of Recipe models
    """
    raw_data = get_recipes_data() #gets the raw data from storage in form of list[dict]
    recipe_list: list[Recipe] = [] #list to hold our Recipe models
    for item in raw_data: #iterating through each dictionary in the list
        try: #attempting to convert the dictionary to a Recipe model
            recipe = Recipe(**item)
            recipe_list.append(recipe)
        except Exception as e:
            # Log the error and skip the invalid entry
            print(f"Error parsing recipe data: {e}")
    return recipe_list

def add_new_recipe(new_recipe:Recipe) -> None:
    """add's a new recipe and saves it to storage.

    Args:
        recipe (Recipe): The Recipe model to be saved.
    """
    recipes = get_recipes() #get the old recipes from storage
    for r in recipes:
        if r.recipe_id == new_recipe.recipe_id: #Check if Recipe ID allready exists
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"Recipe with ID {new_recipe.recipe_id} already exists.")
        raw_recipes = get_recipes_data()
        raw_recipes.append(new_recipe.model_dump())
        set_recipes_data(raw_recipes)

def get_pantry() -> list[PantryItem]:
    """Fetches all the pantry dict and turns it into a List of Pydantic Models

    Returns:
        list[PantryItem]: a list of PantryItem models
    """
    raw_data:dict = get_pantry_data()
    pantry_list = [] #list to hold our Pantry models
    for key, value in raw_data.items():
        item = PantryItem(name=key, amount=value)
        pantry_list.append(item)
    return pantry_list

def modify_pantry(item:PantryItem) -> list[dict]:
    """Adds or Removes an amount of Items to the Pantry

    Args:
        item (PantryItem): name of the Item, all lowercase
        amount (int, optional): Amount of items. Positve adds, negative subtracts Defaults to 0.
    """

    old_data:dict = get_pantry_data()
    new_data = old_data.copy()
    if item.amount ==0:
        return [old_data,new_data] #Amount 0 -> No change to be done
    if item.name in old_data:# Check if the Item allready exists in the Pantry dict
        if item.amount > 0: # If positive amount -> increase amount of Items
            old_amount = old_data[item.name]
            new_data[item.name] = old_amount + item.amount
            set_pantry_data(new_data)
            return [old_data, new_data]
        else: # If negative amount -> reduce amount of Items
            old_amount = int(old_data[item.name])
            new_data[item.name] = old_amount + item.amount
            if int(new_data[item.name]) <= 0: # Item amount ZERO or lower
                new_data.pop(item.name) # remove empty item
            set_pantry_data(new_data)
            return [old_data, new_data]
    else:
        if item.amount <=0:
            return [old_data,new_data]# Item not Found, amount to be lowered -> Nothing needs to be done
        else:
            new_data[item.name] = item.amount
            set_pantry_data(new_data)
            return [old_data, new_data]# Returns a List, first OLD dict, then the NEW Dict

def find_cookable_recipes() -> list[Recipe]:
    """Finds Recipes which can be cooked and returns them as List

    Returns:
        list[Recipe]: List of cookable recipes
    """
    all_r:list[Recipe] = get_recipes()
    pantry:dict = get_pantry_data()
    cookable_r:list[Recipe] = []
    for recipe in all_r:
        can_cook = True
        for ingredient_name, needed_amount in recipe.ingredients.items():
            pantry_amount = pantry.get(ingredient_name, 0)
            if pantry_amount < needed_amount:
                can_cook = False
                break
        if can_cook:
            cookable_r.append(recipe)
    return cookable_r

def cook_recipe(to_cook_id: int) -> Recipe:
    """Cooks a Recipe, removing the used ingredients

    Args:
        to_cook_id (int): ID of Recipe to be Cooked

    Raises:
        HTTPException: Error if Recipe cannot be cooked / found
    """
    all_r:list[Recipe] = get_recipes()
    pantry:dict = get_pantry_data()
    cookable_r = find_cookable_recipes()
    to_cook = None
    for r in cookable_r:
        if r.recipe_id == to_cook_id:
            to_cook = r
            break
    if to_cook == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Recipe with ID {to_cook_id} wasnt found in the cookable Recipes.")
    new_pantry = pantry.copy()
    for ingredient_name, needed_amount in to_cook.ingredients.items():
        new_pantry[ingredient_name] = int(new_pantry[ingredient_name]) - int(needed_amount)
    set_pantry_data(new_pantry)
    return to_cook
