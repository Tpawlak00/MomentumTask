from utils import db_utils
from fastapi import HTTPException
from datetime import datetime
from utils.logger import logger

def add_new_book(serial_num: int, title: str, author: str, is_borrowed: bool = False,
                 borrowed_by: int = None, borrowed_at: datetime = None):
    try:
        if len(str(serial_num)) != 6:
            logger.error(f"Wrong serial number format {str(serial_num)}")
            raise HTTPException(status_code=401, detail="Wrong serial number format")

        if db_utils.get_records_from_db("books", filters={"serial_num": serial_num}):
            logger.error(f"Record {serial_num} already exists in database")
            raise HTTPException(status_code=402, detail=f"Record {serial_num} already exists in database")

        if is_borrowed:
            if not borrowed_by or len(str(borrowed_by)) != 6:
                logger.error(f"Missing customer id (borrowed_by) while is_borrowed is True")
                raise HTTPException(status_code=403, detail="Missing customer id (borrowed_by) while is_borrowed is True")
            if not borrowed_at:
                logger.error(f"Missing date (borrowed_at) while is_borrowed is True")
                raise HTTPException(status_code=405, detail="Missing date (borrowed_at) while is_borrowed is True")
        else:
            record = locals()

            response = db_utils.add_record_to_db("books", record)

            return response

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        logger.error(f"Error in module add_new_book: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def get_all_books():
    try:
        records = db_utils.get_all_records_from_db("books")

        return records
    except Exception as e:
        logger.error(f"Error in module add_new_book: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def delete_book(serial_num: int):
    try:
        if len(str(serial_num)) != 6:
            logger.error(f"Wrong serial number format {str(serial_num)}")
            raise HTTPException(status_code=411, detail="Wrong serial number format")

        records_to_delete = db_utils.get_records_from_db("books", filters={"serial_num": serial_num})

        if not records_to_delete:
            logger.error(f"Record {serial_num} does not exist in database")
            raise HTTPException(status_code=412, detail=f"Record {serial_num} does not exist in database")

        response = db_utils.delete_records_from_db("books", [records_to_delete[0]["id"]])

        return response

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        logger.error(f"Error in module delete_book: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def update_book(serial_num: int, is_borrowed: bool, borrowed_by: int = None, borrowed_at: datetime = None):
    try:
        if len(str(serial_num)) != 6:
            logger.error(f"Wrong serial number format {str(serial_num)}")
            raise HTTPException(status_code=401, detail="Wrong serial number format")
        elif len(str(borrowed_by)) != 6:
            logger.error(f"Wrong customer ID format {str(borrowed_by)}")
            raise HTTPException(status_code=401, detail="Wrong customer ID format")
        elif is_borrowed:
            if not borrowed_by or len(str(borrowed_by)) != 6:
                logger.error(f"Missing customer id (borrowed_by) while is_borrowed is True")
                raise HTTPException(status_code=403, detail="Missing customer id (borrowed_by) while is_borrowed is True")
            elif not borrowed_at:
                logger.error(f"Missing date (borrowed_at) while is_borrowed is True")
                raise HTTPException(status_code=405, detail="Missing date (borrowed_at) while is_borrowed is True")


        table_name = "books"
        filters = {"serial_num": serial_num}

        existing_record = db_utils.get_records_from_db(table_name, filters)
        if existing_record:
            current_data = existing_record[0]
        else:
            logger.error(f"Record {serial_num} does not exist in database")
            raise HTTPException(status_code=412, detail=f"Record {serial_num} does not exist in database")


        if is_borrowed:
            new_data = {
                "borrowed_by": borrowed_by,
                "borrowed_at": borrowed_at,
                "is_borrowed": is_borrowed
            }
        else:
            new_data = {
                "borrowed_by": None,
                "borrowed_at": None,
                "is_borrowed": is_borrowed
            }

        update_data = {key: value for key, value in new_data.items() if value != current_data.get(key)}
        update_data["id"] = current_data["id"]

        if update_data:
            db_utils.update_records_in_db(table_name=table_name, records=[{**filters, **update_data}])
            return {"message": "Record successfully updated!"}
        else:
            return {"message": "No changes to update."}

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        logger.error(f"Error in module update_book: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
