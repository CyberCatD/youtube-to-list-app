from sqlalchemy.orm import Session
from src.models import Recipe, Ingredient, RecipeIngredient, Instruction
from src.schemas import VideoMetadataSchema
from src.services import youtube_service, llm_service
from datetime import datetime

def upsert_recipe_from_youtube_url(db: Session, youtube_url: str) -> Recipe:
    """
    Processes a YouTube URL to create or update a structured Recipe entry in the database.
    If a recipe with the given source_url already exists, it updates it.
    """
    print("--- DEBUG: Starting recipe upsert ---")
    try:
        video_id = youtube_service.extract_video_id(youtube_url)
        print(f"--- DEBUG: Extracted video_id: {video_id} ---")
        
        has_transcript = youtube_service.check_transcript_availability(video_id)
        print(f"--- DEBUG: Transcript available: {has_transcript} ---")
        
        metadata = youtube_service.get_video_metadata(video_id)
        metadata.comments = youtube_service.get_video_comments(video_id)
        print("--- DEBUG: Fetched metadata and comments ---")
        
        transcript = ""
        if has_transcript:
            try:
                transcript = youtube_service.get_video_transcript(video_id)
                print("--- DEBUG: Fetched transcript ---")
            except ValueError as e:
                print(f"--- DEBUG: Error fetching transcript, proceeding without it: {e} ---")
        
        print("--- DEBUG: Sending data to LLM ---")
        llm_output = llm_service.generate_content_and_tags(metadata, transcript)
        print("--- DEBUG: Received data from LLM ---")

        recipe_details = llm_output.get("recipe_details", {})
        
        # Check if recipe already exists
        db_recipe = db.query(Recipe).filter(Recipe.source_url == youtube_url).first()

        if db_recipe:
            print(f"--- DEBUG: Updating existing recipe ID: {db_recipe.id} ---")
            # Update existing recipe details
            db_recipe.name = recipe_details.get("name", metadata.title)
            db_recipe.prep_time = recipe_details.get("prep_time")
            db_recipe.cook_time = recipe_details.get("cook_time")
            db_recipe.total_time = recipe_details.get("total_time")
            db_recipe.servings = recipe_details.get("servings")
            db_recipe.category = recipe_details.get("category")
            db_recipe.cuisine = recipe_details.get("cuisine")
            db_recipe.calories = recipe_details.get("calories")
            db_recipe.main_image_url = llm_output.get("main_image_url", metadata.thumbnail_url)
            # db_recipe.card_color is removed
            
            # Clear existing ingredients and instructions for a full update
            db_recipe.ingredients.clear()
            db_recipe.instructions.clear()
            db.flush() # Ensure old associations are cleared

        else:
            print("--- DEBUG: Creating new recipe ---")
            db_recipe = Recipe(
                name=recipe_details.get("name", metadata.title),
                source_url=youtube_url,
                prep_time=recipe_details.get("prep_time"),
                cook_time=recipe_details.get("cook_time"),
                total_time=recipe_details.get("total_time"),
                servings=recipe_details.get("servings"),
                category=recipe_details.get("category"),
                cuisine=recipe_details.get("cuisine"),
                calories=recipe_details.get("calories"),
                main_image_url=llm_output.get("main_image_url", metadata.thumbnail_url),
            )
            db.add(db_recipe)
        
        # Flush the session to ensure db_recipe has an ID before processing relationships
        db.flush()
        db.refresh(db_recipe) # Refresh to ensure ID is available for new recipes

        # Process Ingredients by leveraging the SQLAlchemy relationship
        ingredients_data = llm_output.get("ingredients", [])
        print(f"--- DEBUG: Processing {len(ingredients_data)} ingredients ---")
        for item in ingredients_data:
            ingredient_name = item.get("name")
            if not ingredient_name:
                continue
            
            # Find existing ingredient or create a new one in the current session
            db_ingredient = db.query(Ingredient).filter(Ingredient.name.ilike(ingredient_name)).first()
            if not db_ingredient:
                db_ingredient = Ingredient(name=ingredient_name)
                db.add(db_ingredient)
                db.flush() # Ensure new ingredient gets an ID if it's created
                print(f"--- DEBUG: Creating new ingredient: {ingredient_name} ---")
            
            # Create the association object and append it to the recipe's ingredient list
            recipe_ingredient = RecipeIngredient(
                ingredient=db_ingredient,
                quantity=item.get("quantity"),
                unit=item.get("unit"),
                notes=item.get("notes")
            )
            db_recipe.ingredients.append(recipe_ingredient)
        print("--- DEBUG: Finished processing ingredients ---")

        # Process Instructions by leveraging the SQLAlchemy relationship
        instructions_data = llm_output.get("instructions", [])
        print(f"--- DEBUG: Processing {len(instructions_data)} instructions ---")
        for item in instructions_data:
            db_instruction = Instruction(
                step_number=item.get("step_number"),
                section_name=item.get("section_name"),
                description=item.get("description")
            )
            db_recipe.instructions.append(db_instruction)
        print("--- DEBUG: Finished processing instructions ---")
            
        print("--- DEBUG: Committing transaction to database ---")
        db.commit() # Commit everything at once at the end
        print("--- DEBUG: Commit successful ---")
        
        db.refresh(db_recipe) # Refresh after commit to load all relationships
        print("--- DEBUG: Recipe object refreshed from DB ---")
        
        return db_recipe
        
    except Exception as e:
        print(f"--- DEBUG: An error occurred: {e} ---")
        db.rollback()
        print("--- DEBUG: Transaction rolled back ---")
        raise RuntimeError(f"Failed to process YouTube URL: {e}") from e

def get_recipe_by_id(db: Session, recipe_id: int) -> Recipe | None:
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()

def get_all_recipes(db: Session) -> list[Recipe]:
    return db.query(Recipe).order_by(Recipe.created_at.desc()).all()

def delete_recipe_by_id(db: Session, recipe_id: int) -> Recipe | None:
    recipe_to_delete = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if recipe_to_delete:
        db.delete(recipe_to_delete)
        db.commit()
        return recipe_to_delete
    return None