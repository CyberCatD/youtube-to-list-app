from sqlalchemy.orm import Session
from src.models import Recipe, Ingredient, RecipeIngredient, Instruction, Tag
from src.schemas import VideoMetadataSchema
from src.services import youtube_service, llm_service, web_scraper_service, social_media_service
from src.logging_config import get_logger
from src.metrics import recipe_processing_time, recipes_imported, update_recipe_count
from datetime import datetime
import time

logger = get_logger(__name__)

def _save_recipe_from_extracted_data(db: Session, source_url: str, llm_output: dict, fallback_name: str = "Untitled Recipe", fallback_image: str = None) -> Recipe:
    """
    Common function to save recipe data to database.
    Used by both YouTube and web import functions.
    """
    recipe_details = llm_output.get("recipe_details", {})
    
    db_recipe = db.query(Recipe).filter(Recipe.source_url == source_url).first()

    if db_recipe:
        logger.info(f"Updating existing recipe ID: {db_recipe.id}")
        db_recipe.name = recipe_details.get("name") or fallback_name
        db_recipe.prep_time = recipe_details.get("prep_time")
        db_recipe.cook_time = recipe_details.get("cook_time")
        db_recipe.total_time = recipe_details.get("total_time")
        db_recipe.servings = recipe_details.get("servings")
        db_recipe.category = recipe_details.get("category")
        db_recipe.cuisine = recipe_details.get("cuisine")
        db_recipe.calories = recipe_details.get("calories")
        db_recipe.main_image_url = llm_output.get("main_image_url") or fallback_image
        db_recipe.source_type = llm_output.get("source_type", "unknown")
        
        db_recipe.ingredients.clear()
        db_recipe.instructions.clear()
        db.flush()

    else:
        logger.info("Creating new recipe")
        db_recipe = Recipe(
            name=recipe_details.get("name") or fallback_name,
            source_url=source_url,
            prep_time=recipe_details.get("prep_time"),
            cook_time=recipe_details.get("cook_time"),
            total_time=recipe_details.get("total_time"),
            servings=recipe_details.get("servings"),
            category=recipe_details.get("category"),
            cuisine=recipe_details.get("cuisine"),
            calories=recipe_details.get("calories"),
            main_image_url=llm_output.get("main_image_url") or fallback_image,
            source_type=llm_output.get("source_type", "unknown"),
        )
        db.add(db_recipe)
    
    db.flush()
    db.refresh(db_recipe)

    ingredients_data = llm_output.get("ingredients", [])
    logger.info(f"Processing {len(ingredients_data)} ingredients")
    for item in ingredients_data:
        ingredient_name = item.get("name")
        if not ingredient_name:
            continue
        
        db_ingredient = db.query(Ingredient).filter(Ingredient.name.ilike(ingredient_name)).first()
        if not db_ingredient:
            db_ingredient = Ingredient(name=ingredient_name)
            db.add(db_ingredient)
            db.flush()
            logger.debug(f"Created new ingredient: {ingredient_name}")
        
        recipe_ingredient = RecipeIngredient(
            ingredient=db_ingredient,
            quantity=item.get("quantity"),
            unit=item.get("unit"),
            notes=item.get("notes")
        )
        db_recipe.ingredients.append(recipe_ingredient)
    logger.info("Finished processing ingredients")

    instructions_data = llm_output.get("instructions", [])
    logger.info(f"Processing {len(instructions_data)} instructions")
    for item in instructions_data:
        db_instruction = Instruction(
            step_number=item.get("step_number"),
            section_name=item.get("section_name"),
            description=item.get("description")
        )
        db_recipe.instructions.append(db_instruction)
    logger.info("Finished processing instructions")
    
    logger.info("Generating ingredient tags")
    for ingredient_assoc in db_recipe.ingredients:
        ingredient_name = ingredient_assoc.ingredient.name.lower()
        
        tag = db.query(Tag).filter(Tag.name == ingredient_name, Tag.tag_type == 'ingredient').first()
        if not tag:
            tag = Tag(name=ingredient_name, tag_type='ingredient')
            db.add(tag)
            db.flush()
        
        if tag not in db_recipe.tags:
            db_recipe.tags.append(tag)
    
    logger.info(f"Added {len(db_recipe.tags)} ingredient tags")
    
    return db_recipe

def upsert_recipe_from_youtube_url(db: Session, youtube_url: str) -> Recipe:
    """
    Processes a YouTube URL to create or update a structured Recipe entry in the database.
    If a recipe with the given source_url already exists, it updates it.
    """
    start_time = time.time()
    status = "success"
    logger.info("Starting YouTube recipe upsert")
    try:
        video_id = youtube_service.extract_video_id(youtube_url)
        logger.info(f"Extracted video_id: {video_id}")
        
        has_transcript = youtube_service.check_transcript_availability(video_id)
        logger.info(f"Transcript available: {has_transcript}")
        
        metadata = youtube_service.get_video_metadata(video_id)
        metadata.comments = youtube_service.get_video_comments(video_id)
        logger.info("Fetched metadata and comments")
        
        transcript = ""
        if has_transcript:
            try:
                transcript = youtube_service.get_video_transcript(video_id)
                logger.info("Fetched transcript")
            except ValueError as e:
                logger.warning(f"Error fetching transcript, proceeding without it: {e}")
        
        logger.info("Sending data to LLM")
        llm_output = llm_service.generate_content_and_tags(metadata, transcript)
        llm_output["source_type"] = "youtube"
        logger.info("Received data from LLM")

        db_recipe = _save_recipe_from_extracted_data(
            db=db,
            source_url=youtube_url,
            llm_output=llm_output,
            fallback_name=metadata.title,
            fallback_image=metadata.thumbnail_url
        )
            
        logger.info("Committing transaction to database")
        db.commit()
        logger.info("Commit successful")
        
        db.refresh(db_recipe)
        logger.info("Recipe object refreshed from DB")
        
        recipes_imported.labels(source_type="youtube").inc()
        return db_recipe
        
    except Exception as e:
        status = "failed"
        logger.error(f"An error occurred: {e}", exc_info=True)
        db.rollback()
        logger.info("Transaction rolled back")
        raise RuntimeError(f"Failed to process YouTube URL: {e}") from e
    finally:
        duration = time.time() - start_time
        recipe_processing_time.labels(source_type="youtube", status=status).observe(duration)
        logger.info(f"YouTube processing completed in {duration:.2f}s", extra={"duration": duration, "status": status})

def upsert_recipe_from_web_url(db: Session, web_url: str) -> Recipe:
    """
    Processes a web URL (recipe websites like AllRecipes, NYTimes, etc.)
    to create or update a structured Recipe entry in the database.
    """
    start_time = time.time()
    status = "success"
    logger.info(f"Starting web recipe import from: {web_url}")
    try:
        extracted_data = web_scraper_service.extract_recipe_from_url(web_url)
        logger.info(f"Extracted recipe: {extracted_data.get('recipe_details', {}).get('name')}")
        
        db_recipe = _save_recipe_from_extracted_data(
            db=db,
            source_url=web_url,
            llm_output=extracted_data,
            fallback_name="Imported Recipe",
            fallback_image=extracted_data.get("main_image_url")
        )
        
        logger.info("Committing transaction to database")
        db.commit()
        logger.info("Commit successful")
        
        db.refresh(db_recipe)
        logger.info("Recipe object refreshed from DB")
        
        recipes_imported.labels(source_type="web").inc()
        return db_recipe
        
    except ValueError as ve:
        status = "failed"
        logger.error(f"Validation error: {ve}")
        db.rollback()
        raise
    except Exception as e:
        status = "failed"
        logger.error(f"An error occurred: {e}", exc_info=True)
        db.rollback()
        logger.info("Transaction rolled back")
        raise RuntimeError(f"Failed to process web URL: {e}") from e
    finally:
        duration = time.time() - start_time
        recipe_processing_time.labels(source_type="web", status=status).observe(duration)
        logger.info(f"Web processing completed in {duration:.2f}s", extra={"duration": duration, "status": status})

def upsert_recipe_from_social_url(db: Session, social_url: str) -> Recipe:
    """
    Processes an Instagram or TikTok URL to create or update a recipe.
    Extracts caption text and uses LLM to parse recipe data.
    """
    start_time = time.time()
    status = "success"
    logger.info(f"Starting social media recipe import from: {social_url}")
    try:
        extracted_data = social_media_service.extract_recipe_from_social_url(social_url)
        source_type = extracted_data.get("source_type", "social")
        logger.info(f"Extracted recipe from social media: {extracted_data.get('recipe_details', {}).get('name')}")
        
        db_recipe = _save_recipe_from_extracted_data(
            db=db,
            source_url=social_url,
            llm_output=extracted_data,
            fallback_name="Social Media Recipe",
            fallback_image=extracted_data.get("main_image_url")
        )
        
        logger.info("Committing transaction to database")
        db.commit()
        logger.info("Commit successful")
        
        db.refresh(db_recipe)
        logger.info("Recipe object refreshed from DB")
        
        recipes_imported.labels(source_type=source_type).inc()
        return db_recipe
        
    except ValueError as ve:
        status = "failed"
        logger.error(f"Validation error: {ve}")
        db.rollback()
        raise
    except Exception as e:
        status = "failed"
        logger.error(f"An error occurred: {e}", exc_info=True)
        db.rollback()
        logger.info("Transaction rolled back")
        raise RuntimeError(f"Failed to process social media URL: {e}") from e
    finally:
        duration = time.time() - start_time
        recipe_processing_time.labels(source_type="social", status=status).observe(duration)
        logger.info(f"Social media processing completed in {duration:.2f}s", extra={"duration": duration, "status": status})

def upsert_recipe_from_any_url(db: Session, url: str) -> Recipe:
    """
    Automatically detect URL type and process accordingly.
    Routes to YouTube, web scraper, or social media handler.
    """
    url_type = web_scraper_service.detect_url_type(url)
    logger.info(f"Detected URL type: {url_type}")
    
    if url_type == "youtube":
        return upsert_recipe_from_youtube_url(db, url)
    elif url_type == "web":
        return upsert_recipe_from_web_url(db, url)
    elif url_type in ["instagram", "tiktok", "facebook", "social"]:
        return upsert_recipe_from_social_url(db, url)
    else:
        raise ValueError(f"Unsupported URL type: {url_type}")

def get_recipe_by_id(db: Session, recipe_id: int) -> Recipe | None:
    return db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.is_deleted == False).first()

def get_all_recipes(db: Session) -> list[Recipe]:
    return db.query(Recipe).filter(Recipe.is_deleted == False).order_by(Recipe.created_at.desc()).all()

def move_to_trash(db: Session, recipe_id: int) -> Recipe | None:
    """Soft delete - mark recipe as deleted but keep in database"""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.is_deleted == False).first()
    if recipe:
        recipe.is_deleted = True
        recipe.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(recipe)
        return recipe
    return None

def get_trash_count(db: Session) -> int:
    """Get count of deleted recipes in trash"""
    return db.query(Recipe).filter(Recipe.is_deleted == True).count()

def restore_most_recent_from_trash(db: Session) -> Recipe | None:
    """Restore the most recently deleted recipe"""
    recipe = db.query(Recipe).filter(Recipe.is_deleted == True).order_by(Recipe.deleted_at.desc()).first()
    if recipe:
        recipe.is_deleted = False
        recipe.deleted_at = None
        db.commit()
        db.refresh(recipe)
        return recipe
    return None

def purge_trash(db: Session) -> int:
    """Permanently delete all recipes in trash. Returns count of deleted recipes."""
    deleted_recipes = db.query(Recipe).filter(Recipe.is_deleted == True).all()
    count = len(deleted_recipes)
    for recipe in deleted_recipes:
        db.delete(recipe)
    db.commit()
    return count

def delete_recipe_by_id(db: Session, recipe_id: int) -> Recipe | None:
    """Hard delete - permanently remove recipe (used for cleanup)"""
    recipe_to_delete = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if recipe_to_delete:
        db.delete(recipe_to_delete)
        db.commit()
        return recipe_to_delete
    return None

def update_recipe(db: Session, recipe_id: int, update_data: dict) -> Recipe | None:
    """Update recipe fields"""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.is_deleted == False).first()
    if not recipe:
        return None
    
    for field, value in update_data.items():
        if hasattr(recipe, field) and value is not None:
            setattr(recipe, field, value)
    
    db.commit()
    db.refresh(recipe)
    return recipe